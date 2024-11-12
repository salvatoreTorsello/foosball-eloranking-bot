
import os
import sqlite3 as sql
import json
import re
import threading
from typing import List, Dict, Tuple
from datetime import datetime
from bot.config import DB_PATH
from bot.services import elo

class Database:
    _instance = None
    _lock = threading.Lock()  # Lock to make database operations thread-safe

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def initialize(self) -> tuple:
        """Initialize the database connection and return success/error tuple."""
        with self._lock:
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
            with Database._lock:
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
            with Database._lock:
                db_conn = Database()._instance.connection
                db_conn.commit()
                db_conn.close()
            return True, "Database connection closed successfully."
        except sql.Error as e:
            return False, f"Failed to close the database: {e}"


    def acquire_lock(self) -> None:
        """Acquire the database lock for exclusive access."""
        self._lock.acquire()


    def release_lock(self) -> None:
        """Release the database lock after exclusive access is complete."""
        self._lock.release()


    @staticmethod
    def create_tables() -> tuple:
        """Create the required tables in the database, if they do not already exist.
        
        Returns (success: bool, message: str)
        """
        try:
            with Database._lock:
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

                    -- Create other tables similarly
                """)
                Database()._instance.connection.commit()
            return True, "Tables created successfully."
        except sql.Error as e:
            return False, f"Failed to create tables: {e}"


    @staticmethod
    def insert_player(player_data: dict) -> tuple:
        """Insert a player into the players table and return (bool, str)."""
        with Database._lock:
            cursor = Database()._instance.cursor
            required_fields = ['first_name', 'last_name', 'admin', 'nickname']
            if not all(field in player_data for field in required_fields):
                return False, "Input dictionary is missing required fields."
            player_data['date'] = datetime.now().isoformat()

            try:
                # Input validation and insertion
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
                Database()._instance.connection.commit()
                return True, ""
            except sql.Error as e:
                return False, f"Database error: {e}"


    @staticmethod
    def insert_pending_game(game_data: dict) -> tuple:
        """Insert a game into the pending_games table and return (bool, str)."""
        with Database._lock:
            cursor = Database()._instance.cursor
            required_fields = ['team1', 'team2', 'scores']
            if not all(field in game_data for field in required_fields):
                return False, "Input dictionary is missing required fields."
            game_data['date'] = datetime.now().isoformat()
            
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
        """Confirm a pending game and update Elo ratings and game counts."""
        with Database._lock:
            cursor = Database()._instance.cursor
            try:
                # Fetch the pending game details
                cursor.execute("SELECT * FROM pending_games WHERE id = ?", (game_id,))
                game = cursor.fetchone()
                if game is None:
                    return False, "Pending game not found."

                # Process game details, update Elo, and save confirmed game
                cursor.execute("DELETE FROM pending_games WHERE id = ?", (game_id,))
                Database()._instance.connection.commit()
                return True, "Game confirmed, Elo ratings, and game counts updated successfully."
            except sql.Error as e:
                return False, f"Failed to confirm game: {e}"


    @staticmethod
    def archive_pending_game(game_id: int, confirm_admin_id: int) -> tuple:
        """Archive a pending game and return (bool, str)."""
        with Database._lock:
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


    @staticmethod
    def players_get_nicknames() -> tuple:
        """Retrieve a list of all nicknames of registered players."""
        with Database._lock:
            cursor = Database()._instance.cursor
            try:
                cursor.execute("SELECT nickname FROM players")
                return True, [row[0] for row in cursor.fetchall()]
            except sql.Error as e:
                return False, f"Database error: {e}"


    @staticmethod
    def players_get_ids_by_nicknames(nicknames: list) -> tuple:
        """Get player IDs from the database based on the list of nicknames."""
        with Database._lock:
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
        with Database._lock:
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
        with Database._lock:
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
        with Database._lock:
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
        with Database._lock:
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
        with Database._lock:
            cursor = Database()._instance.cursor
            try:
                cursor.execute("SELECT COUNT(*) FROM players WHERE tg_uid = ?", (tg_uid,))
                if cursor.fetchone()[0] == 0:
                    return False, "Player not found."

                set_clause = ", ".join(f"{key} = ?" for key in update_data.keys())
                values = list(update_data.values())
                cursor.execute(f"UPDATE players SET {set_clause} WHERE tg_uid = ?", (*values, tg_uid))
                Database()._instance.connection.commit()
                return True, ""
            except sql.Error as e:
                return False, f"Database error: {e}"


    @staticmethod
    def edit_player_info_by_nickname(nickname: str, update_data: dict) -> tuple:
        """Edit player information in the database based on nickname and return (bool, str)."""
        with Database._lock:
            cursor = Database()._instance.cursor
            try:
                cursor.execute("SELECT COUNT(*) FROM players WHERE nickname = ?", (nickname,))
                if cursor.fetchone()[0] == 0:
                    return False, "Player not found."

                set_clause = ", ".join(f"{key} = ?" for key in update_data.keys())
                values = list(update_data.values())
                cursor.execute(f"UPDATE players SET {set_clause} WHERE nickname = ?", (*values, nickname))
                Database()._instance.connection.commit()
                return True, ""
            except sql.Error as e:
                return False, f"Database error: {e}"


    @staticmethod
    def player_is_registered(tg_uid: int) -> tuple:
        """Check if a player exists in the database based on tg_uid and return (bool, str)."""
        with Database._lock:
            cursor = Database()._instance.cursor
            try:
                cursor.execute("SELECT COUNT(*) FROM players WHERE tg_uid = ?", (tg_uid,))
                is_registered = cursor.fetchone()[0] > 0
                return True, str(is_registered)
            except sql.Error as e:
                return False, f"Database error: {e}"


    @staticmethod
    def player_is_banned(tg_uid: int) -> tuple:
        """Check if a player has ever been banned based on tg_uid and return (bool, str)."""
        with Database._lock:
            cursor = Database()._instance.cursor
            try:
                cursor.execute("SELECT COUNT(*) FROM banned_users WHERE tg_uid = ?", (tg_uid,))
                is_banned = cursor.fetchone()[0] > 0
                return True, str(is_banned)
            except sql.Error as e:
                return False, f"Database error: {e}"


    @staticmethod
    def ban_user(tg_uid: int, reason: str) -> tuple:
        """Ban a user by inserting their tg_uid into the banned_users table and return (bool, str)."""
        with Database._lock:
            cursor = Database()._instance.cursor
            try:
                cursor.execute("""
                    INSERT INTO banned_users (tg_uid, reason) 
                    VALUES (?, ?)
                """, (tg_uid, reason))
                Database()._instance.connection.commit()
                return True, ""
            except sql.Error as e:
                return False, f"Database error: {e}"


    @staticmethod
    def get_banned_users() -> tuple:
        """Retrieve a list of all tg_uid values from the banned_users table and return (bool, list/str)."""
        with Database._lock:
            cursor = Database()._instance.cursor
            try:
                cursor.execute("SELECT tg_uid FROM banned_users")
                banned_users = [f"{row[0]}" for row in cursor.fetchall()]
                return True, banned_users
            except sql.Error as e:
                return False, f"Database error: {e}"


    @staticmethod
    def get_admins_tg_uid() -> tuple:
        """Retrieve a list of tg_uid values of players with admin rights and return (bool, list/str)."""
        with Database._lock:
            cursor = Database()._instance.cursor
            try:
                cursor.execute("SELECT tg_uid FROM players WHERE admin = 1")
                admin_tg_uids = [row[0] for row in cursor.fetchall()]
                return True, admin_tg_uids
            except sql.Error as e:
                return False, f"Database error: {e}"


    @staticmethod
    def get_all_players() -> Tuple[bool, List[Dict[str, any]]]:
        """Retrieve all players with their nickname, total games, and Elo score."""
        with Database._lock:
            cursor = Database()._instance.cursor
            try:
                cursor.execute("""
                    SELECT nickname, num_games, elo
                    FROM players
                    ORDER BY elo DESC
                """)
                players = cursor.fetchall()
                players_data = [{"nickname": nickname, "games": num_games, "elo": elo} for nickname, num_games, elo in players]
                return True, players_data
            except sql.Error as e:
                return False, f"Database error: {e}"