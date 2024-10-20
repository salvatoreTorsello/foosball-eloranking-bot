import os
import json

API_TOKEN = os.getenv('API_TOKEN')
BOT_PASSWORD = os.getenv('BOT_PASSWORD')
ROOTADMIN_INFO = os.getenv('ROOTADMIN_INFO')
DB_PATH = os.getenv('DB_PATH')

class BotConfig:
    """Bot configuration class"""
    
    # Parse the JSON string into a dictionary, then set key if and datre
    def __init__(self, welcome_message: str, menu_message: str,
                 ban_message: str) -> None:
        rootadmin_data = json.loads(ROOTADMIN_INFO)
        self.password = BOT_PASSWORD
        self.rootadmin_id = rootadmin_data['tg_uid']
        self.welcome_message = welcome_message
        self.menu_message = menu_message
        self.ban_message = ban_message