import json
import sys
import logging
import asyncio

from logger import logger

from bot.bot import bot, bot_cfg
from bot.config import ROOTADMIN_INFO

from bot.services.db import Database

async def main() -> None:
    """Main function which will execute out
    event loop and start polling.
    """
    try:
        # Initialize the database
        db = Database()
        success, result = db.initialize()
        if not success:
            logger.error(f"Failed to initialize the database: {result}")
            return
        
        # Create tables in the database
        success, result = db.create_tables()
        if not success:
            logger.error(f"Failed to create tables: {result}")
            return
        logger.info("Database tables created successfully.")
        
        # Check if rootadmin already exists
        rootadmin_info = json.loads(ROOTADMIN_INFO)
        nickname = rootadmin_info['nickname']
        success, player_info = db.get_player_info_by_nickname(nickname)
        
        if not success:
            if "not found" in player_info.lower():  # Assuming the function returns a specific error message
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
