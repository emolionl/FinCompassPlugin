import sqlite3
import os
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
            
            # Create cases table with catalog selection
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fin_compass_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    aetherone_case_id INTEGER,
                    name TEXT NOT NULL,
                    catalog_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()

    def get_or_create_case(self, case_data: Dict[str, Any], catalog_id: int) -> Dict[str, Any]:
        """Get existing case or create new one with catalog selection."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if case exists
            cursor.execute('SELECT * FROM fin_compass_cases WHERE aetherone_case_id = ?', (case_data.get('id'),))
            existing_case = cursor.fetchone()
            
            if existing_case:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, existing_case))
            
            # Create new case
            cursor.execute('''
                INSERT INTO fin_compass_cases (
                    aetherone_case_id, name, catalog_id
                ) VALUES (?, ?, ?)
            ''', (
                case_data.get('id'),
                case_data.get('name'),
                catalog_id
            ))
            conn.commit()
            
            # Return the newly created case
            cursor.execute('SELECT * FROM fin_compass_cases WHERE id = ?', (cursor.lastrowid,))
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, cursor.fetchone()))

    def get_cases(self) -> List[Dict[str, Any]]:
        """Get all cases created through FinCompass."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM fin_compass_cases ORDER BY created_at DESC')
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
