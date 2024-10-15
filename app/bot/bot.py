import os
from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.config import BotConfig, API_TOKEN

from bot.handlers.admin import admin_router
from bot.handlers.user import user_router

from bot.services.admins import users_check_admin
from bot.services import keyboard as kbrd
from bot.services import cmd

bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode='HTML')
)

dp = Dispatcher()


def register_routers(dp: Dispatcher) -> None:
    """Register routers"""
    
    dp.include_router(user_router)
    dp.include_router(admin_router)
    
    
def bot_cfg() -> Dispatcher:
    
    cfg = BotConfig(
        admin_ids=[],
        welcome_message='Welcome to Foosball Elo Ranking Bot!'
    )
    dp['cfg'] = cfg
  
    register_routers(dp)
    return dp


def main_menu_get_opts(uid: int, cfg: BotConfig) -> list:
    isadmin, isadmin_str = users_check_admin(uid, cfg)
    opts = cmd.mainMenu_opts
    if not isadmin:
        opts = opts[1:-1]
    return opts


@dp.message(CommandStart())
async def cmd_start(msg: Message, cfg: BotConfig) -> None:
    """Process the `start` command"""
    
    opts = main_menu_get_opts(msg.from_user.id, cfg)
        
    keybaord = kbrd.create_inline(opts)
    await msg.answer(cfg.welcome_message, reply_markup=keybaord)

    
@dp.callback_query(F.data == 'menu_main')
async def cmd_main(cb_query: CallbackQuery, cfg: BotConfig) -> None:
    
    keybaord = kbrd.create_inline(cmd.mainMenu_opts)
    await cb_query.message.edit_text(cfg.welcome_message, reply_markup=keybaord)