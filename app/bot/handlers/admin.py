from typing import Any, Dict
from aiogram import F, Router, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.bot import BotConfig

from bot.services.admins import user_check_admin
from bot.services import cmd
from bot.services import keyboard as kbrd
from bot.services import utils

from bot.services.db import Database


admin_router = Router()

addplayer_title = "👤 Player Registration\n\n"
addplayer_success = "\n✅ Registration completed successfully!"
addplayer_canceled = "\n❌ Registration canceled!"

pending_game_title = "❓ Pending games confirmation\n\n"
peding_game_conf = "\n✅ Game confirmed successfully!"
peding_game_notconf = "\n⚠️ Game refused successfully!"

unban_title = f"{html.quote('Unban user')}\n\n"
unban_conf = "✅ User access has been restored!"
unban_notconf = "❌ Unban canceled!\n\n"

@admin_router.callback_query(F.data == 'menu_admin')
async def cmd_admin(cb_query: CallbackQuery, cfg: BotConfig) -> None:
    
    if user_check_admin(cb_query.from_user.id, cfg):
        keybaord = kbrd.create_inline_2c(cmd.adminMenu_opts)
        await cb_query.message.edit_text(f"Welcome admin, select an option:", reply_markup=keybaord)
    else:
        await cb_query.message.edit_text(f"⛔ You are not allowed to be here!", reply_markup=None)



##### Manage players #####


@admin_router.callback_query(F.data == 'mng_players')
async def cmd_mng_admins(cb_query: CallbackQuery) -> None:
    
    keybaord = kbrd.create_inline_2c(cmd.mngPlayersMenu_opts)
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
    text += f"- First name: {data.get('firstname', 'N/A')}\n"
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
    text += f"- First name: {data.get('firstname', 'N/A')}\n"
    text += f"- Last name: {data.get('lastname', 'N/A')}\n"
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
    text += f"- First name: {data.get('firstname', 'N/A')}\n"
    text += f"- Last name: {data.get('lastname', 'N/A')}\n"
    text += f"- Nickname: {data.get('nickname', 'N/A')}\n"
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
    text += f"- First name: {data.get('firstname', 'N/A')}\n"
    text += f"- Last name: {data.get('lastname', 'N/A')}\n"
    text += f"- Nickname: {data.get('nickname', 'N/A')}\n"
    text += f"- Admin: {msg.text}\n"
    text += "\n➜  Do you confirm?"
    await state.set_state(cmd.AddPlayer.confirm)
    await msg.answer(text, reply_markup=keyboard)
    
    
@admin_router.message(cmd.AddPlayer.confirm, F.text.casefold() == "yes")
async def cmd_add_player_confirmed(msg: Message, state: FSMContext) -> None:
    
    data = await state.get_data()
    await state.clear()
    
    # Build the player_data dictionary
    player_data = {
        "first_name": data.get('firstname', 'N/A'),
        "last_name": data.get('lastname', 'N/A'),
        "admin": utils.to_boolean(data.get("admin", "false")),
        "tg_uid": None,
        "nickname": data.get('nickname', 'N/A')
    }
    
    # Insert data into player table
    db = Database()
    db.insert_player(player_data)
    
    # Preparing success response
    text = addplayer_title
    text += "Summary:\n"
    text += f"- First name: {player_data['first_name']}\n"
    text += f"- Last name: {player_data['last_name']}\n"
    text += f"- Nickname: {player_data['nickname']}\n"
    text += f"- Admin: {player_data['admin']}\n"
    text += addplayer_success
    keyboard = kbrd.reset_reply()
    await msg.answer(text, reply_markup=keyboard)
    
    
@admin_router.message(cmd.AddPlayer.confirm, F.text.casefold() == "no")
async def cmd_add_player_notconfirmed(msg: Message, state: FSMContext) -> None:
    
    data = await state.get_data()
    await state.clear()
    text = addplayer_title
    text += "Summary:\n"
    text += f"- First name: {data.get('firstname', 'N/A')}\n"
    text += f"- Last name: {data.get('lastname', 'N/A')}\n"
    text += f"- Nickname: {data.get('nickname', 'N/A')}\n"
    text += f"- Admin: {data.get('admin', 'N/A')}\n"
    text += addplayer_canceled
    keyboard = kbrd.reset_reply()
    await msg.answer(text, reply_markup=keyboard)




##### Pending Games #####


async def show_pending_game(cb_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    pend_games = data.get('pend_games', [])
    current_index = data.get('cur_idx', 0)

    # Check if there are any pending games
    if current_index < len(pend_games):
        game = pend_games[current_index]
        text = pending_game_title
        text += f"Team 1: {game['team1']}\n"
        text += f"Team 2: {game['team2']}\n"
        text += f"Scores: {game['scores']}\n"
        text += "\n➜  What would you like to do?\n"
        
        opts = [(text, "pending_games_" + callback) for text, callback in cmd.yesnoskip_ik_opts]
        keybaord = kbrd.create_inline_2c(opts)
        await cb_query.message.answer(text, reply_markup=keybaord)
        # Set state for FSM
        await state.set_state(cmd.GameStates.show_pgame)  
    else:
        await cb_query.message.answer("No more pending games.")
        # Clear state when done
        await state.clear() 
        
    
@admin_router.callback_query(F.data == 'pending_games')
async def cmd_pending_games(cb_query: CallbackQuery, state: FSMContext) -> None:
    
    # Fetch pending games
    pend_games = Database.get_pending_games()  
    await state.update_data(pend_games=pend_games, cur_idx=0)
    await cb_query.message.delete()
    await show_pending_game(cb_query, state)


@admin_router.callback_query(F.data == 'pending_games_skip')
async def cmd_pending_games_skip(cb_query: CallbackQuery, state: FSMContext) -> None:
    
    data = await state.get_data()
    current_index = data.get('cur_idx', 0)
    pend_games = data.get('pend_games', [])

    if current_index < len(pend_games) - 1:
        # Move to the next game
        current_index += 1 
        await state.update_data(cur_idx=current_index)
        await cb_query.message.delete()
        await show_pending_game(cb_query, state)
    else:
        await cb_query.message.edit_text("No more pending games.")
        await state.clear()


@admin_router.callback_query(F.data == 'pending_games_finish')
async def cmd_pending_games_finish(cb_query: CallbackQuery, state: FSMContext) -> None:
    
    await cb_query.message.edit_text("You have finished viewing pending games.")
    await state.clear()
    
    
@admin_router.callback_query(F.data == 'pending_games_yes')
async def cmd_pending_games_yes(cb_query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    current_index = data.get('cur_idx', 0)
    pend_games = data.get('pend_games', [])
        
    # Create summary text for the confirmed game
    game = pend_games[current_index] 
    Database.confirm_pending_game(game['id'], cb_query.from_user.id)
    summary_text = peding_game_conf
    summary_text += f"Team 1: {game['team1']}\n"
    summary_text += f"Team 2: {game['team2']}\n"
    summary_text += f"Scores: {game['scores']}\n"
    # Show the game summary as chat answer
    await cb_query.message.delete()
    await cb_query.message.answer(summary_text)
    
    if current_index < len(pend_games) - 1:
        
        # Move to the next game
        current_index += 1 
        await state.update_data(cur_idx=current_index)
        await show_pending_game(cb_query, state)
    else:
        await cb_query.message.answer("No more pending games.")
        await state.clear()
        

@admin_router.callback_query(F.data == 'pending_games_no')
async def cmd_pending_games_yes(cb_query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    current_index = data.get('cur_idx', 0)
    pend_games = data.get('pend_games', [])
        
    # Create summary text for the confirmed game
    game = pend_games[current_index] 
    Database.archive_pending_game(game['id'], cb_query.from_user.id)
    summary_text = peding_game_notconf
    summary_text += f"Team 1: {game['team1']}\n"
    summary_text += f"Team 2: {game['team2']}\n"
    summary_text += f"Scores: {game['scores']}\n"
    # Show the game summary as chat answer
    await cb_query.message.delete()
    await cb_query.message.answer(summary_text)
    
    if current_index < len(pend_games) - 1:
        
        # Move to the next game
        current_index += 1 
        await state.update_data(cur_idx=current_index)
        await show_pending_game(cb_query, state)
    else:
        await cb_query.message.answer("No more pending games.")
        await state.clear()
        
        
        


##### Unban user #####


@admin_router.callback_query(F.data == 'unban_user')
async def cmd_unban_user(cb_query: CallbackQuery, state: FSMContext):
    
    db = Database()
    await state.set_state(cmd.UnbanUserState.id)
    banned_users = db.get_banned_users()
    opts = [(f"{uid}", f"unban_uid_{uid}") for uid in banned_users]
    keyboard = kbrd.create_inline_2c(opts)
    text = unban_title
    text += "➜ Select the telegram id to be restored"
    await cb_query.message.edit_text(text, reply_markup=keyboard)


@admin_router.callback_query(F.data.startswith('unban_uid_'))
async def cmd_unban_uid(cb_query: CallbackQuery, state: FSMContext):

    uid = cb_query.data[10:]
    await state.update_data(uid=uid)
    await state.set_state(cmd.UnbanUserState.confirm)
    text = unban_title
    text += f"➜  Do you want to unban {uid}?"
    keyboard = kbrd.create_reply(cmd.yesno_rk_opts)
    await cb_query.message.answer(text, reply_markup=keyboard)
    

@admin_router.message(cmd.UnbanUserState.confirm)
async def cmd_unban_uid_confirm(msg: Message, state: FSMContext) -> None:

    await state.update_data(confirm=msg.text)
    data = await state.get_data()
    await state.clear()
    text = unban_title
    db = Database()
    if str(data.get('confirm', 'N/A')).casefold() == 'yes':
        db.delete_banned_user(data['uid'])
        text += unban_conf
        await msg.answer(text, reply_markup=None)
    else:
        text += unban_notconf
        await msg.answer(text, reply_markup=None)