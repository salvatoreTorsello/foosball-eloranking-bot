import os
import json

API_TOKEN = os.getenv('API_TOKEN')
ROOTADMIN_INFO = os.getenv('ROOTADMIN_INFO')
DB_PATH = os.getenv('DB_PATH')

class BotConfig:
    """Bot configuration class"""
    
    # Parse the JSON string into a dictionary, then set key if and datre
    def __init__(self, admin_ids: list, welcome_message: str) -> None:
        rootadmin_data = json.loads(ROOTADMIN_INFO)
        self.rootadmin_id = rootadmin_data['tg_uid']
        self.admin_ids = admin_ids+[rootadmin_data['tg_uid']]
        self.welcome_message = welcome_message