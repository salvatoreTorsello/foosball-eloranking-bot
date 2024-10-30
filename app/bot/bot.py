import os, time
from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.config import BotConfig, API_TOKEN
from bot.handlers.admin import admin_router
from bot.handlers.user import user_router
from bot.services.admins import user_check_admin
from bot.services import keyboard as kbrd
from bot.services import cmd
from bot.services import utils
from bot.services.db import Database

from logger import logger  # Import the logger from logger.py

bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode='HTML')
)

dp = Dispatcher()
login_messages = []


def register_routers(dp: Dispatcher) -> None:
    """Register routers"""
    dp.include_router(user_router)
    dp.include_router(admin_router)
    logger.info("Routers registered successfully.")  # Log router registration


def bot_cfg() -> Dispatcher:
    cfg = BotConfig(
        welcome_message="Welcome to the Foosball Elo Ranking Bot! A bot that " \
            "manages and ranks foosball leagues using the Elo rating system.\n",
        menu_message="Foosball Elo Ranking Bot\n",
        ban_message="\n🚨 Your password attempts have been exhausted, and you have " \
                "been banned from accessing this service.\nPlease contact the " \
                "administrator for further assistance."
    )
    dp['cfg'] = cfg
    register_routers(dp)
    logger.info("Bot configuration set up.")  # Log bot configuration setup
    return dp


def main_menu_get_opts(uid: int, cfg: BotConfig) -> list:
    isadmin, isadmin_str = user_check_admin(uid, cfg)
    opts = cmd.mainMenu_opts
    if not isadmin:
        opts = opts[1:]
    return opts


@dp.message(CommandStart())
async def cmd_start(msg: Message, cfg: BotConfig, state: FSMContext) -> None:
    """Process the `start` command"""

    login_messages.append(msg.message_id)
    db = Database()

    logger.info(f"User {msg.from_user.id} initiated start command.")

    # Check if user is banned
    success, is_banned = db.player_is_banned(msg.from_user.id)
    if not success:
        logger.error(f"Database error while checking if user {msg.from_user.id} is banned: {is_banned}")
        await msg.answer("An error occurred. Please try again later.")
        return

    if utils.str_to_bool(is_banned):
        await msg.answer(cfg.ban_message, reply_markup=None)
        logger.warning(f"User {msg.from_user.id} is banned.")  # Log warning if user is banned
        return

    # Check if user is registered
    success, is_registered = db.player_is_registered(msg.from_user.id)
    if not success:
        logger.error(f"Database error while checking if user {msg.from_user.id} is registered: {is_registered}")
        await msg.answer("An error occurred. Please try again later.")
        return

    if not is_registered:
        await state.set_state(cmd.Welcome.password)
        await state.update_data(password=str(0))
        text = "Insert password to proceed (3 attempts left)"
        await msg.answer(text, reply_markup=None)
        logger.info(f"User {msg.from_user.id} not registered, password requested.")  # Log unregistered user
    else:
        # Fetch player info
        success, player_info = db.get_player_info_by_tg_uid(msg.from_user.id)
        if not success:
            logger.error(f"Failed to retrieve player info for user {msg.from_user.id}: {player_info}")
            await msg.answer("An error occurred. Please try again later.")
            return

        text = f"Hello, {player_info['nickname']}\n"
        opts = main_menu_get_opts(msg.from_user.id, cfg)
        keyboard = kbrd.create_inline_2c(opts)
        await msg.answer(text, reply_markup=keyboard)
        logger.info(f"User {msg.from_user.id} successfully logged in.")  # Log successful login


@dp.message(cmd.Welcome.password)
async def cmd_start_passwd(msg: Message, cfg: BotConfig, state: FSMContext) -> None:
    """Process password input during login"""

    login_messages.append(msg.message_id)
    db = Database()
    passwd = msg.text
    data = await state.get_data()
    data['password'] = str(int(data['password']) + 1)
    await state.update_data(password=data['password'])
    
    # Compare password
    if passwd == cfg.password:
        text = "Access granted!"
        await msg.answer(text, reply_markup=None)
        
        # Delete login messages after granting access
        time.sleep(2)
        for id in login_messages:
            await bot.delete_message(chat_id=msg.chat.id, message_id=id)
        login_messages.clear()
        
        await state.set_state(cmd.Welcome.search)
        text = "Hello, first time here?\n"
        text += f"\n➜ Insert your first name and last name, or your nickname"
        await msg.answer(text, reply_markup=None)
        logger.info(f"User {msg.from_user.id} granted access.")  # Log access grant

    else:
        if data['password'] > '3':
            text = cfg.ban_message
            success, error = db.ban_user(msg.from_user.id, "Excessive password attempts.")
            if not success:
                logger.error(f"Failed to ban user {msg.from_user.id}: {error}")
                await msg.answer("An error occurred while banning. Please try again later.")
                return
            logger.warning(f"User {msg.from_user.id} banned for too many password attempts.")  # Log ban
        else:
            text = "Access denied!\n"
            text += f"\n➜ Insert password again ({3 - int(data['password'])} attempts left)"
        await msg.answer(text, reply_markup=None)
        logger.info(f"User {msg.from_user.id} failed password attempt.")  # Log failed attempt


@dp.message(cmd.Welcome.search)
async def cmd_start_search_player(msg: Message, cfg: BotConfig, state: FSMContext) -> None:
    """Process player search based on input"""
    
    db = Database()
    await state.clear()
    text = "👤 Select your nickname from the list below. If not present, contact administrator."
    
    # Get similar players
    success, similar_players = db.get_similar_players(msg.text)
    if not success:
        logger.error(f"Failed to retrieve similar players for search term {msg.text}: {similar_players}")
        await msg.answer("An error occurred while searching. Please try again later.")
        return

    similar_players_nick = [(p['nickname'], f"search_player_{p['nickname']}") for p in similar_players]
    keyboard = kbrd.create_inline_2c(similar_players_nick)
    await msg.answer(text, reply_markup=keyboard)
    
    logger.info(f"User {msg.from_user.id} is searching for a player.")  # Log search operation


@dp.callback_query(F.data.startswith('search_player_'))
async def cmd_start_select_nickname(cb_query: CallbackQuery, cfg: BotConfig) -> None:
    """Process player selection based on callback query"""
    
    db = Database()
    nickname = cb_query.data[14:]
    
    # Get player info by nickname
    success, player_info = db.get_player_info_by_nickname(nickname)
    if not success:
        logger.error(f"Failed to retrieve player info for nickname {nickname}: {player_info}")
        await cb_query.message.answer("An error occurred. Please try again later.")
        return

    player_info['tg_uid'] = cb_query.from_user.id
    
    # Update player info
    success, error = db.edit_player_info_by_nickname(nickname, player_info)
    if not success:
        logger.error(f"Failed to update player info for nickname {nickname}: {error}")
        await cb_query.message.answer("An error occurred. Please try again later.")
        return

    text = f"Hello, {player_info['nickname']}\n"
    opts = main_menu_get_opts(cb_query.from_user.id, cfg)
    keyboard = kbrd.create_inline_2c(opts)
    await cb_query.message.edit_text(text, reply_markup=keyboard)
    
    logger.info(f"User {cb_query.from_user.id} selected nickname {nickname}.")  # Log nickname selection


@dp.callback_query(F.data == 'menu_main')
async def cmd_main(cb_query: CallbackQuery, cfg: BotConfig) -> None:
    """Process the main menu selection"""
    
    db = Database()
    
    # Get player info by tg_uid
    success, player_info = db.get_player_info_by_tg_uid(cb_query.from_user.id)
    if not success:
        logger.error(f"Failed to retrieve player info for user {cb_query.from_user.id}: {player_info}")
        await cb_query.message.answer("An error occurred. Please try again later.")
        return

    text = f"Hello, {player_info['nickname']}\n"
    opts = main_menu_get_opts(cb_query.from_user.id, cfg)
    keyboard = kbrd.create_inline_2c(opts)
    await cb_query.message.edit_text(text, reply_markup=keyboard)
    
    logger.info(f"User {cb_query.from_user.id} accessed the main menu.")  # Log main menu access
