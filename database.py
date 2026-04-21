import sqlite3
import os

DB_PATH = 'agrismart.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    with conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS grain_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                default_days_to_harvest INTEGER NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS crops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                grain_type_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                planted_date DATE NOT NULL,
                expected_harvest_date DATE NOT NULL,
                status TEXT NOT NULL DEFAULT 'Growing',
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (grain_type_id) REFERENCES grain_types (id)
            );
            
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crop_id INTEGER NOT NULL,
                log_date DATE NOT NULL,
                log_type TEXT NOT NULL,
                cost REAL NOT NULL DEFAULT 0.0,
                notes TEXT,
                FOREIGN KEY (crop_id) REFERENCES crops (id) ON DELETE CASCADE
            );
        ''')
    conn.close()
