import os
import argparse
from typing import Tuple
import pandas as pd
import json
from datetime import datetime
from bot.services.db import Database

ROOTADMIN_INFO = os.getenv('ROOTADMIN_INFO')
rootadmin_data = json.loads(ROOTADMIN_INFO)

def load_players_from_excel(file_path: str) -> Tuple[bool, str]:
    """Load players from an Excel file."""
    
    try:
        data = pd.read_excel(file_path, sheet_name='players')
        for _, row in data.iterrows():
            player_data = {
                'first_name': row['first_name'],
                'last_name': row['last_name'],
                'admin': row['admin'],
                'nickname': row['nickname'],
                # 'tg_uid': row.get('tg_uid'),
                # 'elo': row.get('elo', 1000),
                # 'num_games': row.get('num_games', 0),
            }
            success, message = Database.insert_player(player_data)
            if not success:
                return False, f"Failed to insert player {player_data['nickname']}: {message}"
        return True, "All players loaded successfully."
    except Exception as e:
        return False, f"Error loading players from Excel: {e}"

def load_games_from_excel(file_path: str) -> Tuple[bool, str]:
    """Load games from an Excel file."""
    
    try:
        data = pd.read_excel(file_path, sheet_name='games')
        for _, row in data.iterrows():
            game_data = {
                'team1': json.loads(row['team1']) if isinstance(row['team1'], str) else row['team1'],
                'team2': json.loads(row['team2']) if isinstance(row['team2'], str) else row['team2'],
                'scores': json.loads(row['scores']) if isinstance(row['scores'], str) else row['scores'],
                'date': row['date'] if 'date' in row else datetime.now().isoformat(),
            }
            success, message = Database.insert_pending_game(game_data)
            if not success:
                return False, f"Failed to insert game on {game_data['date']}: {message}"
        return True, "All games loaded successfully."
    except Exception as e:
        return False, f"Error loading games from Excel: {e}"


def approve_all_pending_games() -> Tuple[bool, str]:
    """Approve all pending games by confirming each one."""
    success, pending_games = Database.get_pending_games()
    if not success:
        return False, "Error retrieving pending games."

    for game in pending_games:
        game_id = game['id']
        confirm_admin_id = game.get('confirm_admin_id', rootadmin_data['tg_uid'])
        success, message = Database.confirm_pending_game(game_id, confirm_admin_id)
        if not success:
            return False, f"Failed to confirm game with ID {game_id}: {message}"

    return True, "All pending games approved successfully."


def main():
    parser = argparse.ArgumentParser(description="Load data into players or games table from an Excel file, or approve all pending games.")
    parser.add_argument('--load', choices=['players', 'games'], help="Specify which table to load: 'players' or 'games'")
    parser.add_argument('-f', '--file', type=str, help="Path to the Excel file containing data")
    parser.add_argument('--approve', action='store_true', help="Approve all pending games")

    args = parser.parse_args()
    
    # Initialize the database
    db = Database()
    db.initialize()

    # Load data based on the specified table
    if args.load == 'players' and args.file:
        success, message = load_players_from_excel(args.file)
        print(message)
        if not success:
            exit(1)  # Indicate failure

    elif args.load == 'games':
        if args.file:
            success, message = load_games_from_excel(args.file)
            print(message)
            if not success:
                exit(1)  # Indicate failure

        if args.approve:
            success, message = approve_all_pending_games()
            print(message)
            if not success:
                exit(1)  # Indicate failure

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
