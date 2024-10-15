import os
import sqlite3 as sql
import json
from datetime import datetime
from bot.config import DB_PATH, ROOTADMIN_INFO

def connect_db() -> sql.Connection: 
    """Function to connect to the database 
    (or create it if it doesn't exist)
    """
    
    print(os.path.abspath(DB_PATH))
    conn = sql.connect(DB_PATH)
    return conn

def close_db(conn: sql.Connection):
    """Close the database connection."""
    
    conn.close()

def create_tables(cursor: sql.Cursor):
    """Create the required tables in the database, if they do not already exist.
    Insert then the root admin with primary key 1."""
    
    cursor.executescript("""
        -- Create the players table
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL CHECK (first_name GLOB '[A-Za-z]*' AND LENGTH(first_name) <= 50),
            last_name TEXT NOT NULL CHECK (last_name GLOB '[A-Za-z]*' AND LENGTH(last_name) <= 50),
            admin BOOLEAN NOT NULL DEFAULT 0,
            tg_uid INTEGER NOT NULL,
            nickname TEXT NOT NULL CHECK (nickname GLOB '[A-Za-z0-9!@#$%^&*()_+]*' AND LENGTH(nickname) <= 30),
            date DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Create the games table
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY,
            first_team JSON NOT NULL,
            second_team JSON NOT NULL,
            score JSON NOT NULL CHECK (json_valid(score) AND
                                      (json_extract(score, '$.first_team') BETWEEN 0 AND 10) AND
                                      (json_extract(score, '$.second_team') BETWEEN 0 AND 10)),
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            confirm_admin_id INTEGER,
            confirm_date DATETIME,
            FOREIGN KEY (confirm_admin_id) REFERENCES players(id)
        );

        -- Create the pending_games table
        CREATE TABLE IF NOT EXISTS pending_games (
            id INTEGER PRIMARY KEY,
            first_team JSON NOT NULL,
            second_team JSON NOT NULL,
            score JSON NOT NULL CHECK (json_valid(score) AND
                                      (json_extract(score, '$.first_team') BETWEEN 0 AND 10) AND
                                      (json_extract(score, '$.second_team') BETWEEN 0 AND 10)),
            date DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
def insert_rootadmin(cursor: sql.Cursor) -> None:
    """Insert, if it doesn't exist, the ROOTADMIN_INFO into the players table with 
    primary key 1."""
    
    cursor.execute("SELECT COUNT(*) FROM players WHERE id = 1")
    # Check if the ROOT admin does not already exist
    if cursor.fetchone()[0] == 0:  
    
        if ROOTADMIN_INFO:
            # Parse the JSON string into a dictionary, then set key if and datre
            rootadmin_data = json.loads(ROOTADMIN_INFO)
            rootadmin_data['id'] = 1
            rootadmin_data['date'] = datetime.now().isoformat()

            # Insert into the players table
            cursor.execute("""
                INSERT INTO players (id, first_name, last_name, admin, tg_uid, nickname, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                rootadmin_data['id'],
                rootadmin_data['first_name'],
                rootadmin_data['last_name'],
                rootadmin_data['admin'],
                rootadmin_data['tg_uid'],
                rootadmin_data['nickname'],
                rootadmin_data['date']
            ))
    
def players_get_nicknames(cursor: sql.Cursor) -> list:
    """Retrieve a list of all nicknames of registered players."""
    
    cursor.execute("SELECT nickname FROM players")
    return [row[0] for row in cursor.fetchall()]
    
def players_get_ids_by_nicknames(cursor: sql.Cursor, nicknames: list) -> list:
    """Get player IDs from the database based on the list of nicknames."""
    
    # Create placeholders for the query
    placeholders = ', '.join('?' for _ in nicknames)
    query = f"SELECT id FROM players WHERE nickname IN ({placeholders})"
    
    # Retrieve player IDs
    cursor.execute(query, nicknames)
    player_ids = [row[0] for row in cursor.fetchall()]

    # Check if the number of retrieved IDs games the number of requested nicknames
    if len(player_ids) != len(nicknames):
        missing_nicknames = set(nicknames) - set(player_ids)
        raise ValueError(f"The following nicknames do not exist in the players table: {', '.join(missing_nicknames)}")
