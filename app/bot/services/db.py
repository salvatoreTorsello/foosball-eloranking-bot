import os
import sqlite3 as sql
import json
from datetime import datetime
from bot.config import DB_PATH

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.connection = cls.connect_db()
            cls._instance.cursor = cls._instance.connection.cursor()
        return cls._instance

    @staticmethod
    def connect_db() -> sql.Connection: 
        """Function to connect to the database 
        (or create it if it doesn't exist)
        """
        
        return sql.connect(DB_PATH)

    @staticmethod
    def close_db():
        """Close the database connection."""
        
        print("Closing the database.")
        db_conn = Database()._instance.connection
        db_conn.commit()
        db_conn.close()


    @staticmethod
    def create_tables():
        """Create the required tables in the database, 
        if they do not already exist."""
        
        cursor = Database()._instance.cursor
        cursor.executescript("""
            -- Create the players table
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY,
                first_name TEXT NOT NULL CHECK (first_name GLOB '[A-Za-z]*' AND LENGTH(first_name) <= 50),
                last_name TEXT NOT NULL CHECK (last_name GLOB '[A-Za-z]*' AND LENGTH(last_name) <= 50),
                admin BOOLEAN NOT NULL DEFAULT 0,
                tg_uid INTEGER,
                nickname TEXT NOT NULL CHECK (nickname GLOB '[A-Za-z0-9!@#$%^&*()_+]*' AND LENGTH(nickname) <= 30),
                date DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- Create the games table
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY,
                team1 JSON NOT NULL,
                team2 JSON NOT NULL,
                scores JSON NOT NULL CHECK (json_valid(scores) AND
                                        (json_extract(scores, '$.team1') BETWEEN 0 AND 10) AND
                                        (json_extract(scores, '$.team2') BETWEEN 0 AND 10)),
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                confirm_admin_id INTEGER,
                confirm_date DATETIME,
                FOREIGN KEY (confirm_admin_id) REFERENCES players(id)
            );

            -- Create the pending_games table
            CREATE TABLE IF NOT EXISTS pending_games (
                id INTEGER PRIMARY KEY,
                team1 JSON NOT NULL,
                team2 JSON NOT NULL,
                scores JSON NOT NULL CHECK (json_valid(scores) AND
                                        (json_extract(scores, '$.team1') BETWEEN 0 AND 10) AND
                                        (json_extract(scores, '$.team2') BETWEEN 0 AND 10)),
                date DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- Create the archived_games table
            CREATE TABLE IF NOT EXISTS archived_games (
                id INTEGER PRIMARY KEY,
                team1 JSON NOT NULL,
                team2 JSON NOT NULL,
                scores JSON NOT NULL CHECK (json_valid(scores) AND
                                        (json_extract(scores, '$.team1') BETWEEN 0 AND 10) AND
                                        (json_extract(scores, '$.team2') BETWEEN 0 AND 10)),
                date DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        Database()._instance.connection.commit()
                
                
    @staticmethod
    def insert_player(player_data: dict) -> None:
        """Insert a player into the players table."""
        
        cursor = Database()._instance.cursor
        
        # Check if the player already exists based on tg_uid
        cursor.execute("SELECT COUNT(*) FROM players WHERE tg_uid = ?", (player_data['tg_uid'],))
        
        if cursor.fetchone()[0] == 0:  
            # Ensure the necessary fields are present
            required_fields = ['first_name', 'last_name', 'admin', 'tg_uid', 'nickname']
            if all(field in player_data for field in required_fields):
                player_data['date'] = datetime.now().isoformat()

                # Insert into the players table
                cursor.execute("""
                    INSERT INTO players (first_name, last_name, admin, tg_uid, nickname, date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    player_data['first_name'],
                    player_data['last_name'],
                    player_data['admin'],
                    player_data['tg_uid'],
                    player_data['nickname'],
                    player_data['date']
                ))
            else:
                raise ValueError("Input dictionary is missing required fields.")
            Database()._instance.connection.commit()
            
    
    @staticmethod
    def insert_pending_game(game_data: dict) -> None:
        """Insert a game into the pending_games table."""
        
        cursor = Database()._instance.cursor
        
        # Ensure the necessary fields are present
        required_fields = ['team1', 'team2', 'scores']
        if all(field in game_data for field in required_fields):
            game_data['date'] = datetime.now().isoformat()  # Set the current date
            
            # Insert into the pending_games table
            cursor.execute("""
                INSERT INTO pending_games (team1, team2, scores, date)
                VALUES (?, ?, ?, ?)
            """, (
                json.dumps(game_data['team1']),  # Assuming team1 is a JSON object
                json.dumps(game_data['team2']),  # Assuming team2 is a JSON object
                json.dumps(game_data['scores']),  # Assuming scores is a JSON object
                game_data['date']
            ))
            
            Database()._instance.connection.commit()  # Commit the transaction
        else:
            raise ValueError("Input dictionary is missing required fields.")
    
    
    @staticmethod
    def confirm_pending_game(game_id: int, confirm_admin_id: int) -> None:
        """Delete a pending game and insert it into the games table."""
        
        cursor = Database()._instance.cursor
        
        # Fetch the pending game details using the provided game_id
        cursor.execute("SELECT * FROM pending_games WHERE id = ?", (game_id,))
        game = cursor.fetchone()
        
        if game is None:
            raise ValueError("Pending game not found.")

        # Construct the game data to insert into the games table
        game_data = {
            "team1": json.loads(game[1]),
            "team2": json.loads(game[2]),
            "scores": json.loads(game[3]),
            "confirm_admin_id": confirm_admin_id,
            "confirm_date": datetime.now().isoformat()
        }
        
        # Insert into the games table
        cursor.execute("""
            INSERT INTO games (team1, team2, scores, date, confirm_admin_id, confirm_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            json.dumps(game_data['team1']),
            json.dumps(game_data['team2']),
            json.dumps(game_data['scores']),
            datetime.now().isoformat(),
            confirm_admin_id,
            game_data['confirm_date']
        ))
        
        # Delete the game from the pending_games table
        cursor.execute("DELETE FROM pending_games WHERE id = ?", (game_id,))
        
        Database()._instance.connection.commit()
        
    
    @staticmethod
    def archive_pending_game(game_id: int, confirm_admin_id: int) -> None:
        """Delete a pending game and insert it into the archived games table."""
        
        cursor = Database()._instance.cursor
        
        # Fetch the pending game details using the provided game_id
        cursor.execute("SELECT * FROM pending_games WHERE id = ?", (game_id,))
        game = cursor.fetchone()
        
        if game is None:
            raise ValueError("Pending game not found.")

        # Insert into the archived games table
        cursor.execute("""
            INSERT INTO archived_games (team1, team2, scores, date)
            VALUES (?, ?, ?, ?)
        """, (
            game[1],
            game[2],
            game[3],
            game[4]
        ))
        
        # Delete the game from the pending_games table
        cursor.execute("DELETE FROM pending_games WHERE id = ?", (game_id,))
        
        Database()._instance.connection.commit()


##### Getters ######

        
    @staticmethod
    def players_get_nicknames() -> list:
        """Retrieve a list of all nicknames of registered players."""
        
        cursor = Database()._instance.cursor
        cursor.execute("SELECT nickname FROM players")
        return [row[0] for row in cursor.fetchall()]
        
        
    @staticmethod
    def players_get_ids_by_nicknames(nicknames: list) -> list:
        """Get player IDs from the database based on the list of nicknames."""
        
        cursor = Database()._instance.cursor
        
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
        return player_ids


    @staticmethod
    def players_get_ids() -> list:
        """Get all players IDS."""
        
        cursor = Database()._instance.cursor
        
        # Create the query
        query = "SELECT tg_uid FROM players"
        
        # Retrieve player IDs
        cursor.execute(query)
        player_ids = [row[0] for row in cursor.fetchall()]
        return player_ids
    

    @staticmethod
    def get_pending_games() -> list:
        """Retrieve all pending games from the database and return them as a list of dictionaries."""
        
        cursor = Database()._instance.cursor
        cursor.execute("SELECT * FROM pending_games")  # Fetch all data from pending_games
        rows = cursor.fetchall()  # Get all rows

        # Get column names from the cursor description
        column_names = [description[0] for description in cursor.description]
        
        # Create a list of dictionaries
        pending_games = []
        for row in rows:
            game_data = {column_names[i]: row[i] for i in range(len(column_names))}
            pending_games.append(game_data)

        return pending_games