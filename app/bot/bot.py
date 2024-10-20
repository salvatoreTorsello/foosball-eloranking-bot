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
from bot.services.db import Database

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
    
    
def bot_cfg() -> Dispatcher:
    
    cfg = BotConfig(
        welcome_message = "Welcome to the Foosball Elo Ranking Bot! A bot that " \
            "manages and ranks foosball leagues using the Elo rating system.\n",
        menu_message = "Foosball Elo Ranking Bot\n",
        ban_message="\n🚨 Your password attempts have been exhausted, and you have " \
                "been banned from accessing this service.\nPlease contact the " \
                "administrator for further assistance."
    )
    dp['cfg'] = cfg
  
    register_routers(dp)
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
    if db.player_is_banned(msg.from_user.id):
        text = cfg.ban_message
        await msg.answer(text, reply_markup=None)
    elif not db.player_is_registered(msg.from_user.id):
        await state.set_state(cmd.Welcome.password)
        await state.update_data(password=str(0))
        text = "Insert password to proceed (3 attemps left)"
        await msg.answer(text, reply_markup=None)
    else:
        player_info = db.get_player_info_by_tg_uid(msg.from_user.id)
        text = f"Hello, {player_info['nickname']}\n"
        opts = main_menu_get_opts(msg.from_user.id, cfg)
        keybaord = kbrd.create_inline_2c(opts)  
        await msg.answer(text, reply_markup=keybaord)


@dp.message(cmd.Welcome.password)
async def cmd_start_passwd(msg: Message, cfg: BotConfig, state: FSMContext) -> None:
    
    login_messages.append(msg.message_id)
    db = Database()
    passwd = msg.text
    data = await state.get_data()
    data['password'] = str(int(data['password'])+1)
    await state.update_data(password=data['password'])
    if passwd == cfg.password:
        text = "Access granted!"
        await msg.answer(text, reply_markup=None)
        
        time.sleep(2)
        for id in login_messages:
            await bot.delete_message(chat_id=msg.chat.id, message_id=id)
        login_messages.clear()
        
        await state.set_state(cmd.Welcome.search)        
        text = "Hello, first time here?\n"
        text += f"\n➜ Insert your first name and last name, or your nickname"
        await msg.answer(text, reply_markup=None)
        
    else:
        if data['password'] > '3':
            text = cfg.ban_message
            db.ban_user(msg.from_user.id, "Excessive password attempts.")
        else:
            text = "Access denied!\n"
            text += f"\n➜ Insert password again ({3-int(data['password'])} attemps left)"
        await msg.answer(text, reply_markup=None)
        
        
@dp.message(cmd.Welcome.search)
async def cmd_start_search_player(msg: Message, cfg: BotConfig, state: FSMContext) -> None:
    
    db = Database()
    await state.clear()
    text = "👤 Select your nickname from list below. If not present, contact administrator." 
    similar_players = db.get_similar_players(msg.text)
    similar_players_nick = [(p['nickname'], f"search_player_{p['nickname']}") for p in similar_players]
    keybaord = kbrd.create_inline_2c(similar_players_nick)
    await msg.answer(text, reply_markup=keybaord)
    

@dp.callback_query(F.data.startswith('search_player_'))
async def cmd_start_select_nickname(cb_query: CallbackQuery, cfg: BotConfig) -> None:
    
    db = Database()
    nickname = cb_query.data[14:]
    player_info = db.get_player_info_by_nickname(nickname)
    player_info['tg_uid'] = cb_query.from_user.id
    print(player_info)
    db.edit_player_info_by_nickname(nickname, player_info)        
    text = f"Hello, {player_info['nickname']}\n"
    opts = main_menu_get_opts(cb_query.from_user.id, cfg)
    keybaord = kbrd.create_inline_2c(opts)  
    await cb_query.message.edit_text(text, reply_markup=keybaord)
    
    
@dp.callback_query(F.data == 'menu_main')
async def cmd_main(cb_query: CallbackQuery, cfg: BotConfig) -> None:
    
    db = Database()
    player_info = db.get_player_info_by_tg_uid(cb_query.from_user.id)
    text = f"Hello, {player_info['nickname']}\n"
    opts = main_menu_get_opts(cb_query.from_user.id, cfg)
    keybaord = kbrd.create_inline_2c(opts)  
    await cb_query.message.edit_text(text, reply_markup=keybaord)