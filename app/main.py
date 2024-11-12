import json
import sys, os
import logging
import asyncio
from threading import Thread, Event

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
        db_exists = True
        if os.path.exists(DB_PATH) and os.path.isfile(DB_PATH):
            logger.info("Database file already exists")
        else:
            success, result = bak.download_latest()
            logger.info(f"Downloading backup file: {result}")
            if not success:
                logger.info(f"Creating empty file")
                os.open(DB_PATH, os.O_CREAT)
                db_exists = False

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
            
            # Insert rootadmin into the database
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
            
        # Start the bakup thread
        th_stop = Event()
        t1 = Thread(target = bak.upload_th, args = (th_stop,))
        t1.start()
        
        # Start bot polling
        bot_dp = bot_cfg()
        await bot_dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("Program interrupted.")
        
    finally:
        # Stop backup thread
        logger.info("Send exit notification to backup thread")
        th_stop.set()
        t1.join()
        
        # Close the database
        success, result = db.close_db()
        if not success:
            logger.error(f"Failed to close the database: {result}")
        else:
            logger.info(result)

if __name__ == "__main__":
    asyncio.run(main())
