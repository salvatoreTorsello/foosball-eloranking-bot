from aiogram.filters import Command
from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from bot.config import BotConfig
from bot.services.admins import users_check_admin
from bot.services import keyboard as kbrd
import bot.services.cmd as cmd

user_router = Router()

@user_router.message(Command('admin_info'))
async def cmd_admin_info(msg: types.Message, cfg: BotConfig) -> None:
    """Check wether as user is admin or not"""
    
    isadmin, isadmin_str = users_check_admin(msg.from_user.id, cfg)
    await msg.answer(isadmin_str)
    
@user_router.message(Command('dice'))
async def cmd_dice(msg: types.Message) -> None:
    """Answer dice to yur user dice command"""
    
    await msg.answer_dice(emoji="🎲")