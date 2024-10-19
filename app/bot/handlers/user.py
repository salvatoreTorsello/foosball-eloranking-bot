from typing import Any, Dict
from aiogram import F, Router, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.bot import BotConfig

from bot.services.admins import user_check_admin
from bot.services import keyboard as kbrd
from bot.services import cmd

from bot.services.db import Database


user_router = Router()
addgame_title = f"{html.quote('Game Registration')}\n\n"
addgame_success = f"\n✅ Registration completed successfully!"
addgame_canceled = f"\n❌ {html.quote('Registration canceled!')} "


@user_router.message(Command('user_info'))
async def cmd_user_info(msg: Message, cfg: BotConfig) -> None:
    """Check wether as user is admin or not"""
    
    isadmin, isadmin_str = user_check_admin(msg.from_user.id, cfg)
    await msg.answer(isadmin_str)
    

@user_router.message(Command('dice'))
async def cmd_dice(msg: Message) -> None:
    """Answer dice to yur user dice command"""
    
    await msg.answer_dice(emoji="🎲")
    

@user_router.callback_query(F.data == 'menu_addgame')
async def cmd_addgame(cb_query: CallbackQuery, state: FSMContext) -> None:
    
    db = Database()
    ids = db.players_get_ids()
    if len(ids) < 4:
        text = "⛔ Not enough players in database.\nRegister players before adding a game."
        await cb_query.message.edit_text(text, reply_markup=None)
    elif cb_query.from_user.id in ids:
        await state.set_state(cmd.AddGame.player1)
        
        # Preparing for player 1
        nicknames = db.players_get_nicknames()
        opts = [(nick, f"addgame_p1_{nick}") for nick in nicknames]
        keyboard = kbrd.create_inline_2c(opts)
        text = addgame_title
        text += "\n➜ Select the first player of team 1"
        await cb_query.message.edit_text(text, reply_markup=keyboard)
    else:
        text = "⛔ You are not allowed to be here!"
        await cb_query.message.edit_text(text, reply_markup=None)
        

@user_router.callback_query(F.data.startswith('addgame_p1_'))
async def cmd_addgame_p1(cb_query: CallbackQuery, state: FSMContext) -> None:
    
    # Save player 1
    await state.update_data(player1=cb_query.data[11:])
    await state.set_state(cmd.AddGame.player2)
    data = await state.get_data()
    players_nick = [data.get('player1', 'N/A')]
    
    # Preparing for player 2
    db = Database()
    nicknames = db.players_get_nicknames()
    opts = [(nick, f"addgame_p2_{nick}") for nick in nicknames if nick not in players_nick]
    keyboard = kbrd.create_inline_2c(opts)
    text = addgame_title
    text += f"Team 1:\n"
    text += f"- First player: {data.get('player1', 'N/A')}\n"
    text += "\n➜ Select the second player of team 1"
    await cb_query.message.edit_text(text, reply_markup=keyboard)
        

@user_router.callback_query(F.data.startswith('addgame_p2_'))
async def cmd_addgame_p2(cb_query: CallbackQuery, state: FSMContext) -> None:
    
    # Save player 2
    await state.update_data(player2=cb_query.data[11:])
    await state.set_state(cmd.AddGame.player3)
    data = await state.get_data()
    players_nick = [
        data.get('player1', 'N/A'),
        data.get('player2', 'N/A')
    ]
    
    # Preparing for player 3
    db = Database()
    nicknames = db.players_get_nicknames()
    opts = [(nick, f"addgame_p3_{nick}") for nick in nicknames if nick not in players_nick]
    keyboard = kbrd.create_inline_2c(opts)
    text = addgame_title
    text += f"Team 1:\n"
    text += f"- First player: {data.get('player1', 'N/A')}\n"
    text += f"- Second player: {data.get('player2', 'N/A')}\n"
    text += "\n➜ Select the first player of team 1"
    await cb_query.message.edit_text(text, reply_markup=keyboard)
        

@user_router.callback_query(F.data.startswith('addgame_p3_'))
async def cmd_addgame_p3(cb_query: CallbackQuery, state: FSMContext) -> None:
    
    # Save player 2
    await state.update_data(player3=cb_query.data[11:])
    await state.set_state(cmd.AddGame.player4)
    data = await state.get_data()
    players_nick = [
        data.get('player1', 'N/A'),
        data.get('player2', 'N/A'),
        data.get('player3', 'N/A')
    ]
    
    # Preparing for player 3
    db = Database()
    nicknames = db.players_get_nicknames()
    opts = [(nick, f"addgame_p4_{nick}") for nick in nicknames if nick not in players_nick]
    keyboard = kbrd.create_inline_2c(opts)
    text = addgame_title
    text += f"Team 1:\n"
    text += f"- First player: {data.get('player1', 'N/A')}\n"
    text += f"- Second player: {data.get('player2', 'N/A')}\n"
    text += f"\nTeam 2:\n"
    text += f"- First player: {data.get('player3', 'N/A')}\n"
    text += "\n➜ Select the first player of team 2"
    await cb_query.message.edit_text(text, reply_markup=keyboard)
        

@user_router.callback_query(F.data.startswith('addgame_p4_'))
async def cmd_addgame_p4(cb_query: CallbackQuery, state: FSMContext) -> None:
    
    # Save player 2
    await state.update_data(player4=cb_query.data[11:])
    await state.set_state(cmd.AddGame.score1)
    data = await state.get_data()
    players_nick = [
        data.get('player1', 'N/A'),
        data.get('player2', 'N/A'),
        data.get('player3', 'N/A'),
        data.get('player4', 'N/A')
    ]
    
    # Preparing for team 1 score
    opts = list(range(11))
    opts = [(f"{opt}", f"addgame_s1_{opt}") for opt in opts]
    keyboard = kbrd.create_inline_5c(opts)
    text = addgame_title
    text += f"Team 1:\n"
    text += f"- First player: {data.get('player1', 'N/A')}\n"
    text += f"- Second player: {data.get('player2', 'N/A')}\n"
    text += f"\nTeam 2:\n"
    text += f"- First player: {data.get('player3', 'N/A')}\n"
    text += f"- Second player: {data.get('player4', 'N/A')}\n"
    text += "\n➜ Select the score of team 1"
    await cb_query.message.edit_text(text, reply_markup=keyboard)
        

@user_router.callback_query(F.data.startswith('addgame_s1_'))
async def cmd_addgame_p4(cb_query: CallbackQuery, state: FSMContext) -> None:
    
    # Save player 2
    await state.update_data(score1=cb_query.data[11:])
    await state.set_state(cmd.AddGame.score2)
    data = await state.get_data()
    score1 = int(data.get('score1', 'N/A'))
    
    # Preparing for team 1 score
    opts = list(range(11))
    opts.remove(score1)
    opts = [(f"{opt}", f"addgame_s2_{opt}") for opt in opts]
    keyboard = kbrd.create_inline_5c(opts)
    text = addgame_title
    text += f"Team 1:\n"
    text += f"- First player: {data.get('player1', 'N/A')}\n"
    text += f"- Second player: {data.get('player2', 'N/A')}\n"
    text += f"\nTeam 2:\n"
    text += f"- First player: {data.get('player3', 'N/A')}\n"
    text += f"- Second player: {data.get('player4', 'N/A')}\n"
    text += "\n➜ Select the score of team 2"
    await cb_query.message.edit_text(text, reply_markup=keyboard)
        

@user_router.callback_query(F.data.startswith('addgame_s2_'))
async def cmd_addgame_p4(cb_query: CallbackQuery, state: FSMContext) -> None:
    
    # Save player 2
    await state.update_data(score2=cb_query.data[11:])
    await state.set_state(cmd.AddGame.confirm)
    data = await state.get_data()
    score1 =  int(data.get('score1', 'N/A'))
    score2 =  int(data.get('score2', 'N/A'))
    
    text = addgame_title
    text += f"Team 1:\n"
    text += f"- {data.get('player1', 'N/A')} and {data.get('player2', 'N/A')}\n"
    text += f"\nTeam 2:\n"
    text += f"- {data.get('player3', 'N/A')} and {data.get('player4', 'N/A')}\n"
    if (score1 != 10 and score2 != 10):
        text += f"\n ⚠️ One of the two scores must be 10, please retry.\n"
        text += "\n➜ Select the score of team 1"
        # Preparing for team 1 score
        opts = list(range(11))
        opts = [(f"{opt}", f"addgame_s1_{opt}") for opt in opts]
        keyboard = kbrd.create_inline_5c(opts)
        await cb_query.message.edit_text(text, reply_markup=keyboard)
    else:
        # Preparing for confirmation
        opts = [(text, "addgame_conf_" + callback) for text, callback in cmd.yesno_ik_opts]
        keyboard = kbrd.create_inline_2c(opts)
        if score1 > score2:
            text += f"\nTeam 1 wins against Team 2 for {score1} to {score2}.\n"
        else:
            text += f"\nTeam 2 wins against Team 1 for {score2} to {score1}.\n"
        text += "\n➜  Do you confirm?"
        await cb_query.message.edit_text(text, reply_markup=keyboard)
    

@user_router.callback_query(F.data.casefold() == "addgame_conf_yes")
async def cmd_addgame_conf(cb_query: CallbackQuery, state: FSMContext) -> None:
    
    data = await state.get_data()
    await state.clear()
    score1 =  data.get('score1', 'N/A')
    score2 =  data.get('score2', 'N/A')
    
    # Constructing game_data dictionary
    game_data = {
        "team1": {
            "players": [data.get('player1', 'N/A'), data.get('player2', 'N/A')]
        },
        "team2": {
            "players": [data.get('player3', 'N/A'), data.get('player4', 'N/A')]
        },
        "scores": {
            "team1": int(score1),
            "team2": int(score2)
        }
    }
    
    # Insert data into pending games table
    Database.insert_pending_game(game_data)
    
    text = addgame_title
    text += f"Team 1:\n"
    text += f"- {data.get('player1', 'N/A')} and {data.get('player2', 'N/A')}\n"
    text += f"\nTeam 2:\n"
    text += f"- {data.get('player3', 'N/A')} and {data.get('player4', 'N/A')}\n"
    if score1 > score2:
        text += f"\nTeam 1 wins against Team 2 for {score1} to {score2}.\n"
    else:
        text += f"\nTeam 2 wins against Team 1 for {score2} to {score1}.\n"
    text += addgame_success
    keyboard = kbrd.reset_reply()
    await cb_query.message.edit_text(text, reply_markup=None)
    

@user_router.callback_query(F.data.casefold() == "addgame_conf_no")
async def cmd_addgame_notconf(cb_query: CallbackQuery, state: FSMContext) -> None:
    
    data = await state.get_data()
    await state.clear()
    score1 =  data.get('score1', 'N/A')
    score2 =  data.get('score2', 'N/A')
    
    text = addgame_title
    text += f"Team 1:\n"
    text += f"- {data.get('player1', 'N/A')} and {data.get('player2', 'N/A')}\n"
    text += f"\nTeam 2:\n"
    text += f"- {data.get('player3', 'N/A')} and {data.get('player4', 'N/A')}\n"
    if score1 > score2:
        text += f"\nTeam 1 wins against Team 2 for {score1} to {score2}.\n"
    else:
        text += f"\nTeam 2 wins against Team 1 for {score2} to {score1}.\n"
    text += addgame_canceled
    keyboard = kbrd.reset_reply()
    await cb_query.message.edit_text(text, reply_markup=None)