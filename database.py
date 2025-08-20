import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

class FinCompassDatabase:
    def __init__(self, db_path: str):
        """Initialize the database connection and create tables if they don't exist."""
        self.db_path = db_path
        self._create_tables()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        """Create necessary database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create cases table with catalog selection and selection support
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    aetherone_case_id INTEGER UNIQUE,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    selected BOOLEAN DEFAULT 0
                )
            ''')

            conn.commit()

            # Create servers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL UNIQUE,
                    description TEXT,
                    api_key TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    selected BOOLEAN DEFAULT 0
                )
            ''')
            # Insert default server if none exist
            cursor.execute('SELECT COUNT(*) FROM servers')
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO servers (url, description, selected)
                    VALUES (?, ?, 1)
                ''', ('https://fincompass.emolio.nl', 'Default FinCompass server',))
            
            # Create intentions table (add amount)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS intentions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT,
                    intention TEXT NOT NULL,
                    selected BOOLEAN DEFAULT 0
                )
            ''')
            # Add hold_minutes column if it doesn't exist
            cursor.execute("PRAGMA table_info(intentions)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'hold_minutes' not in columns:
                cursor.execute('ALTER TABLE intentions ADD COLUMN hold_minutes INTEGER DEFAULT 0')
            if 'amount' not in columns:
                cursor.execute('ALTER TABLE intentions ADD COLUMN amount FLOAT DEFAULT 0')
            if 'stop_loss_percentage' not in columns:
                cursor.execute('ALTER TABLE intentions ADD COLUMN stop_loss_percentage FLOAT DEFAULT 0')
            if 'take_profit_percentage' not in columns:
                cursor.execute('ALTER TABLE intentions ADD COLUMN take_profit_percentage FLOAT DEFAULT 0')

            # Create intention_schedules table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS intention_schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    intention_id INTEGER NOT NULL,
                    buy_datetime TEXT,
                    sell_datetime TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (intention_id) REFERENCES intentions(id)
                )
            ''')

            # Create providers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS providers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    server_provider_id TEXT NOT NULL,
                    server_id INTEGER NOT NULL,
                    url TEXT,
                    api_key TEXT,
                    selected BOOLEAN DEFAULT 0,
                    exchange_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(server_provider_id, server_id)
                )
            ''')

            # Create catalogs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS catalogs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    aetherone_catalog_id INTEGER NOT NULL UNIQUE,
                    selected BOOLEAN DEFAULT 0
                )
            ''')
            conn.commit()

    def get_or_create_case(self, aetherone_case_id: int, name: str, catalog_id: int) -> Dict[str, Any]:
        """Get existing case or create new one with catalog selection."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if case exists
            cursor.execute('SELECT * FROM cases WHERE aetherone_case_id = ?', (aetherone_case_id,))
            existing_case = cursor.fetchone()
            
            if existing_case:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, existing_case))
            
            # Create new case
            cursor.execute('''
                INSERT INTO cases (
                    aetherone_case_id, name, catalog_id
                ) VALUES (?, ?, ?)
            ''', (
                aetherone_case_id,
                name,
                catalog_id
            ))
            conn.commit()
            
            # Return the newly created case
            new_id = cursor.lastrowid
            cursor.execute('SELECT * FROM cases WHERE id = ?', (new_id,))
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, cursor.fetchone()))

    def get_cases(self) -> List[Dict[str, Any]]:
        """Get all cases created through FinCompass."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM cases ORDER BY created_at DESC')
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def add_server(self, url: str, description: str = None, selected: bool = False, api_key: str = None, exchange_id: str = None) -> dict:
        """Add a new server/provider. If selected is True, unselect all others."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if selected:
                cursor.execute('UPDATE servers SET selected = 0')
            cursor.execute('''
                INSERT OR IGNORE INTO servers (url, description, selected, api_key)
                VALUES (?, ?, ?, ?)
            ''', (url, description, int(selected), api_key))
            # Add provider with exchange_id if provided
            if exchange_id:
                cursor.execute('''
                    INSERT OR IGNORE INTO providers (url, server_id, exchange_id)
                    VALUES (?, (SELECT id FROM servers WHERE url = ?), ?)
                ''', (url, url, exchange_id))
            conn.commit()
            cursor.execute('SELECT * FROM servers WHERE url = ?', (url,))
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, cursor.fetchone()))

    def update_server_api_key(self, url: str, api_key: str) -> None:
        """Update the API key for a given server URL."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE servers SET api_key = ? WHERE url = ?', (api_key, url))
            conn.commit()

    def get_servers(self) -> List[Dict[str, Any]]:
        """Get all servers."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM servers ORDER BY created_at DESC')
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def set_selected_server(self, url: str) -> None:
        """Set the selected server by URL, unselect all others."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE servers SET selected = 0')
            cursor.execute('UPDATE servers SET selected = 1 WHERE url = ?', (url,))
            conn.commit()

    def get_selected_server(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected server, if any."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM servers WHERE selected = 1 LIMIT 1')
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None

    def create_intention(self, intention: str, description: str = None, selected: bool = False, hold_minutes: int = 0, amount: float = 0, stop_loss_percentage: float = 0, take_profit_percentage: float = 0) -> Dict[str, Any]:
        """Create a new intention."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if selected:
                cursor.execute('UPDATE intentions SET selected = 0')
            cursor.execute('''
                INSERT INTO intentions (intention, description, selected, hold_minutes, amount, stop_loss_percentage, take_profit_percentage)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (intention, description, int(selected), hold_minutes, amount, stop_loss_percentage, take_profit_percentage))
            conn.commit()
            cursor.execute('SELECT * FROM intentions WHERE id = ?', (cursor.lastrowid,))
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, cursor.fetchone()))

    def get_intentions(self) -> List[Dict[str, Any]]:
        """Get all intentions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM intentions ORDER BY id DESC')
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def update_intention(self, intention_id: int, intention: str = None, description: str = None, selected: bool = None, hold_minutes: int = None, amount: float = None, stop_loss_percentage: float = None, take_profit_percentage: float = None) -> None:
        """Update an intention."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if selected is not None:
                if selected:
                    cursor.execute('UPDATE intentions SET selected = 0')
                cursor.execute('UPDATE intentions SET selected = ? WHERE id = ?', (int(selected), intention_id))
            if intention is not None:
                cursor.execute('UPDATE intentions SET intention = ? WHERE id = ?', (intention, intention_id))
            if description is not None:
                cursor.execute('UPDATE intentions SET description = ? WHERE id = ?', (description, intention_id))
            if hold_minutes is not None:
                cursor.execute('UPDATE intentions SET hold_minutes = ? WHERE id = ?', (hold_minutes, intention_id))
            if amount is not None:
                cursor.execute('UPDATE intentions SET amount = ? WHERE id = ?', (amount, intention_id))
            if stop_loss_percentage is not None:
                cursor.execute('UPDATE intentions SET stop_loss_percentage = ? WHERE id = ?', (stop_loss_percentage, intention_id))
            if take_profit_percentage is not None:
                cursor.execute('UPDATE intentions SET take_profit_percentage = ? WHERE id = ?', (take_profit_percentage, intention_id))
            conn.commit()

    def delete_intention(self, intention_id: int) -> None:
        """Delete an intention."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM intentions WHERE id = ?', (intention_id,))
            conn.commit()

    def store_providers(self, server_id: int, providers: List[Dict[str, Any]]) -> None:
        """Store or update providers for a specific server."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for provider in providers:
                cursor.execute('''
                    INSERT INTO providers (name, server_provider_id, server_id)
                    VALUES (?, ?, ?)
                    ON CONFLICT(server_provider_id, server_id) DO NOTHING
                ''', (provider['name'], provider['id'], server_id))
            conn.commit()

    def get_providers_by_server(self, server_id: int) -> list:
        """Get all providers for a specific server, including exchange_id."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM providers WHERE server_id = ?', (server_id,))
            return [dict(row) for row in cursor.fetchall()]

    def set_selected_provider(self, server_id: int, provider_id: int) -> None:
        """Set a provider as selected for a given server, unselecting others."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Unselect all providers for this server first
            cursor.execute('UPDATE providers SET selected = 0 WHERE server_id = ?', (server_id,))
            # Select the new provider
            cursor.execute('UPDATE providers SET selected = 1 WHERE id = ? AND server_id = ?', (provider_id, server_id))
            conn.commit()

    def sync_catalogs(self, catalogs_data: List[Dict[str, Any]]) -> None:
        """Insert or ignore catalogs from AetherOnePy."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for catalog in catalogs_data:
                cursor.execute('''
                    INSERT INTO catalogs (name, aetherone_catalog_id)
                    VALUES (?, ?)
                    ON CONFLICT(aetherone_catalog_id) DO NOTHING
                ''', (catalog['name'], catalog['id']))
            conn.commit()

    def get_catalogs(self) -> List[Dict[str, Any]]:
        """Get all catalogs stored in the plugin's database."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM catalogs ORDER BY name')
            return [dict(row) for row in cursor.fetchall()]

    def set_selected_catalog(self, catalog_id: int) -> None:
        """Set a catalog as selected, unselecting all others. If catalog_id is None, deselect all."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE catalogs SET selected = 0')
            if catalog_id is not None:
                cursor.execute('UPDATE catalogs SET selected = 1 WHERE id = ?', (catalog_id,))
            conn.commit()

    def get_catalogs_from_aetheronepy(self) -> list:
        """Read catalogs from the main AetherOnePy database (data/aetherone.db)."""
        import sqlite3, os
        catalogs = []
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../data/aetherone.db'))
        if not os.path.exists(db_path):
            print(f"[FinCompass] Database file does not exist: {db_path}")
            return catalogs
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT id, name FROM catalog ORDER BY name')
            for row in cursor.fetchall():
                catalogs.append({'id': row[0], 'name': row[1]})
            conn.close()
        except Exception as e:
            print(f"[FinCompass] Could not read catalogs from {db_path}: {e}")
        return catalogs

    def debug_print_aetheronepy_catalogs(self):
        import sqlite3, os
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../data/aetherone.db'))
        if not os.path.exists(db_path):
            print(f"[FinCompass DEBUG] Database file does not exist: {db_path}")
            return
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            print('--- TABLES IN data/aetherone.db ---')
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            for row in cursor.fetchall():
                print(row[0])
            print('--- FIRST 10 ROWS FROM catalog ---')
            cursor.execute('SELECT * FROM catalog LIMIT 10')
            for row in cursor.fetchall():
                print(row)
            conn.close()
        except Exception as e:
            print(f"[FinCompass DEBUG] Could not read catalogs from {db_path}: {e}")

    def get_provider_with_url_by_exchange_id(self, server_id: int, exchange_id: str) -> dict:
        """Get a provider by exchange_id and server_id, including the server's URL."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.*, s.url as server_url
                FROM providers p
                JOIN servers s ON p.server_id = s.id
                WHERE p.server_id = ? AND p.exchange_id = ?
                LIMIT 1
            ''', (server_id, exchange_id))
            row = cursor.fetchone()
            return dict(row) if row else None

    def set_selected_case(self, case_id: Optional[int]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE cases SET selected = 0')
            if case_id is not None:
                cursor.execute('UPDATE cases SET selected = 1 WHERE id = ?', (case_id,))
            conn.commit()

    def get_selected_case(self) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM cases WHERE selected = 1 LIMIT 1')
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None

    def get_cases_from_aetheronepy(self) -> list:
        """Read cases from the main AetherOnePy database (data/aetherone.db)."""
        import sqlite3, os
        cases = []
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../data/aetherone.db'))
        if not os.path.exists(db_path):
            print(f"[FinCompass] Database file does not exist: {db_path}")
            return cases
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT id, name FROM cases ORDER BY id')
            for row in cursor.fetchall():
                cases.append({'id': row[0], 'name': row[1]})
            conn.close()
        except Exception as e:
            print(f"[FinCompass] Could not read cases from {db_path}: {e}")
        return cases

    def sync_cases(self, cases_data: list) -> None:
        """Insert or ignore cases from AetherOnePy."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for case in cases_data:
                cursor.execute('''
                    INSERT OR IGNORE INTO cases (aetherone_case_id, name)
                    VALUES (?, ?)
                ''', (case['id'], case['name']))
            conn.commit()

    def create_intention_schedule(self, intention_id: int, buy_datetime: str, sell_datetime: str, status: str = 'pending', server_schedule_buy_id: str = None, server_schedule_sell_id: str = None) -> dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Add columns if they do not exist
            cursor.execute("PRAGMA table_info(intention_schedules)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'server_schedule_buy_id' not in columns:
                cursor.execute('ALTER TABLE intention_schedules ADD COLUMN server_schedule_buy_id TEXT')
            if 'server_schedule_sell_id' not in columns:
                cursor.execute('ALTER TABLE intention_schedules ADD COLUMN server_schedule_sell_id TEXT')
            # Insert with new columns
            cursor.execute('''
                INSERT INTO intention_schedules (intention_id, buy_datetime, sell_datetime, status, server_schedule_buy_id, server_schedule_sell_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (intention_id, buy_datetime, sell_datetime, status, server_schedule_buy_id, server_schedule_sell_id))
            conn.commit()
            cursor.execute('SELECT * FROM intention_schedules WHERE id = ?', (cursor.lastrowid,))
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, cursor.fetchone()))

    def get_schedules_for_intention(self, intention_id: int) -> list:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM intention_schedules WHERE intention_id = ? ORDER BY created_at DESC', (intention_id,))
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def update_intention_schedule(self, schedule_id: int, buy_datetime: str = None, sell_datetime: str = None, status: str = None) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if buy_datetime is not None:
                cursor.execute('UPDATE intention_schedules SET buy_datetime = ? WHERE id = ?', (buy_datetime, schedule_id))
            if sell_datetime is not None:
                cursor.execute('UPDATE intention_schedules SET sell_datetime = ? WHERE id = ?', (sell_datetime, schedule_id))
            if status is not None:
                cursor.execute('UPDATE intention_schedules SET status = ? WHERE id = ?', (status, schedule_id))
            conn.commit()

    def deselect_provider(self, server_id: int, provider_id: int) -> None:
        """Deselect a single provider for a given server (set selected=0 for that provider only)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE providers SET selected = 0 WHERE id = ? AND server_id = ?', (provider_id, server_id))
            conn.commit()

    def get_provider_with_url_by_exchange_and_server_provider_id_and_url(self, exchange_id: str, server_provider_id: str, url: str) -> dict:
        """
        Get a provider and its server's URL by exchange_id, server_provider_id, and server url.
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.*, s.url as server_url
                FROM providers p
                JOIN servers s ON p.server_id = s.id
                WHERE p.exchange_id = ? AND p.server_provider_id = ? AND s.url = ?
                LIMIT 1
            ''', (exchange_id, server_provider_id, url))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_providers(self) -> list:
        """Get all providers from the database."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM providers')
            return [dict(row) for row in cursor.fetchall()]

    def get_provider_by_server_and_provider_id(self, server_id: int, server_provider_id: str) -> dict:
        """Get a provider by server_id and server_provider_id, including the server's URL."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.*, s.url as server_url
                FROM providers p
                JOIN servers s ON p.server_id = s.id
                WHERE p.server_id = ? AND p.server_provider_id = ?
                LIMIT 1
            ''', (server_id, server_provider_id))
            row = cursor.fetchone()
            return dict(row) if row else None

    def loadSettings(self) -> dict:
        """Load settings from the main AetherOnePy settings file."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
        json_file_path = os.path.join(project_root, "data", "settings.json")
        if os.path.isfile(json_file_path):
            with open(json_file_path, 'r') as f:
                settings = json.load(f)
                self.ensure_settings_defaults(settings)
                return settings
        else:
            with open(json_file_path, 'w') as f:
                settings = {'created': datetime.now().isoformat()}
                self.ensure_settings_defaults(settings)
                json.dump(settings, f)
            return settings

    def ensure_settings_defaults(self, settings: dict):
        """Ensure default settings exist."""
        defaults = {
            'analysisAlwaysCheckGV': True,
            'analysisAdvanced': False
        }
        for key, value in defaults.items():
            if key not in settings:
                settings[key] = value

    def get_setting(self, key: str):
        """Get a setting value by key."""
        try:
            return self.loadSettings()[key]
        except:
            return None
