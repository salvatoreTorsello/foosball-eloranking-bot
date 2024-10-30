from typing import List, Dict
import os

# File path for the generated HTML
RANKING_HTML_FILE = "ranking.html"

def generate_html_structure(rows: str) -> str:
    """Generate the complete HTML structure with a table."""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Foosball Elo Ranking</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; }}
            h1 {{ color: #333; }}
            table {{ margin: auto; border-collapse: collapse; width: 80%; }}
            th, td {{ padding: 12px; border: 1px solid #ddd; text-align: center; }}
            th {{ background-color: #4CAF50; color: white; }}
        </style>
    </head>
    <body>
        <h1>Foosball Elo Ranking</h1>
        <table>
            <tr>
                <th>Nickname</th>
                <th>Games</th>
                <th>Elo</th>
            </tr>
            {rows}
        </table>
    </body>
    </html>
    """

def generate_player_row(player: Dict[str, any]) -> str:
    """Generate an HTML row for a player."""
    return f"""
    <tr>
        <td>{player['nickname']}</td>
        <td>{player['games']}</td>
        <td>{player['elo']}</td>
    </tr>
    """

def generate_ranking_html(players_data: List[Dict[str, any]]) -> str:
    """Generate and save the HTML file for player ranking."""
    rows = "".join(generate_player_row(player) for player in players_data)
    html_content = generate_html_structure(rows)
    
    # Save HTML content to file
    with open(RANKING_HTML_FILE, "w", encoding="utf-8") as file:
        file.write(html_content)
        
    return RANKING_HTML_FILE
