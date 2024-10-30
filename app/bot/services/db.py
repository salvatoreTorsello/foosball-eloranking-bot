import os
import sqlite3 as sql
import json
import re
from typing import List, Dict, Tuple
from datetime import datetime
from bot.config import DB_PATH
from bot.services import elo

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def initialize(self) -> tuple:
        """Initialize the database connection and return success/error tuple."""
        success, connection_or_error = self.connect_db()
        if not success:
            return False, connection_or_error

        self.connection = connection_or_error
        self.cursor = self.connection.cursor()
        return True, "Database initialized successfully."


    @staticmethod
    def connect_db() -> tuple:
        """Function to connect to the database (or create it if it doesn't exist).
        
        Returns (success: bool, connection: sql.Connection or error_message: str)
        """
        try:
            connection = sql.connect(DB_PATH)
            return True, connection
        except sql.Error as e:
            return False, f"Failed to connect to the database: {e}"

    @staticmethod
    def close_db() -> tuple:
        """Close the database connection.
        
        Returns (success: bool, message: str)
        """
        try:
            print("Closing the database.")
            db_conn = Database()._instance.connection
            db_conn.commit()
            db_conn.close()
            return True, "Database connection closed successfully."
        except sql.Error as e:
            return False, f"Failed to close the database: {e}"

    @staticmethod
    def create_tables() -> tuple:
        """Create the required tables in the database, if they do not already exist.
        
        Returns (success: bool, message: str)
        """
        try:
            cursor = Database()._instance.cursor
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY,
                    first_name TEXT NOT NULL CHECK (first_name GLOB '[A-Za-z]*' AND LENGTH(first_name) <= 50),
                    last_name TEXT NOT NULL CHECK (last_name GLOB '[A-Za-z]*' AND LENGTH(last_name) <= 50),
                    admin BOOLEAN NOT NULL DEFAULT 0,
                    tg_uid INTEGER,
                    nickname TEXT NOT NULL CHECK (nickname GLOB '[A-Za-z0-9!@#$%^&*()_+]*' AND LENGTH(nickname) <= 30),
                    date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    elo INTEGER NOT NULL CHECK (elo >= 50) DEFAULT 1000,
                    num_games INTEGER NOT NULL CHECK (num_games >= 0) DEFAULT 0
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
            return True, "Tables created successfully."
        except sql.Error as e:
            return False, f"Failed to create tables: {e}"

        
    
    @staticmethod
    def validate_player_field(field_name: str, field_value: str) -> tuple:
        """
        Validate a specific field for the players table.
        Returns a tuple: (bool, str), where bool indicates if the field is valid, and str contains an error message if invalid.
        """
        # Define the constraints for each field
        if field_name == 'first_name' or field_name == 'last_name':
            # Must be alphabetic and up to 50 characters
            if not isinstance(field_value, str) or not field_value.isalpha() or len(field_value) > 50:
                return False, f"{field_name.capitalize()} must be alphabetic and up to 50 characters."

        elif field_name == 'nickname':
            # Must be alphanumeric or special characters and up to 30 characters
            if not isinstance(field_value, str) or len(field_value) > 30 or not re.match(r'^[A-Za-z0-9!@#$%^&*()_+]*$', field_value):
                return False, "Nickname must be alphanumeric or special characters (!@#$%^&*()_+) and up to 30 characters."

        else:
            return False, f"Unknown field: {field_name}"

        # If no error was found, return True
        return True, ""

            
    @staticmethod
    def insert_player(player_data: dict) -> tuple:
        """Insert a player into the players table and return (bool, str)."""
        
        cursor = Database()._instance.cursor

        # Ensure the necessary fields are present (except for fields with default values)
        required_fields = ['first_name', 'last_name', 'admin', 'nickname']
        if not all(field in player_data for field in required_fields):
            return False, "Input dictionary is missing required fields."

        player_data['date'] = datetime.now().isoformat()

        try:
            # Additional input validation before insertion
            if len(player_data['first_name']) > 50 or not player_data['first_name'].isalpha():
                return False, "First name must be alphabetic and up to 50 characters."
            
            if len(player_data['last_name']) > 50 or not player_data['last_name'].isalpha():
                return False, "Last name must be alphabetic and up to 50 characters."
            
            if len(player_data['nickname']) > 30 or not all(c.isalnum() or c in '!@#$%^&*()_+' for c in player_data['nickname']):
                return False, "Nickname must be alphanumeric or special characters (!@#$%^&*()_+) and up to 30 characters."

            # Insert into the players table, letting the database use default values for missing fields (like tg_uid, elo, num_games)
            cursor.execute("""
                INSERT INTO players (first_name, last_name, admin, nickname, date)
                VALUES (?, ?, ?, ?, ?)
            """, (
                player_data['first_name'],
                player_data['last_name'],
                player_data['admin'],
                player_data['nickname'],
                player_data['date']
            ))

            # Commit the transaction
            Database()._instance.connection.commit()

            # If everything is successful, return True with an empty string for no error
            return True, ""

        except sql.IntegrityError as e:
            # Catch database-specific integrity errors (like CHECK constraints, uniqueness violations, etc.)
            return False, f"Database integrity error: {e}"
        
        except sql.Error as e:
            # Catch all other SQLite-related errors
            return False, f"Database error: {e}"


    @staticmethod
    def insert_pending_game(game_data: dict) -> tuple:
        """Insert a game into the pending_games table and return (bool, str)."""
        
        cursor = Database()._instance.cursor
        
        required_fields = ['team1', 'team2', 'scores']
        if not all(field in game_data for field in required_fields):
            return False, "Input dictionary is missing required fields."
        
        game_data['date'] = datetime.now().isoformat()  # Set the current date
        
        try:
            cursor.execute("""
                INSERT INTO pending_games (team1, team2, scores, date)
                VALUES (?, ?, ?, ?)
            """, (
                json.dumps(game_data['team1']),
                json.dumps(game_data['team2']),
                json.dumps(game_data['scores']),
                game_data['date']
            ))
            Database()._instance.connection.commit()
            return True, ""
        except sql.Error as e:
            return False, f"Database error: {e}"

    
    @staticmethod
    def confirm_pending_game(game_id: int, confirm_admin_id: int) -> tuple:
        """Confirm a pending game, calculate new Elo ratings, update game counts, and insert it into the games table.
        
        Args:
            game_id (int): The ID of the pending game.
            confirm_admin_id (int): The ID of the admin confirming the game.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        cursor = Database()._instance.cursor
        
        try:
            # Fetch the pending game details
            cursor.execute("SELECT * FROM pending_games WHERE id = ?", (game_id,))
            game = cursor.fetchone()
            
            if game is None:
                return False, "Pending game not found."

            # Extract teams and scores
            team1 = json.loads(game[1])
            team2 = json.loads(game[2])
            scores = json.loads(game[3])

            # Determine the winning and losing teams based on the score
            if scores['team1'] > scores['team2']:
                winning_team = team1
                losing_team = team2
            else:
                winning_team = team2
                losing_team = team1

            # Retrieve Elo ratings of players
            player_data = []
            for team, team_players in zip(['winners', 'losers'], [winning_team, losing_team]):
                team_elos = []
                for nickname in team_players['players']:
                    cursor.execute("SELECT elo, num_games FROM players WHERE nickname = ?", (nickname,))
                    result = cursor.fetchone()
                    if result is None:
                        return False, f"Player with nickname '{nickname}' not found in the database."
                    team_elos.append(result)
                player_data.append(team_elos)

            # Separate player data for easier access
            (elo_team1_player1, num_games_team1_player1), (elo_team1_player2, num_games_team1_player2) = player_data[0]
            (elo_team2_player1, num_games_team2_player1), (elo_team2_player2, num_games_team2_player2) = player_data[1]

            # Prepare the initial Elo dictionary and compute the updated one
            initial_elos = {
                'winners': [elo_team1_player1, elo_team1_player2],
                'losers': [elo_team2_player1, elo_team2_player2]
            }
            updated_elos = elo.compute_ratings(initial_elos)

            # Increment num_games for each player
            num_games_team1_player1 += 1
            num_games_team1_player2 += 1
            num_games_team2_player1 += 1
            num_games_team2_player2 += 1
            
            # Update the new Elo ratings and num_games in the database
            cursor.execute("UPDATE players SET elo = ?, num_games = ? WHERE nickname = ?", 
                        (updated_elos['winners'][0], num_games_team1_player1, winning_team['players'][0]))
            cursor.execute("UPDATE players SET elo = ?, num_games = ? WHERE nickname = ?", 
                        (updated_elos['winners'][1], num_games_team1_player2, winning_team['players'][1]))
            cursor.execute("UPDATE players SET elo = ?, num_games = ? WHERE nickname = ?", 
                        (updated_elos['losers'][0], num_games_team2_player1, losing_team['players'][0]))
            cursor.execute("UPDATE players SET elo = ?, num_games = ? WHERE nickname = ?", 
                        (updated_elos['losers'][1], num_games_team2_player2, losing_team['players'][1]))

            # Insert confirmed game into games table
            cursor.execute("""
                INSERT INTO games (team1, team2, scores, date, confirm_admin_id, confirm_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                json.dumps(team1),
                json.dumps(team2),
                json.dumps(scores),
                game[4],
                confirm_admin_id,
                datetime.now().isoformat()
            ))

            # Delete the game from the pending_games table
            cursor.execute("DELETE FROM pending_games WHERE id = ?", (game_id,))
            
            # Commit the transaction
            Database()._instance.connection.commit()

            return True, "Game confirmed, Elo ratings, and game counts updated successfully."

        except sql.Error as e:
            return False, f"Failed to confirm game: {e}"

        
    @staticmethod
    def archive_pending_game(game_id: int, confirm_admin_id: int) -> tuple:
        """Delete a pending game and insert it into the archived games table and return (bool, str)."""
        
        cursor = Database()._instance.cursor
        try:
            cursor.execute("SELECT * FROM pending_games WHERE id = ?", (game_id,))
            game = cursor.fetchone()
            
            if game is None:
                return False, "Pending game not found."
            
            cursor.execute("""
                INSERT INTO archived_games (team1, team2, scores, date)
                VALUES (?, ?, ?, ?)
            """, (
                game[1],
                game[2],
                game[3],
                game[4]
            ))
            
            cursor.execute("DELETE FROM pending_games WHERE id = ?", (game_id,))
            Database()._instance.connection.commit()
            return True, ""
        except sql.Error as e:
            return False, f"Database error: {e}"



##### Getters ######

        
    @staticmethod
    def players_get_nicknames() -> tuple:
        """Retrieve a list of all nicknames of registered players."""
        
        cursor = Database()._instance.cursor
        try:
            cursor.execute("SELECT nickname FROM players")
            return True, [row[0] for row in cursor.fetchall()]
        except sql.Error as e:
            return False, f"Database error: {e}"

        
    @staticmethod
    def players_get_ids_by_nicknames(nicknames: list) -> tuple:
        """Get player IDs from the database based on the list of nicknames."""
        
        cursor = Database()._instance.cursor
        try:
            placeholders = ', '.join('?' for _ in nicknames)
            query = f"SELECT id FROM players WHERE nickname IN ({placeholders})"
            cursor.execute(query, nicknames)
            player_ids = [row[0] for row in cursor.fetchall()]
            
            if len(player_ids) != len(nicknames):
                missing_nicknames = set(nicknames) - set(player_ids)
                return False, f"The following nicknames do not exist: {', '.join(missing_nicknames)}"
            return True, player_ids
        except sql.Error as e:
            return False, f"Database error: {e}"


    @staticmethod
    def players_get_ids() -> tuple:
        """Get all player IDs."""
        
        cursor = Database()._instance.cursor
        try:
            query = "SELECT tg_uid FROM players"
            cursor.execute(query)
            return True, [row[0] for row in cursor.fetchall()]
        except sql.Error as e:
            return False, f"Database error: {e}"


    @staticmethod
    def get_pending_games() -> tuple:
        """Retrieve all pending games and return them as a list of dictionaries."""
        
        cursor = Database()._instance.cursor
        try:
            cursor.execute("SELECT * FROM pending_games")
            rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            pending_games = [
                {column_names[i]: row[i] for i in range(len(column_names))} 
                for row in rows
            ]
            return True, pending_games
        except sql.Error as e:
            return False, f"Database error: {e}"

    
    @staticmethod
    def get_player_info_by_tg_uid(tg_uid: int) -> tuple:
        """Retrieve player info based on tg_uid and return it as a dictionary."""
        
        cursor = Database()._instance.cursor
        try:
            cursor.execute("SELECT * FROM players WHERE tg_uid = ?", (tg_uid,))
            player = cursor.fetchone()
            
            if player is None:
                return False, "Player not found."
            
            column_names = [description[0] for description in cursor.description]
            player_info = {column_names[i]: player[i] for i in range(len(column_names))}
            return True, player_info
        except sql.Error as e:
            return False, f"Database error: {e}"


    @staticmethod
    def get_player_info_by_nickname(nickname: str) -> tuple:
        """Retrieve player info based on nickname and return it as a dictionary."""
        
        cursor = Database()._instance.cursor
        try:
            cursor.execute("SELECT * FROM players WHERE nickname = ?", (nickname,))
            player = cursor.fetchone()
            
            if player is None:
                return False, "Player not found."
            
            column_names = [description[0] for description in cursor.description]
            player_info = {column_names[i]: player[i] for i in range(len(column_names))}
            return True, player_info
        except sql.Error as e:
            return False, f"Database error: {e}"

    
    @staticmethod
    def edit_player_info_by_tg_uid(tg_uid: int, update_data: dict) -> tuple:
        """Edit player information in the database based on tg_uid and return (bool, str)."""
        
        cursor = Database()._instance.cursor
        try:
            # Check if the player exists
            cursor.execute("SELECT COUNT(*) FROM players WHERE tg_uid = ?", (tg_uid,))
            if cursor.fetchone()[0] == 0:
                return False, "Player not found."

            # Prepare the SQL UPDATE statement
            set_clause = ", ".join(f"{key} = ?" for key in update_data.keys())
            values = list(update_data.values())
            
            # Execute the update query
            cursor.execute(f"UPDATE players SET {set_clause} WHERE tg_uid = ?", (*values, tg_uid))
            Database()._instance.connection.commit()
            return True, ""
        except sql.Error as e:
            return False, f"Database error: {e}"

    
    @staticmethod
    def edit_player_info_by_nickname(nickname: str, update_data: dict) -> tuple:
        """Edit player information in the database based on nickname and return (bool, str)."""
        
        cursor = Database()._instance.cursor
        try:
            # Check if the player exists based on nickname
            cursor.execute("SELECT COUNT(*) FROM players WHERE nickname = ?", (nickname,))
            if cursor.fetchone()[0] == 0:
                return False, "Player not found."

            # Prepare the SQL UPDATE statement
            set_clause = ", ".join(f"{key} = ?" for key in update_data.keys())
            values = list(update_data.values())
            
            # Execute the update query
            cursor.execute(f"UPDATE players SET {set_clause} WHERE nickname = ?", (*values, nickname))
            Database()._instance.connection.commit()
            return True, ""
        except sql.Error as e:
            return False, f"Database error: {e}"

        
    @staticmethod
    def player_is_registered(tg_uid: int) -> tuple:
        """Check if a player exists in the database based on tg_uid and return (bool, str)."""
        
        cursor = Database()._instance.cursor
        try:
            cursor.execute("SELECT COUNT(*) FROM players WHERE tg_uid = ?", (tg_uid,))
            is_registered = cursor.fetchone()[0] > 0
            return True, str(is_registered)  # Returning the result as a string
        except sql.Error as e:
            return False, f"Database error: {e}"

    
    @staticmethod
    def player_is_banned(tg_uid: int) -> tuple:
        """Check if a player has ever been banned based on tg_uid and return (bool, str)."""
        
        cursor = Database()._instance.cursor
        try:
            cursor.execute("SELECT COUNT(*) FROM banned_users WHERE tg_uid = ?", (tg_uid,))
            is_banned = cursor.fetchone()[0] > 0
            return True, str(is_banned)  # Returning the result as a string
        except sql.Error as e:
            return False, f"Database error: {e}"


    @staticmethod
    def ban_user(tg_uid: int, reason: str) -> tuple:
        """Ban a user by inserting their tg_uid into the banned_users table and return (bool, str)."""
        
        cursor = Database()._instance.cursor
        try:
            cursor.execute("""
                INSERT INTO banned_users (tg_uid, reason) 
                VALUES (?, ?)
            """, (tg_uid, reason))
            Database()._instance.connection.commit()
            return True, ""
        except sql.IntegrityError as e:
            return False, f"Database integrity error: {e}"
        except sql.Error as e:
            return False, f"Database error: {e}"


    @staticmethod
    def get_banned_users() -> tuple:
        """Retrieve a list of all tg_uid values from the banned_users table and return (bool, list/str)."""
        
        cursor = Database()._instance.cursor
        try:
            cursor.execute("SELECT tg_uid FROM banned_users")
            banned_users = [f"{row[0]}" for row in cursor.fetchall()]
            return True, banned_users
        except sql.Error as e:
            return False, f"Database error: {e}"


    @staticmethod
    def get_similar_players(search_string: str) -> tuple:
        """Retrieve a list of players whose combined first name, last name, and nickname is similar to the input string.
        
        Args:
            search_string (str): The string to search for in the concatenated player name fields.
            
        Returns:
            tuple: (bool, list/str) where list contains player information or str contains an error message.
        """
        
        cursor = Database()._instance.cursor
        try:
            # Create a search pattern for the LIKE query
            search_pattern = f"%{search_string}%"
            
            # Query to select players where the concatenation of first_name, last_name, and nickname is similar to the search string
            query = """
                SELECT * FROM players
                WHERE LOWER(first_name || ' ' || last_name || ' ' || nickname) LIKE LOWER(?)
            """
            
            cursor.execute(query, (search_pattern,))
            players = cursor.fetchall()
            
            # Get column names to map the result rows into dictionaries
            column_names = [description[0] for description in cursor.description]
            
            similar_players = [
                {column_names[i]: row[i] for i in range(len(column_names))} 
                for row in players
            ]
            
            return True, similar_players
        except sql.Error as e:
            return False, f"Database error: {e}"
    

    @staticmethod
    def get_admins_tg_uid() -> tuple:
        """Retrieve a list of tg_uid values of players with admin rights and return (bool, list/str)."""
        
        cursor = Database()._instance.cursor
        try:
            cursor.execute("SELECT tg_uid FROM players WHERE admin = 1")
            admin_tg_uids = [row[0] for row in cursor.fetchall()]
            return True, admin_tg_uids
        except sql.Error as e:
            return False, f"Database error: {e}"
        
    
    @staticmethod
    def get_all_players() -> Tuple[bool, List[Dict[str, any]]]:
        """
        Retrieve all players with their nickname, total games, and Elo score.

        Returns:
            Tuple[bool, List[Dict[str, any]]]: A tuple with a success flag and a list of player data.
        """
        cursor = Database()._instance.cursor
        try:
            # Query to retrieve all players ordered by Elo
            cursor.execute("""
                SELECT nickname, num_games, elo
                FROM players
                ORDER BY elo DESC
            """)
            players = cursor.fetchall()

            # Prepare player data as a list of dictionaries
            players_data = [{"nickname": nickname, "games": num_games, "elo": elo} for nickname, num_games, elo in players]

            return True, players_data

        except sql.Error as e:
            return False, f"Database error: {e}"