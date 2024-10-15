import sys
import logging
import asyncio

from bot.bot import bot, bot_cfg

import bot.services.db as db


# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Main function which will execute out
    event loop and start polling.
    """
    
    # Connect to the database and create tables
    db_conn = db.connect_db()
    db_cursor = db_conn.cursor()
    db.create_tables(db_cursor)
    db.insert_rootadmin(db_cursor)
    
    bot_dp = bot_cfg()
    await bot_dp.start_polling(bot)
    db.close_db(db_conn)
    
if __name__ == "__main__":
    asyncio.run(main())