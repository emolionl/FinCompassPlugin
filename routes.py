from flask import Blueprint, jsonify, request, current_app, send_from_directory
import os
from datetime import datetime
import requests
from .database import FinCompassDatabase
from flasgger import Swagger, swag_from
import pathlib
from domains.aetherOneDomains import Session as AOSession, Analysis as AOAnalysis
from services.analyzeService import analyze
from services.hotbitsService import HotbitsService, HotbitsSource

def push_schedule_to_external_api(schedule: dict) -> dict:
    """
    Push a schedule to the external FinCompass API.
    Args:
        schedule (dict): The schedule data to send (must match external API schema).
    Returns:
        dict: The response from the external API.
    Raises:
        Exception: If the request fails or the API returns an error.
    """
    # Get the selected server URL from the database
    db_path = os.path.join(os.path.dirname(__file__), 'fincompass.db')
    db = FinCompassDatabase(db_path)
    selected_server = db.get_selected_server()
    if not selected_server or not selected_server.get('url'):
        raise Exception("No server URL selected in the database.")
    base_url = selected_server['url'].rstrip('/')
    api_url = f"{base_url}/api/v1/schedules"
    api_key = selected_server.get('api_key')
    if not api_key:
        raise Exception("No API key set for the selected server in the database.")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.post(api_url, json=schedule, headers=headers, timeout=15)
    if not response.ok:
        raise Exception(f"External API error: {response.status_code} {response.text}")
    return response.json()

def create_blueprint(app_instance=None):
    print("[DEBUG] Creating FinCompass blueprint...")
    fincompass_blueprint = Blueprint('fincompass', __name__)
    
    # Initialize database
    db_path = os.path.join(os.path.dirname(__file__), 'fincompass.db')
    db = FinCompassDatabase(db_path)
    
    # Get case_dao reference - use app_instance if provided, otherwise fall back to current_app
    def get_case_dao():
        if app_instance and hasattr(app_instance, 'case_dao'):
            return app_instance.case_dao
        else:
            return current_app.case_dao

    AETHERONE_API_URL = "http://localhost:7000"

    # --- Static frontend serving for FinCompass (like AetherOnePySocialPlugin) ---
    FRONTEND_DIST_DIR = pathlib.Path(__file__).parent / 'frontend' / 'dist'

    @fincompass_blueprint.route('/analyze-complete', methods=['POST'])
    def analyze_complete():
        """
        Complete analysis flow - creates case, session, and runs analysis.
        ---
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                case:
                  type: object
                  properties:
                    name:
                      type: string
                      description: Name of the case
                session:
                  type: object
                  properties:
                    intention:
                      type: string
                      description: Session intention
                    description:
                      type: string
                      description: Session description
                catalogId:
                  type: integer
                  description: ID of the catalog to use
                note:
                  type: string
                  description: Optional note for the analysis
        responses:
          200:
            description: Analysis completed successfully
            schema:
              type: object
              properties:
                status:
                  type: string
                case:
                  type: object
                session:
                  type: object
                analysis:
                  type: object
                results:
                  type: object
          400:
            description: Missing required fields
          500:
            description: Server error
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400

            # Extract data
            case_data = data.get('case', {})
            session_data = data.get('session', {})
            catalog_id = data.get('catalogId')
            note = data.get('note', '')

            # Validate required fields
            if not case_data.get('name'):
                return jsonify({"error": "Case name is required"}), 400
            if not catalog_id:
                return jsonify({"error": "Catalog ID is required"}), 400

            # Create case in AetherOnePy
            case = get_case_dao().create_case(case_data['name'])
            if not case:
                return jsonify({"error": "Failed to create case"}), 500

            # Store case in FinCompass database
            stored_case = db.get_or_create_case(case.id, case_data['name'], catalog_id)
            if not stored_case:
                return jsonify({"error": "Failed to store case"}), 500

            # Create session in AetherOnePy
            session = get_case_dao().create_session(
                case.id,
                session_data.get('intention', ''),
                session_data.get('description', '')
            )
            if not session:
                return jsonify({"error": "Failed to create session"}), 500

            # Create analysis
            analysis = get_case_dao().create_analysis(
                session.id,
                catalog_id,
                note
            )
            if not analysis:
                return jsonify({"error": "Failed to create analysis"}), 500

            # Run analysis
            results = get_case_dao().run_analysis(analysis.id)
            if not results:
                return jsonify({"error": "Failed to run analysis"}), 500

            return jsonify({
                "status": "success",
                "case": stored_case,
                "session": session.__dict__,
                "analysis": analysis.__dict__,
                "results": results
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @fincompass_blueprint.route('/cases', methods=['GET'])
    def get_cases():
        """
        Get all cases created through FinCompass.
        ---
        responses:
          200:
            description: List of cases
            schema:
              type: object
              properties:
                status:
                  type: string
                cases:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                      aetherone_case_id:
                        type: integer
                      name:
                        type: string
                      catalog_id:
                        type: integer
                      created_at:
                        type: string
                        format: date-time
          500:
            description: Server error
        """
        try:
            cases = db.get_all_cases()
            return jsonify({
                "status": "success",
                "cases": cases
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @fincompass_blueprint.route('/ping', methods=['GET'])
    def ping():
        """
        Health check endpoint for the FinCompass plugin.
        ---
        responses:
          200:
            description: Pong response with plugin info and timestamp
            schema:
              type: object
              properties:
                status:
                  type: string
                message:
                  type: string
                plugin:
                  type: string
                timestamp:
                  type: string
        """
        return jsonify({
            "status": "success",
            "message": "pong",
            "plugin": "FinCompass",
            "timestamp": datetime.now().isoformat()
        })

    @fincompass_blueprint.route('/schedules', methods=['GET'])
    def get_schedules():
        """
        Get all schedules created through FinCompass.
        ---
        responses:
        """
        return jsonify({
            "status": "success",
            "schedules": []
        })
    
    @fincompass_blueprint.route('/api/servers', methods=['GET'])
    def api_get_servers():
        """
        Get all servers (for frontend).
        """
        try:
            servers = db.get_servers()
            return jsonify({
                "status": "success",
                "servers": servers
            })
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 500

    @fincompass_blueprint.route('/api/servers', methods=['POST'])
    def api_add_server():
        """
        Add a new server/provider (for frontend).
        """
        try:
            data = request.get_json()
            url = data.get('url')
            description = data.get('description')
            api_key = data.get('api_key')
            exchange_id = data.get('exchange_id')
            if not url:
                return jsonify({"status": "error", "error": "Missing url"}), 400
            # If this is the first server, set as selected
            servers = db.get_servers()
            selected = len(servers) == 0
            server = db.add_server(url, description, selected, api_key, exchange_id)
            return jsonify({"status": "success", "server": server})
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 500

    @fincompass_blueprint.route('/api/servers/<path:url>/api_key', methods=['PUT'])
    def api_update_server_api_key(url):
        """
        Update the API key for a server by URL.
        """
        try:
            data = request.get_json()
            api_key = data.get('api_key')
            if not api_key:
                return jsonify({"status": "error", "error": "Missing api_key"}), 400
            db.update_server_api_key(url, api_key)
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 500

    @fincompass_blueprint.route('/api/providers', methods=['GET'])
    def api_get_providers():
        """
        Proxy: Get all providers from the selected server, store them locally,
        and return the local list.
        """
        try:
            # Get selected server
            selected_server = db.get_selected_server()
            if not selected_server or not selected_server.get('url'):
                return jsonify({"status": "error", "error": "No server selected"}), 400
            
            base_url = selected_server['url'].rstrip('/')
            api_key = selected_server.get('api_key')
            
            if not api_key:
                # If no API key, just return what we have locally
                local_providers = db.get_providers_by_server(selected_server['id'])
                return jsonify({"status": "success", "providers": local_providers})

            # Compose external API URL
            api_url = f"{base_url}/api/v1/providers/"
            headers = { "X-API-Key": f"{api_key}" }

            # Fetch from external API
            resp = requests.get(api_url, headers=headers, timeout=15)
            if resp.status_code != 200:
                return jsonify({"status": "error", "error": f"Upstream error: {resp.status_code} {resp.text}"}), 502

            # Store providers locally
            external_providers = resp.json()
            db.store_providers(selected_server['id'], external_providers)

            # Get the (potentially updated) list from local DB and return
            local_providers = db.get_providers_by_server(selected_server['id'])
            return jsonify({"status": "success", "providers": local_providers})

        except requests.exceptions.RequestException as e:
            # If the external API fails, fall back to local data
            current_app.logger.warning(f"Could not connect to external provider API: {e}. Serving local data.")
            selected_server = db.get_selected_server()
            if selected_server:
                local_providers = db.get_providers_by_server(selected_server['id'])
                return jsonify({"status": "success", "providers": local_providers})
            return jsonify({"status": "error", "error": "No server selected and external API is unavailable."}), 503

        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 500

    @fincompass_blueprint.route('/api/providers/<int:provider_id>/select', methods=['POST'])
    def api_select_provider(provider_id):
        """
        Set a provider as selected for the current server.
        """
        try:
            selected_server = db.get_selected_server()
            if not selected_server:
                return jsonify({"status": "error", "error": "No server selected"}), 400
            
            db.set_selected_provider(selected_server['id'], provider_id)
            return jsonify({"status": "success"})

        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 500

    @fincompass_blueprint.route('/api/providers/<int:provider_id>/deselect', methods=['POST'])
    def api_deselect_provider(provider_id):
        """
        Deselect a single provider for the current selected server.
        """
        try:
            selected_server = db.get_selected_server()
            if not selected_server:
                return jsonify({"status": "error", "error": "No server selected"}), 400
            db.deselect_provider(selected_server['id'], provider_id)
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 500

    @fincompass_blueprint.route('/api/catalogs', methods=['GET'])
    def api_get_catalogs():
        """
        Always use the main app's DAO to get catalogs.
        """
        try:
            # Convert Catalog objects to dicts for sync_catalogs
            core_catalogs = [c.to_dict() if hasattr(c, 'to_dict') else {'id': c.id, 'name': c.name} for c in get_case_dao().list_catalogs()]
            db.sync_catalogs(core_catalogs)
            local_catalogs = db.get_catalogs()
            return jsonify({"status": "success", "catalogs": local_catalogs})

        except Exception as e:
            current_app.logger.error(f"Error in /api/catalogs: {e}")
            return jsonify({"status": "error", "error": str(e)}), 500

    @fincompass_blueprint.route('/api/catalogs/<int:catalog_id>/select', methods=['POST'])
    def api_select_catalog(catalog_id):
        """
        Sets a specific catalog as 'selected' in the plugin's database.
        """
        try:
            db.set_selected_catalog(catalog_id)
            return jsonify({"status": "success"})
        except Exception as e:
            current_app.logger.error(f"Error selecting catalog {catalog_id}: {e}")
            return jsonify({"status": "error", "error": str(e)}), 500
        
    @fincompass_blueprint.route('/api/intentions', methods=['GET'])
    def api_get_intentions():
        intentions = db.get_intentions()
        return jsonify(intentions)

    @fincompass_blueprint.route('/api/intentions', methods=['POST'])
    def api_create_intention():
        data = request.get_json()
        intention = db.create_intention(
            intention=data.get('intention'),
            description=data.get('description'),
            selected=data.get('selected'),
            hold_minutes=data.get('hold_minutes', 0),
            amount=data.get('amount', 0),
            stop_loss_percentage=data.get('stop_loss_percentage', 0),
            take_profit_percentage=data.get('take_profit_percentage', 0)
        )
        return jsonify(intention), 201

    @fincompass_blueprint.route('/api/intentions/<int:intention_id>', methods=['PUT'])
    def api_update_intention(intention_id):
        data = request.get_json()
        db.update_intention(
            intention_id=intention_id,
            intention=data.get('intention'),
            description=data.get('description'),
            selected=data.get('selected'),
            hold_minutes=data.get('hold_minutes'),
            amount=data.get('amount'),
            stop_loss_percentage=data.get('stop_loss_percentage'),
            take_profit_percentage=data.get('take_profit_percentage')
        )
        return jsonify({'status': 'success'})

    @fincompass_blueprint.route('/api/intentions/<int:intention_id>', methods=['DELETE'])
    def api_delete_intention(intention_id):
        db.delete_intention(intention_id)
        return jsonify({'status': 'success'})
    

    @fincompass_blueprint.route('/api/providers/<string:exchange_id>/sync-rates', methods=['POST'])
    def api_sync_rates(exchange_id):
        """
        Sync rates from external provider into the local AetherOnePy database under a catalog named after the provider.
        The provider's API URL is read from the local FinCompass database, joining on server_id.
        """
        try:
            # 1. Look up provider in local DB by exchange_id and get server_url
            selected_server = db.get_selected_server()
            provider = db.get_provider_with_url_by_exchange_id(selected_server['id'], exchange_id)
            if not provider or not provider.get('server_url'):
                return jsonify({"status": "error", "error": f"Provider '{exchange_id}' not found or missing server URL in database."}), 400

            # 2. Build the API URL (assume the server's URL is the base, append the endpoint as needed)
            api_url = provider['server_url'].rstrip('/') + "/api/v1/symbols/exchange/" + exchange_id + "?trading_type=spot"
            print(f"[DEBUG] API URL: {api_url}")
            resp = requests.get(api_url, headers={"accept": "application/json"}, timeout=20)
            if not resp.ok:
                return jsonify({"status": "error", "error": f"Upstream error: {resp.status_code} {resp.text}"}), 502

            # Debug: log the raw response text before parsing JSON
            print(f"[DEBUG] API response text: {resp.text}")
            try:
                rates_data = resp.json()
            except Exception as e:
                current_app.logger.error(f"Error parsing JSON from {api_url}: {resp.text}")
                return jsonify({"status": "error", "error": f"Invalid JSON from upstream: {e}"}), 502

            # 3. Use main DAO to check/create catalog
            dao = get_case_dao()
            catalog = dao.get_catalog_by_name(exchange_id)
            if not catalog:
                from domains.aetherOneDomains import Catalog
                catalog = Catalog(exchange_id, f"Rates for {exchange_id}", "FinCompass")
                dao.insert_catalog(catalog)
                catalog = dao.get_catalog_by_name(exchange_id)

            # 4. Full sync: remove local rates not on server, then insert new ones
            from domains.aetherOneDomains import Rate
            
            # FIX: Use 'symbols' key and strip quotes from each symbol
            raw_symbols = rates_data.get('symbols', [])
            server_symbols = {s.strip('"') for s in raw_symbols}
            
            current_app.logger.info(f"[SYNC] Found {len(server_symbols)} symbols from API for catalog '{exchange_id}'.")
            
            local_rates = dao.list_rates_from_catalog(catalog.id)
            current_app.logger.info(f"[SYNC] Found {len(local_rates)} existing local rates for catalog '{catalog.id}'.")

            # Remove local rates not present on the server
            deleted_count = 0
            for rate in local_rates:
                if rate.signature not in server_symbols:
                    dao.delete_rate(rate.id)
                    deleted_count += 1
            
            # Insert new rates from the server
            inserted_count = 0
            # Re-fetch existing symbols after deletion
            existing_symbols = {r.signature for r in dao.list_rates_from_catalog(catalog.id)}
            for symbol in server_symbols:
                if symbol not in existing_symbols:
                    dao.insert_rate(Rate(symbol, '', catalog.id))
                    inserted_count += 1
            
            current_app.logger.info(f"[SYNC] Deleted {deleted_count} stale rates and inserted {inserted_count} new rates for catalog '{exchange_id}'.")

            return jsonify({
                "status": "success",
                "message": f"Sync complete for {exchange_id}",
                "inserted": inserted_count,
                "deleted": deleted_count,
                "total_in_catalog": len(server_symbols)
            })

        except Exception as e:
            current_app.logger.error(f"Error syncing rates for provider {exchange_id}: {e}")
            return jsonify({"status": "error", "error": str(e)}), 500
    
    # 1. create a case with name
    # 2. create a session with intention
    # 3. create a analysis with catalog id
    # 4. run analysis
    # 5. get results from analysis
    # 6. create a schedule with intention
    # 7. get schedule id
    # 8. create a schedule to sell with schedule id

    @fincompass_blueprint.route('/js/<path:filename>')
    def serve_js(filename):
        return send_from_directory(FRONTEND_DIST_DIR / 'js', filename)

    @fincompass_blueprint.route('/css/<path:filename>')
    def serve_css(filename):
        return send_from_directory(FRONTEND_DIST_DIR / 'css', filename)

    @fincompass_blueprint.route('/', defaults={'path': ''})
    @fincompass_blueprint.route('/<path:path>')
    def serve_frontend(path):
        """
        Serve the FinCompass frontend (index.html and static assets).
        The directory 'py/plugins/FinCompass/frontend/dist' must exist and contain index.html and assets.
        """
        # Serve static files if they exist
        if path and (FRONTEND_DIST_DIR / path).exists():
            return send_from_directory(FRONTEND_DIST_DIR, path)
        return send_from_directory(FRONTEND_DIST_DIR, 'index.html')

    @fincompass_blueprint.route('/api/catalogs/deselect', methods=['POST'])
    def api_deselect_catalog():
        """
        Deselect all catalogs.
        """
        try:
            db.set_selected_catalog(None)
            return jsonify({"status": "success"})
        except Exception as e:
            current_app.logger.error(f"Error deselecting catalogs: {e}")
            return jsonify({"status": "error", "error": str(e)}), 500

    @fincompass_blueprint.route('/api/cases', methods=['GET'])
    def api_get_cases():
        # Sync cases from AetherOnePy before returning
        try:
            core_cases = db.get_cases_from_aetheronepy()
            db.sync_cases(core_cases)
            cases = db.get_cases()
            return jsonify({"status": "success", "cases": cases})
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)})

    @fincompass_blueprint.route('/api/cases/<int:case_id>/select', methods=['POST'])
    def api_select_case(case_id):
        db.set_selected_case(case_id)
        return jsonify({"status": "success"})

    @fincompass_blueprint.route('/api/cases/deselect', methods=['POST'])
    def api_deselect_case():
        db.set_selected_case(None)
        return jsonify({"status": "success"})

    @fincompass_blueprint.route('/api/start-magic', methods=['POST'])
    def api_start_magic():
        import datetime
        import requests
        import os
        from domains.aetherOneDomains import Session as AOSession, Analysis as AOAnalysis
        from services.analyzeService import analyze
        from services.hotbitsService import HotbitsService, HotbitsSource
        class DummyMain:
            def emitMessage(self, *args, **kwargs):
                pass
        try:
            data = request.get_json()
            # --- Variables from API request (frontend) ---
            plugin_intention_id = data.get('intention_id')  # FinCompass plugin DB
            plugin_case_id = data.get('case_id')            # FinCompass plugin DB
            plugin_provider_id = data.get('provider_id')    # FinCompass plugin DB
            plugin_catalog_id = data.get('catalog_id')      # FinCompass plugin DB
            print(f"[DEBUG] plugin_intention_id: {plugin_intention_id}, plugin_catalog_id: {plugin_catalog_id}, plugin_case_id: {plugin_case_id}, plugin_provider_id: {plugin_provider_id}")
            if not all([plugin_intention_id, plugin_case_id, plugin_provider_id, plugin_catalog_id]):
                return jsonify({'status': 'error', 'error': 'Missing required selection.'}), 400

            # --- PLUGIN DB: Get intention (for hold_minutes) from FinCompass database ---
            plugin_intention = next((i for i in db.get_intentions() if i['id'] == plugin_intention_id), None)
            if not plugin_intention:
                return jsonify({'status': 'error', 'error': 'Intention not found.'}), 404
            hold_minutes = plugin_intention.get('hold_minutes', 0) or 0
            print(f"[DEBUG] plugin_intention: {plugin_intention}")

            # --- PLUGIN DB: Get provider from FinCompass database ---
            plugin_provider = next((p for p in db.get_providers() if p['id'] == plugin_provider_id), None)
            if not plugin_provider:
                return jsonify({'status': 'error', 'error': 'Provider not found.'}), 404
            print(f"[DEBUG] plugin_provider: {plugin_provider}")

            # --- PLUGIN DB: Map plugin_catalog_id to aetherone_catalog_id ---
            plugin_catalog_row = next((c for c in db.get_catalogs() if c['id'] == plugin_catalog_id), None)
            if not plugin_catalog_row:
                return jsonify({'status': 'error', 'error': 'Catalog not found.'}), 404
            aetherone_catalog_id = plugin_catalog_row['aetherone_catalog_id']  # main AetherOnePy DB
            print(f"[DEBUG] plugin_catalog_id: {plugin_catalog_id}, aetherone_catalog_id: {aetherone_catalog_id}")

            # --- MAIN AETHERONE DB: Get case ID for AetherOnePy (from plugin DB mapping) ---
            plugin_case_row = next((c for c in db.get_cases() if c['id'] == plugin_case_id), None)
            if not plugin_case_row:
                return jsonify({'status': 'error', 'error': 'Case not found.'}), 404
            aetherone_case_id = plugin_case_row['aetherone_case_id']  # main AetherOnePy DB
            print(f"[DEBUG] plugin_case_id: {plugin_case_id}, aetherone_case_id: {aetherone_case_id}")

            # --- MAIN AETHERONE DB: Create session ---
            session_obj = AOSession(plugin_intention['intention'], plugin_intention.get('description', ''), aetherone_case_id)
            get_case_dao().insert_session(session_obj)  # main DB
            aetherone_session = session_obj  # Now has .id set
            print(f"[DEBUG] aetherone_session: {aetherone_session}")

            # --- MAIN AETHERONE DB: Create analysis ---
            analysis_obj = AOAnalysis('', aetherone_session.id)
            analysis_obj.catalogId = aetherone_catalog_id
            get_case_dao().insert_analysis(analysis_obj)  # main DB
            aetherone_analysis = analysis_obj  # Now has .id set
            print(f"[DEBUG] aetherone_analysis: {aetherone_analysis}")

            # --- MAIN AETHERONE DB: Run analysis (get rates, call analyze, insert results) ---
            rates_list = get_case_dao().list_rates_from_catalog(aetherone_catalog_id)  # main DB
            # Create HotbitsService instance locally (independent)
            PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
            hotbits = HotbitsService(HotbitsSource.WEBCAM, os.path.join(PROJECT_ROOT, "hotbits"), db, DummyMain())
            enhanced_rates = analyze(
                aetherone_analysis.id,
                rates_list,
                hotbits,
                get_case_dao().get_setting('analysisAlwaysCheckGV'),
                get_case_dao().get_setting('analysisAdvanced')
            )
            #print(f"[DEBUG] enhanced_rates: {[r.to_dict() for r in enhanced_rates]}")
            get_case_dao().insert_rates_for_analysis(enhanced_rates)  # main DB
            results = [r.to_dict() for r in enhanced_rates]
            print(f"[DEBUG] results: {results}")

            # --- Find highest rate (from analysis results) ---
            highest = max(results, key=lambda r: r.get('value', 0)) if results else None
            print(f"[DEBUG] highest: {highest}")
            if not highest:
                return jsonify({'status': 'error', 'error': 'No rates found in analysis.'}), 500
            symbol = highest.get('signature') or highest.get('symbol')
            if not symbol:
                return jsonify({'status': 'error', 'error': 'No symbol found in highest rate.'}), 500
            print(f"[DEBUG] symbol: {symbol}")

            # --- Calculate buy/sell times ---
            now = datetime.datetime.utcnow()
            buy_time = now.isoformat(timespec='seconds') + 'Z'
            sell_time = (now + datetime.timedelta(minutes=hold_minutes)).isoformat(timespec='seconds') + 'Z'
            print(f"[DEBUG] buy_time: {buy_time}")
            print(f"[DEBUG] sell_time: {sell_time}")


            # --- PLUGIN DB: Get selected server and provider (for remote schedule) ---
            print(f"[DEBUG] highest: {highest}")
            selected_server = db.get_selected_server()  # plugin DB
            print(f"[DEBUG] selected_server: {selected_server}")
            provider = db.get_provider_by_server_and_provider_id(
                selected_server['id'],
                plugin_provider['server_provider_id']
            )  # plugin DB
            print(f"[DEBUG] provider: {provider}")
            if not provider or not provider.get('server_url'):
                return jsonify({'status': 'error', 'error': 'Provider or server URL not found in database.'}), 500
            remote_url = provider['server_url'].rstrip('/') + '/api/v1/schedules/'
            payload = {
                'amount': str(plugin_intention.get('amount', '0')),
                'is_active': True,
                'name': f"{plugin_intention['intention'][:20].strip()} {symbol}",
                'order_type': 'market',
                'provider_id': provider['server_provider_id'],
                'recurrence_type': 'none',
                'scheduled_time': buy_time,  # use buy_time as the scheduled time
                'sell_all': False,
                'side': 'buy',
                'symbol': symbol,
                'social_key': '',  # TODO: fetch from SocialPlugin
                'stop_loss_percentage': plugin_intention.get('stop_loss_percentage', 0),
                'take_profit_percentage': plugin_intention.get('take_profit_percentage', 0)
            }
            api_key = selected_server.get('api_key')
            if not api_key:
                return jsonify({'status': 'error', 'error': 'No API key set for the selected server.'}), 500
            headers = {'X-API-KEY': api_key}
            print(f"[DEBUG] payload: {payload}")
            try:
                resp = requests.post(remote_url, json=payload, headers=headers, timeout=15)
                resp.raise_for_status()
                resp_data = resp.json()
                buy_schedule_id = resp_data.get('id')
                print(f"[DEBUG] buy_schedule_id: {buy_schedule_id}")

                # Post sell schedule
                sell_payload = payload.copy()
                sell_payload['side'] = 'sell'
                sell_payload['scheduled_time'] = sell_time
                sell_payload['linked_buy_schedule_id'] = buy_schedule_id
                print(f"[DEBUG] sell_payload: {sell_payload}")
                sell_resp = requests.post(remote_url, json=sell_payload, headers=headers, timeout=15)
                sell_resp.raise_for_status()
                sell_resp_data = sell_resp.json()
                sell_schedule_id = sell_resp_data.get('id')
                print(f"[DEBUG] sell_schedule_id: {sell_schedule_id}")
            except Exception as e:
                return jsonify({'status': 'error', 'error': f'Failed to post schedule to remote server: {e}'}), 502

            # --- PLUGIN DB: Save schedule locally ---
            schedule_record = db.create_intention_schedule(
                plugin_intention_id,
                buy_time,
                sell_time,
                status='scheduled',
                server_schedule_buy_id=buy_schedule_id,
                server_schedule_sell_id=sell_schedule_id
            )
            return jsonify({
                'status': 'success',
                'buy_schedule_id': buy_schedule_id,
                'sell_schedule_id': sell_schedule_id,
                'server_schedule_buy_id': schedule_record.get('server_schedule_buy_id'),
                'server_schedule_sell_id': schedule_record.get('server_schedule_sell_id')
            })
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 500

    @fincompass_blueprint.route('/api/servers/<path:url>/select', methods=['POST'])
    def api_select_server(url):
        db.set_selected_server(url)
        return jsonify({"status": "success"})

    @fincompass_blueprint.route('/api/servers/deselect', methods=['POST'])
    def api_deselect_server():
        db.set_selected_server(None)
        return jsonify({"status": "success"})

    @fincompass_blueprint.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not found',
            'message': 'The requested resource was not found'
        }), 404

    @fincompass_blueprint.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500

    # Swagger config for blueprint
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "FinCompass API",
            "description": "API documentation for the FinCompass plugin.",
            "version": "1.0.0"
        },
        "basePath": "/fincompass"
    }

    return fincompass_blueprint
