import json
import sys
import logging
import asyncio

from bot.bot import bot, bot_cfg
from bot.config import ROOTADMIN_INFO

from bot.services.db import Database


# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Main function which will execute out
    event loop and start polling.
    """
    try:
        # Initialize the database and create tables
        db = Database()
        db.create_tables()
        # Insert rootadmin in the database
        rootadmin_info = json.loads(ROOTADMIN_INFO)
        db.insert_player(rootadmin_info)
        
        bot_dp = bot_cfg()
        await bot_dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("Program interrupted.")
        
    finally:
    # Close database
        db.close_db()
    
if __name__ == "__main__":
    asyncio.run(main())