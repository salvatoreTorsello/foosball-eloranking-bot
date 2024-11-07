import json
import sys, os
import logging
import asyncio

from logger import logger

from bot.bot import bot, bot_cfg
from bot.config import ROOTADMIN_INFO, DB_PATH

from bot.services.db import Database
from bot.services import backup as bak

async def main() -> None:
    """Main function which will execute out
    event loop and start polling.
    """
    try:
        db_exists = False
        if os.path.exists(DB_PATH) and os.path.isfile(DB_PATH):
            logger.info("Database file already exists")
            success, result = bak.upload()
            logger.info(f"Backing up db file: {result}") 
            db_exists = True
        else:
            success, result = bak.download_latest()
            if not success:
                logger.info(f"Downloading backup file: {result}")
                logger.info(f"Creating empty file")
                os.open(DB_PATH, os.O_CREAT)
            else:
                logger.info(f"Backup file retrived: {result}")
                db_exists = True

        # Initialize the database conncetion
        db = Database()
        success, result = db.initialize()
        if not success:
            logger.error(f"Failed to initialize the database: {result}")
            return
        
        # Create tables in the database
        if not db_exists:
            success, result = db.create_tables()
            if not success:
                logger.error(f"Failed to create tables: {result}")
                return
            logger.info("Database tables created successfully.")           
        
            # Check if rootadmin already exists
            rootadmin_info = json.loads(ROOTADMIN_INFO)
            nickname = rootadmin_info['nickname']
            success, player_info = db.get_player_info_by_nickname(nickname)
            logger.info(f"Rootadmin {nickname} search: {player_info}")

            if not success:
                if "not found" in player_info.lower():  
                    # Insert rootadmin into the database only if they don't exist
                    success, result = db.insert_player(rootadmin_info)
                    if not success:
                        logger.error(f"Failed to insert rootadmin: {result}")
                        return
                    logger.info("Rootadmin inserted successfully.")
                    
                    # Update the tg_uid of the newly inserted rootadmin
                    success, player_info = db.get_player_info_by_nickname(nickname)
                    if success:
                        player_info['tg_uid'] = rootadmin_info.get('tg_uid', None)  # Use the provided tg_uid from ROOTADMIN_INFO
                        success, result = db.edit_player_info_by_nickname(nickname, player_info)
                        if not success:
                            logger.error(f"Failed to update tg_uid for rootadmin: {result}")
                            return
                        logger.info("Rootadmin tg_uid updated successfully.")
                    else:
                        logger.error(f"Failed to retrieve rootadmin info by nickname '{nickname}' after insertion: {player_info}")
                else:
                    logger.error(f"Error retrieving rootadmin info: {player_info}")
                    return
            else:
                logger.info("Rootadmin already exists in the database, skipping insertion.")
                
            success, result = bak.upload()
            logger.info(f"Uploading backup file: {result}") 
            db_exists = True
        
        # Start bot polling
        bot_dp = bot_cfg()
        await bot_dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("Program interrupted.")
        
    finally:
        # Close the database
        success, result = db.close_db()
        if not success:
            logger.error(f"Failed to close the database: {result}")
        else:
            logger.info(result)

if __name__ == "__main__":
    asyncio.run(main())
