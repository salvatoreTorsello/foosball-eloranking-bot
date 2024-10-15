from typing import Any, Dict
from aiogram import F, Router, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.bot import BotConfig

from bot.services.admins import users_check_admin
from bot.services import cmd
from bot.services import keyboard as kbrd

import bot.services.db as db


admin_router = Router()

addplayer_title = f"👤 {html.quote("Player Registration")}\n\n"
addplayer_success = f"\n✅ {html.quote("Registration completed successfully!")}"
addplayer_canceled = f"\n❌ {html.quote("Registration canceled!")} "

@admin_router.callback_query(F.data == 'menu_admin')
async def cmd_admin(cb_query: CallbackQuery, cfg: BotConfig) -> None:
    
    if users_check_admin(cb_query.from_user.id, cfg):
        keybaord = kbrd.create_inline(cmd.adminMenu_opts)
        await cb_query.message.edit_text(f"Welcome admin, select an option:", reply_markup=keybaord)
    else:
        await cb_query.message.edit_text(f"⛔ You are not allowed to be here!", reply_markup=None)
        

@admin_router.callback_query(F.data == 'mng_players')
async def cmd_mng_admins(cb_query: CallbackQuery) -> None:
    
    keybaord = kbrd.create_inline(cmd.mngPlayersMenu_opts)
    await cb_query.message.edit_text(f"Player managemnt menu, select an option:", reply_markup=keybaord)
    

@admin_router.callback_query(F.data == 'add_player')
async def cmd_add_player(cb_query: CallbackQuery, state: FSMContext) -> None:
    
    await state.set_state(cmd.AddPlayer.firstname)
    text = addplayer_title
    text += "\n➜  Insert player first name"
    await cb_query.message.edit_text(text, reply_markup=None)
    
    
@admin_router.message(cmd.AddPlayer.firstname)
async def cmd_add_player_firstname(msg: Message, state: FSMContext) -> None:
    
    # TODO: Add here formal checks on player first name (same as db attribute)
    await state.update_data(firstname=msg.text)
    await state.set_state(cmd.AddPlayer.lastname)
    text = addplayer_title
    data = await state.get_data()
    text += f"- First name: {msg.text}\n"
    text += "\n➜  Insert player last name"
    await msg.answer(text, reply_markup=None)
    
    
@admin_router.message(cmd.AddPlayer.lastname)
async def cmd_add_player_lastname(msg: Message, state: FSMContext) -> None:
    
    # TODO: Add here formal checks on player last name (same as db attribute)
    await state.update_data(lastname=msg.text)
    await state.set_state(cmd.AddPlayer.nickname)
    text = addplayer_title
    data = await state.get_data()
    text += f"- First name: {data.get("firstname", "N/A")}\n"
    text += f"- Last name: {msg.text}\n"
    text += "\n➜  Insert player nickname"
    await msg.answer(text, reply_markup=None)
    

@admin_router.message(cmd.AddPlayer.nickname)
async def cmd_add_player_nickname(msg: Message, state: FSMContext) -> None:

    keyboard = kbrd.create_reply(cmd.yesno_rk_opts)
    # TODO: Add here formal checks on player nickname (same as db attribute)
    await state.update_data(nickname=msg.text)
    await state.set_state(cmd.AddPlayer.admin)
    text = addplayer_title
    data = await state.get_data()
    text += f"- First name: {data.get("firstname", "N/A")}\n"
    text += f"- Last name: {data.get("lastname", "N/A")}\n"
    text += f"- Nickname: {msg.text}\n"
    text += "\n➜  Would you like to grant administrator privileges?"
    await msg.answer(text, reply_markup=keyboard)
    
    
@admin_router.message(cmd.AddPlayer.admin, F.text.casefold() == "yes")
async def cmd_add_player_admin(msg: Message, state: FSMContext) -> None:
    
    keyboard = kbrd.create_reply(cmd.yesno_rk_opts)
    await state.update_data(admin=msg.text)
    await state.set_state(cmd.AddPlayer.admin)
    data = await state.get_data()
    await state.set_state(cmd.AddPlayer.admin)
    text = addplayer_title
    text += f"- First name: {data.get("firstname", "N/A")}\n"
    text += f"- Last name: {data.get("lastname", "N/A")}\n"
    text += f"- Nickname: {data.get("nickname", "N/A")}\n"
    text += f"- Admin: {msg.text}\n"
    text += "\n➜  Do you confirm?"
    await state.set_state(cmd.AddPlayer.confirm)
    await msg.answer(text, reply_markup=keyboard)
    
    
@admin_router.message(cmd.AddPlayer.admin, F.text.casefold() == "no")
async def cmd_add_player_notadmin(msg: Message, state: FSMContext) -> None:
    
    keyboard = kbrd.create_reply(cmd.yesno_rk_opts)
    await state.update_data(admin=msg.text)
    await state.set_state(cmd.AddPlayer.admin)
    data = await state.get_data()
    await state.set_state(cmd.AddPlayer.admin)
    text = addplayer_title
    text += f"- First name: {data.get("firstname", "N/A")}\n"
    text += f"- Last name: {data.get("lastname", "N/A")}\n"
    text += f"- Nickname: {data.get("nickname", "N/A")}\n"
    text += f"- Admin: {msg.text}\n"
    text += "\n➜  Do you confirm?"
    await state.set_state(cmd.AddPlayer.confirm)
    await msg.answer(text, reply_markup=keyboard)
    
    
@admin_router.message(cmd.AddPlayer.confirm, F.text.casefold() == "yes")
async def cmd_add_player_confirmed(msg: Message, state: FSMContext) -> None:
    
    data = await state.get_data()
    await state.clear()
    # TODO: Insert data into player table
    text = addplayer_title
    text += "Summary:\n"
    text += f"- First name: {data.get("firstname", "N/A")}\n"
    text += f"- Last name: {data.get("lastname", "N/A")}\n"
    text += f"- Nickname: {data.get("nickname", "N/A")}\n"
    text += f"- Admin: {data.get("admin", "N/A")}\n"
    text += addplayer_success
    keyboard = kbrd.reset_reply()
    await msg.answer(text, reply_markup=keyboard)
    
    
@admin_router.message(cmd.AddPlayer.confirm, F.text.casefold() == "no")
async def cmd_add_player_notconfirmed(msg: Message, state: FSMContext) -> None:
    
    data = await state.get_data()
    await state.clear()
    text = addplayer_title
    text += "Summary:\n"
    text += f"- First name: {data.get("firstname", "N/A")}\n"
    text += f"- Last name: {data.get("lastname", "N/A")}\n"
    text += f"- Nickname: {data.get("nickname", "N/A")}\n"
    text += f"- Admin: {data.get("admin", "N/A")}\n"
    text += addplayer_canceled
    keyboard = kbrd.reset_reply()
    await msg.answer(text, reply_markup=keyboard)