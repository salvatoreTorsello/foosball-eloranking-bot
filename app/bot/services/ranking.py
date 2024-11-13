from typing import List, Dict
import os

# File path for the generated HTML
RANKING_HTML_FILE = "ranking.html"

def generate_html_structure(rows: str) -> str:
    """Generate the complete HTML structure with a table and JavaScript for sortable columns."""
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
            th {{ background-color: #4CAF50; color: white; cursor: pointer; }}
        </style>
        <script>
            function sortTable(n) {{
                const table = document.getElementById("rankingTable");
                let rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                switching = true;
                dir = "asc"; 
                
                while (switching) {{
                    switching = false;
                    rows = table.rows;
                    
                    for (i = 1; i < (rows.length - 1); i++) {{
                        shouldSwitch = false;
                        x = rows[i].getElementsByTagName("TD")[n];
                        y = rows[i + 1].getElementsByTagName("TD")[n];
                        
                        const xContent = x.innerHTML.toLowerCase();
                        const yContent = y.innerHTML.toLowerCase();

                        const xValue = isNaN(xContent) ? xContent : parseInt(xContent);
                        const yValue = isNaN(yContent) ? yContent : parseInt(yContent);
                        
                        if (dir == "asc") {{
                            if (xValue > yValue) {{
                                shouldSwitch = true;
                                break;
                            }}
                        }} else if (dir == "desc") {{
                            if (xValue < yValue) {{
                                shouldSwitch = true;
                                break;
                            }}
                        }}
                    }}
                    
                    if (shouldSwitch) {{
                        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                        switching = true;
                        switchcount++; 
                    }} else {{
                        if (switchcount == 0 && dir == "asc") {{
                            dir = "desc";
                            switching = true;
                        }}
                    }}
                }}
            }}
        </script>
    </head>
    <body>
        <h1>Foosball Elo Ranking</h1>
        <table id="rankingTable">
            <tr>
                <th onclick="sortTable(0)">Position</th>
                <th onclick="sortTable(1)">Nickname</th>
                <th onclick="sortTable(2)">Games</th>
                <th onclick="sortTable(3)">Elo</th>
            </tr>
            {rows}
        </table>
    </body>
    </html>
    """


def generate_player_row(position: int, player: Dict[str, any]) -> str:
    """Generate an HTML row for a player with position."""
    return f"""
    <tr>
        <td>{position}</td>
        <td>{player['nickname']}</td>
        <td>{player['games']}</td>
        <td>{player['elo']}</td>
    </tr>
    """

def generate_ranking_html(players_data: List[Dict[str, any]]) -> str:
    """Generate and save the HTML file for player ranking."""
    # Sort players by Elo in descending order to calculate positions
    sorted_players = sorted(players_data, key=lambda p: p['elo'], reverse=True)
    
    # Add position to each player's dictionary
    for pos, player in enumerate(sorted_players, start=1):
        player['position'] = pos  # Add position as an integer

    # Generate rows using the updated sorted_players list with position
    rows = "".join(generate_player_row(player['position'], player) for player in sorted_players)
    html_content = generate_html_structure(rows)
    
    # Save HTML content to file
    with open(RANKING_HTML_FILE, "w", encoding="utf-8") as file:
        file.write(html_content)
        
    return RANKING_HTML_FILE
