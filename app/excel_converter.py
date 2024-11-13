import pandas as pd
import json

# Load the new players data and games dump data
players_path = "players.xlsx"
games_dump_path = "games_dump.xlsx"

players_df = pd.read_excel(players_path)
games_df = pd.read_excel(games_dump_path)

# Rebuild the mapping dictionary to use the updated nicknames
players_df['full_name'] = players_df['first_name'] + " " + players_df['last_name']
name_to_nickname = dict(zip(players_df['full_name'], players_df['nickname']))

# Helper function for progressive matching with updated data
def get_nickname(player_full_name):
    # Split full name to get first name, last name, and optional nickname parts
    name_parts = player_full_name.split()
    first_name = name_parts[0]
    last_name = name_parts[-1]
    nickname = " ".join(name_parts[1:-1]) if len(name_parts) > 2 else ""

    # 1. Attempt to match with "first name + nickname + last name"
    full_pattern = f"{first_name} {nickname} {last_name}".strip()
    if full_pattern in name_to_nickname:
        return name_to_nickname[full_pattern]
    
    # 2. Attempt to match with "first name + last name"
    simple_full_name = f"{first_name} {last_name}".strip()
    if simple_full_name in name_to_nickname:
        return name_to_nickname[simple_full_name]
    
    # 3. Attempt to match with "nickname" only
    if nickname and nickname in name_to_nickname.values():
        for full_name, nick in name_to_nickname.items():
            if nick == nickname:
                return nick
    
    # 4. Attempt to match with "last name" only
    for full_name, nick in name_to_nickname.items():
        if full_name.endswith(last_name):
            return nick
    
    # 5. Attempt to match with "first name" only
    for full_name, nick in name_to_nickname.items():
        if full_name.startswith(first_name):
            return nick

    # If all attempts fail, return an unknown marker
    return f"unknown_{player_full_name}"

# Prepare the formatted games data based on the structured data
formatted_games = {
    'team1': [],
    'team2': [],
    'scores': [],
    'date': [],
    'confirm_admin_id': [],
    'confirm_date': []
}

# Track unknown players for reporting
unknown_players = set()

# Process each row in games_dump to apply enhanced matching logic
for _, row in games_df.iterrows():
    # Enhanced matching for team A players
    team1_players = [
        get_nickname(row['Squadra A Giocatore 1'].strip()),
        get_nickname(row['Squadra A Giocatore 2'].strip())
    ]
    # Enhanced matching for team B players
    team2_players = [
        get_nickname(row['Squadra B Giocatore 1'].strip()),
        get_nickname(row['Squadra B Giocatore 2'].strip())
    ]

    # Record any unmatched players
    for player in team1_players + team2_players:
        if player.startswith("unknown_"):
            unknown_players.add(player.replace("unknown_", "").strip())
    
    # Format scores as JSON-like data
    scores = json.dumps({"team1": row['Punteggio A'], "team2": row['Punteggio B']})
    
    # Populate formatted_games dictionary
    formatted_games['team1'].append(json.dumps({"players": team1_players}))
    formatted_games['team2'].append(json.dumps({"players": team2_players}))
    formatted_games['scores'].append(scores)
    formatted_games['date'].append(row['Data'])
    formatted_games['confirm_admin_id'].append(None)  # No confirm_admin_id available
    formatted_games['confirm_date'].append(None)  # No confirm_date available

# Convert to DataFrame for saving
formatted_games_df = pd.DataFrame(formatted_games)

# Save the reformatted data to a new Excel file
output_path = "formatted_games.xlsx"
formatted_games_df.to_excel(output_path, sheet_name='games', index=False)

# Display any unknown players
print("Unknown players:", list(unknown_players))
