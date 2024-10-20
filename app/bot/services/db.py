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
            
            -- Create the banned_users table
            CREATE TABLE IF NOT EXISTS banned_users (
                id INTEGER PRIMARY KEY,
                tg_uid INTEGER NOT NULL,
                reason TEXT,
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tg_uid)  -- Ensure each user is unique
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
        cursor.execute("SELECT * FROM pending_games")
        rows = cursor.fetchall()

        column_names = [description[0] for description in cursor.description]
        pending_games = []
        for row in rows:
            game_data = {column_names[i]: row[i] for i in range(len(column_names))}
            pending_games.append(game_data)

        return pending_games
    
    
    @staticmethod
    def get_player_info_by_tg_uid(tg_uid: int) -> dict:
        """Retrieve player information from the database based on tg_uid and return it as a dictionary."""
        
        cursor = Database()._instance.cursor
        cursor.execute("SELECT * FROM players WHERE tg_uid = ?", (tg_uid,))
        player = cursor.fetchone()
        
        if player is None:
            raise ValueError("Player not found.")

        column_names = [description[0] for description in cursor.description]
        player_info = {column_names[i]: player[i] for i in range(len(column_names))}

        return player_info
    
    
    @staticmethod
    def get_player_info_by_nickname(nickname: str) -> dict:
        """Retrieve player information from the database based on nickname and return it as a dictionary."""
        
        cursor = Database()._instance.cursor
        cursor.execute("SELECT * FROM players WHERE nickname = ?", (nickname,))
        player = cursor.fetchone()
        
        if player is None:
            raise ValueError("Player not found.")

        column_names = [description[0] for description in cursor.description]
        player_info = {column_names[i]: player[i] for i in range(len(column_names))}

        return player_info
    
    
    @staticmethod
    def edit_player_info_by_tg_uid(tg_uid: int, update_data: dict) -> bool:
        """Edit player information in the database based on tg_uid and provided data dictionary.
        
        Returns True if the player is found and the operation is successful, otherwise returns False.
        """
        
        cursor = Database()._instance.cursor
        cursor.execute("SELECT COUNT(*) FROM players WHERE tg_uid = ?", (tg_uid,))
        if cursor.fetchone()[0] == 0:
            return False

        set_clause = ", ".join(f"{key} = ?" for key in update_data.keys())
        values = list(update_data.values())
        
        try:
            cursor.execute(f"UPDATE players SET {set_clause} WHERE tg_uid = ?", (*values, tg_uid))
            Database()._instance.connection.commit()
            return True
        except Exception as e:
            return False
    
    @staticmethod
    def edit_player_info_by_nickname(nickname: str, update_data: dict) -> bool:
        """Edit player information in the database based on nickname and provided data dictionary.
        
        Returns True if the player is found and the operation is successful, otherwise returns False.
        """
        
        cursor = Database()._instance.cursor
        
        # Check if the player exists based on nickname
        cursor.execute("SELECT COUNT(*) FROM players WHERE nickname = ?", (nickname,))
        if cursor.fetchone()[0] == 0:
            return False  # Player not found

        # Prepare the SQL update statement
        set_clause = ", ".join(f"{key} = ?" for key in update_data.keys())
        values = list(update_data.values())
        
        try:
            # Execute the update query with the nickname at the end
            cursor.execute(f"UPDATE players SET {set_clause} WHERE nickname = ?", (*values, nickname))
            Database()._instance.connection.commit()  # Commit the transaction
            return True  # Update successful
        except Exception as e:
            print(f"An error occurred: {e}")  # Optional: log the error for debugging
            return False  # Operation failed
        
        
    @staticmethod
    def player_is_registered(tg_uid: int) -> bool:
        """Check if a player exists in the database based on tg_uid.
        
        Returns True if the player is found, otherwise returns False.
        """
        
        cursor = Database()._instance.cursor
        cursor.execute("SELECT COUNT(*) FROM players WHERE tg_uid = ?", (tg_uid,))
        return cursor.fetchone()[0] > 0
    
    
    @staticmethod
    def player_is_banned(tg_uid: int) -> bool:
        """Check if a player has been ever banned based on tg_uid.
        
        Returns True if the player is banned, otherwise returns False.
        """
        
        cursor = Database()._instance.cursor
        cursor.execute("SELECT COUNT(*) FROM banned_users WHERE tg_uid = ?", (tg_uid,))
        return cursor.fetchone()[0] > 0
    
    
    @staticmethod
    def ban_user(tg_uid: int, reason: str) -> None:
        """Ban a user by inserting their tg_uid into the banned_users table."""
        
        cursor = Database()._instance.cursor
        cursor.execute("""
            INSERT INTO banned_users (tg_uid, reason) 
            VALUES (?, ?)
        """, (tg_uid, reason))
        
        Database()._instance.connection.commit()
        
        
    @staticmethod
    def delete_banned_user(tg_uid: int) -> None:
        """Delete a user from the banned_users table based on tg_uid."""
        
        cursor = Database()._instance.cursor
        cursor.execute("DELETE FROM banned_users WHERE tg_uid = ?", (tg_uid,))
        Database()._instance.connection.commit()
        
        
    @staticmethod
    def get_banned_users() -> list:
        """Retrieve a list of all tg_uid values from the banned_users table."""
        
        cursor = Database()._instance.cursor
        cursor.execute("SELECT tg_uid FROM banned_users")
        banned_users = cursor.fetchall() 
        return [f"{row[0]}" for row in banned_users]
    
    
    @staticmethod
    def get_similar_players(search_string: str) -> list:
        """Retrieve a list of players whose first name, last name, or nickname is similar to the input string.
        
        Args:
            search_string (str): The string to search for in player names and nicknames.
            
        Returns:
            list: A list of dictionaries containing player information.
        """
        
        cursor = Database()._instance.cursor
        query = """
            SELECT * FROM players
            WHERE LOWER(first_name) LIKE LOWER(?) OR
                LOWER(last_name) LIKE LOWER(?) OR
                LOWER(nickname) LIKE LOWER(?)
        """
        
        search_pattern = f"%{search_string}%"
        cursor.execute(query, (search_pattern, search_pattern, search_pattern))
        players = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        
        similar_players = []
        for row in players:
            player_info = {column_names[i]: row[i] for i in range(len(column_names))}
            similar_players.append(player_info)

        return similar_players


    @staticmethod
    def get_admins_tg_uid() -> list:
        """Retrieve a list of tg_uid values of players with admin rights from the database.
        
        Returns:
            list: A list of tg_uid values for players with admin rights.
        """
        
        cursor = Database()._instance.cursor
        cursor.execute("SELECT tg_uid FROM players WHERE admin = 1")
        admin_tg_uids = cursor.fetchall()
        return [row[0] for row in admin_tg_uids]

