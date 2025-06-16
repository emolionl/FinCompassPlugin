from flask import Blueprint, jsonify, request, current_app
import os
from datetime import datetime
import requests
from .database import FinCompassDatabase
from flasgger import Swagger, swag_from

def create_blueprint():
    print("[DEBUG] Creating FinCompass blueprint...")
    fincompass_blueprint = Blueprint('fincompass', __name__)
    
    # Initialize database
    db_path = os.path.join(os.path.dirname(__file__), 'fincompass.db')
    db = FinCompassDatabase(db_path)

    AETHERONE_API_URL = "http://localhost:7000"

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
            case = current_app.case_dao.create_case(case_data['name'])
            if not case:
                return jsonify({"error": "Failed to create case"}), 500

            # Store case in FinCompass database
            stored_case = db.get_or_create_case(case.id, case_data['name'], catalog_id)
            if not stored_case:
                return jsonify({"error": "Failed to store case"}), 500

            # Create session in AetherOnePy
            session = current_app.case_dao.create_session(
                case.id,
                session_data.get('intention', ''),
                session_data.get('description', '')
            )
            if not session:
                return jsonify({"error": "Failed to create session"}), 500

            # Create analysis
            analysis = current_app.case_dao.create_analysis(
                session.id,
                catalog_id,
                note
            )
            if not analysis:
                return jsonify({"error": "Failed to create analysis"}), 500

            # Run analysis
            results = current_app.case_dao.run_analysis(analysis.id)
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
