from typing import Any, Dict
from aiogram import F, Router, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile

from bot.bot import BotConfig
from bot.services.admins import user_check_admin
from bot.services import keyboard as kbrd
from bot.services import cmd
from bot.services import utils
from bot.services.db import Database
from bot.services import elo
from bot.services import ranking
from logger import logger

user_router = Router()
addgame_title = f"{html.quote('Game Registration')}\n\n"
addgame_success = f"\n✅ Registration completed successfully!"
addgame_canceled = f"\n❌ {html.quote('Registration canceled!')} "
myprofile_title = "👤 My profile\n\n"
myprofile_edit_conf = "\n✅ Profile edited successfully!\n\n"
myprofile_edit_notconf = "\n❌ Edit canceled!\n\n"


@user_router.message(Command('user_info'))
async def cmd_user_info(msg: Message, cfg: BotConfig) -> None:
    """Check whether a user is admin or not"""
    isadmin, isadmin_str = user_check_admin(msg.from_user.id, cfg)
    await msg.answer(isadmin_str)
    logger.info(f"User {msg.from_user.id} requested admin check.")


@user_router.message(Command('dice'))
async def cmd_dice(msg: Message) -> None:
    """Answer dice to your user dice command"""
    await msg.answer_dice(emoji="🎲")
    logger.info(f"User {msg.from_user.id} rolled a dice.")


@user_router.callback_query(F.data == 'menu_myprofile')
async def cmd_myprofile(cb_query: CallbackQuery) -> None:
    db = Database()
    success, player_info = db.get_player_info_by_tg_uid(cb_query.from_user.id)
    if not success:
        logger.error(f"Failed to retrieve player info for user {cb_query.from_user.id}: {player_info}")
        await cb_query.message.answer("Failed to load profile. Please try again later.")
        return

    text = myprofile_title
    text += f"- First name: {player_info['first_name']}\n"
    text += f"- Last name: {player_info['last_name']}\n"
    text += f"- Nickname: {player_info['nickname']}\n"
    text += f"- Telegram id: {player_info['tg_uid']}\n"
    text += f"- Admin: {player_info['admin']}\n"
    text += f"- Create time: {player_info['date']}\n"
    keyboard = kbrd.create_inline_2c(cmd.myProfileMenu_opts)
    await cb_query.message.edit_text(text, reply_markup=keyboard)
    logger.info(f"User {cb_query.from_user.id} accessed profile.")


@user_router.callback_query(F.data == 'myprofile_edit')
async def cmd_myprofile_edit(cb_query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(cmd.EditProfileStates.field)
    keyboard = kbrd.create_inline_2c(cmd.myProfileEdit_opts)
    await cb_query.message.edit_text(cb_query.message.text, reply_markup=keyboard)
    logger.info(f"User {cb_query.from_user.id} started profile edit.")


@user_router.callback_query(F.data.startswith('myprofile_edit_'))
async def cmd_myprofile_edit_field(cb_query: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(field=cb_query.data[11:])
    await state.set_state(cmd.EditProfileStates.value)
    field = cb_query.data[15:]
    text = cb_query.message.text + "\n"
    text += f"\n➜ Insert your new {field}"
    await cb_query.message.answer(text, reply_markup=None)
    logger.info(f"User {cb_query.from_user.id} is editing profile field {field}.")


@user_router.message(cmd.EditProfileStates.value)
async def cmd_myprofile_edit_value(msg: Message, state: FSMContext) -> None:
    await state.update_data(value=msg.text)
    data = await state.get_data()
    await state.set_state(cmd.EditProfileStates.confirm)

    db = Database()
    success, player_info = db.get_player_info_by_tg_uid(msg.from_user.id)
    if not success:
        logger.error(f"Failed to retrieve player info for user {msg.from_user.id}: {player_info}")
        await msg.answer("Failed to load profile. Please try again later.")
        return

    player_info[data.get('field', 'N/A')[4:]] = data.get('value', 'N/A')
    text = myprofile_title
    text += f"- First name: {player_info['first_name']}\n"
    text += f"- Last name: {player_info['last_name']}\n"
    text += f"- Nickname: {player_info['nickname']}\n"
    text += f"- Telegram id: {player_info['tg_uid']}\n"
    text += f"- Admin: {player_info['admin']}\n"
    text += f"- Create time: {player_info['date']}\n"
    text += "\n➜  Do you confirm?"
    keyboard = kbrd.create_reply(cmd.yesno_rk_opts)
    await msg.answer(text, reply_markup=keyboard)
    logger.info(f"User {msg.from_user.id} is confirming profile edit.")


@user_router.message(cmd.EditProfileStates.confirm)
async def cmd_myprofile_edit_confirm(msg: Message, state: FSMContext) -> None:
    def player_info_text(info: dict) -> str:
        return (
            f"- First name: {info['first_name']}\n"
            f"- Last name: {info['last_name']}\n"
            f"- Nickname: {info['nickname']}\n"
            f"- Telegram id: {info['tg_uid']}\n"
            f"- Admin: {info['admin']}\n"
            f"- Create time: {info['date']}\n"
        )

    await state.update_data(confirm=msg.text)
    data = await state.get_data()
    await state.clear()

    db = Database()
    success, player_info = db.get_player_info_by_tg_uid(msg.from_user.id)
    if not success:
        logger.error(f"Failed to retrieve player info for user {msg.from_user.id}: {player_info}")
        await msg.answer("Failed to load profile. Please try again later.")
        return

    if str(data.get('confirm', 'N/A')).casefold() == 'yes':
        player_info[data.get('field', 'N/A')[4:]] = data.get('value', 'N/A')
        success, result = db.edit_player_info_by_tg_uid(msg.from_user.id, player_info)
        if not success:
            logger.error(f"Failed to update player info for user {msg.from_user.id}: {result}")
            await msg.answer(f"⚠️ Unexpected error while updating player info: {result}. Please contact administrator.")
            return
        resp = myprofile_edit_conf
        logger.info(f"User {msg.from_user.id} updated their profile successfully.")
    else:
        resp = myprofile_edit_notconf
        logger.info(f"User {msg.from_user.id} canceled profile edit.")

    text = myprofile_title + player_info_text(player_info) + resp
    keyboard = kbrd.create_inline_2c(cmd.myProfileEdit_opts)
    await msg.answer(text, reply_markup=keyboard)


@user_router.callback_query(F.data == 'menu_addgame')
async def cmd_addgame(cb_query: CallbackQuery, state: FSMContext) -> None:
    db = Database()
    success, ids = db.players_get_ids()
    if not success:
        logger.error(f"Failed to fetch player ids: {ids}")
        await cb_query.message.answer("Failed to retrieve player information. Please try again later.")
        return

    if len(ids) < 4:
        text = "⛔ Insufficient players in the database. Please register at least 4 players before adding a game."
        await cb_query.message.edit_text(text, reply_markup=None)
        logger.warning(f"User {cb_query.from_user.id} attempted to add a game with insufficient players.")
    elif cb_query.from_user.id in ids:
        await state.set_state(cmd.AddGame.player1)

        # Preparing for player 1
        success, nicknames = db.players_get_nicknames()
        if not success:
            logger.error(f"Failed to fetch player nicknames: {nicknames}")
            await cb_query.message.answer("Failed to retrieve player information. Please try again later.")
            return

        opts = [(nick, f"addgame_p1_{nick}") for nick in nicknames]
        keyboard = kbrd.create_inline_2c(opts)
        text = addgame_title + "\n➜ Select the first player of team 1"
        await cb_query.message.edit_text(text, reply_markup=keyboard)
        logger.info(f"User {cb_query.from_user.id} started adding a game.")
    else:
        text = "⛔ You are not allowed to be here!"
        await cb_query.message.edit_text(text, reply_markup=None)
        

@user_router.callback_query(F.data.startswith('addgame_p1_'))
async def cmd_addgame_p1(cb_query: CallbackQuery, state: FSMContext) -> None:
    player1 = cb_query.data[11:]
    await state.update_data(player1=player1)
    await state.set_state(cmd.AddGame.player2)
    data = await state.get_data()
    players_nick = [data.get('player1', 'N/A')]

    db = Database()
    success, nicknames = db.players_get_nicknames()
    if not success:
        logger.error(f"Failed to fetch player nicknames: {nicknames}")
        await cb_query.message.answer("Failed to retrieve player information. Please try again later.")
        return
    opts = [(nick, f"addgame_p2_{nick}") for nick in nicknames if nick not in players_nick]
    print(players_nick)
    print(nicknames)
    print(opts)
    keyboard = kbrd.create_inline_2c(opts)
    text = addgame_title
    text += f"Team 1:\n"
    text += f"- First player: {data.get('player1', 'N/A')}\n"
    text += "\n➜ Select the second player of team 1"
    await cb_query.message.edit_text(text, reply_markup=keyboard)
    
    logger.info(f"Player {player1} selected as first player for Team 1 by user {cb_query.from_user.id}.")


@user_router.callback_query(F.data.startswith('addgame_p2_'))
async def cmd_addgame_p2(cb_query: CallbackQuery, state: FSMContext) -> None:
    player2 = cb_query.data[11:]
    await state.update_data(player2=player2)
    await state.set_state(cmd.AddGame.player3)
    data = await state.get_data()
    players_nick = [data.get('player1', 'N/A'), data.get('player2', 'N/A')]

    db = Database()
    success, nicknames = db.players_get_nicknames()
    if not success:
        logger.error(f"Failed to fetch player nicknames: {nicknames}")
        await cb_query.message.answer("Failed to retrieve player information. Please try again later.")
        return
    opts = [(nick, f"addgame_p3_{nick}") for nick in nicknames if nick not in players_nick]
    keyboard = kbrd.create_inline_2c(opts)
    text = addgame_title
    text += f"Team 1:\n"
    text += f"- First player: {data.get('player1', 'N/A')}\n"
    text += f"- Second player: {data.get('player2', 'N/A')}\n"
    text += "\n➜ Select the first player of team 1"
    await cb_query.message.edit_text(text, reply_markup=keyboard)
    
    logger.info(f"Player {player2} selected as second player for Team 1 by user {cb_query.from_user.id}.")


@user_router.callback_query(F.data.startswith('addgame_p3_'))
async def cmd_addgame_p3(cb_query: CallbackQuery, state: FSMContext) -> None:
    player3 = cb_query.data[11:]
    await state.update_data(player3=player3)
    await state.set_state(cmd.AddGame.player4)
    data = await state.get_data()
    players_nick = [data.get('player1', 'N/A'), data.get('player2', 'N/A'), data.get('player3', 'N/A')]

    db = Database()
    success, nicknames = db.players_get_nicknames()
    if not success:
        logger.error(f"Failed to fetch player nicknames: {nicknames}")
        await cb_query.message.answer("Failed to retrieve player information. Please try again later.")
        return
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
    
    logger.info(f"Player {player3} selected as first player for Team 2 by user {cb_query.from_user.id}.")


@user_router.callback_query(F.data.startswith('addgame_p4_'))
async def cmd_addgame_p4(cb_query: CallbackQuery, state: FSMContext) -> None:
    player4 = cb_query.data[11:]
    await state.update_data(player4=player4)
    await state.set_state(cmd.AddGame.score1)
    data = await state.get_data()
    players_nick = [data.get('player1', 'N/A'), data.get('player2', 'N/A'), data.get('player3', 'N/A'), data.get('player4', 'N/A')]

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
    logger.info(f"Player {player4} selected as second player for Team 2 by user {cb_query.from_user.id}.")


@user_router.callback_query(F.data.startswith('addgame_s1_'))
async def cmd_addgame_s1(cb_query: CallbackQuery, state: FSMContext) -> None:
    score1 = int(cb_query.data[11:])
    await state.update_data(score1=score1)
    await state.set_state(cmd.AddGame.score2)
    data = await state.get_data()

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
    logger.info(f"Score for Team 1 set to {score1} by user {cb_query.from_user.id}.")


@user_router.callback_query(F.data.startswith('addgame_s2_'))
async def cmd_addgame_s2(cb_query: CallbackQuery, state: FSMContext) -> None:
    score2 = int(cb_query.data[11:])
    await state.update_data(score2=score2)
    await state.set_state(cmd.AddGame.confirm)
    data = await state.get_data()
    score1 = int(data.get('score1', 'N/A'))

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
        logger.warning(f"Invalid score selection by user {cb_query.from_user.id}: Neither team has a score of 10.")
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
        logger.info(f"Scores set by user {cb_query.from_user.id}: Team 1 - {score1}, Team 2 - {score2}. Confirmation requested.")
    

@user_router.callback_query(F.data.casefold() == "addgame_conf_yes")
async def cmd_addgame_conf(cb_query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    score1 = data.get('score1', 'N/A')
    score2 = data.get('score2', 'N/A')

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

    # Insert game into pending games
    success, result = Database().insert_pending_game(game_data)
    if not success:
        logger.error(f"Failed to insert pending game: {result}")
        await cb_query.message.answer("Failed to add the game. Please try again later.")
        return

    text = addgame_title
    text += f"Team 1:\n- {data.get('player1', 'N/A')} and {data.get('player2', 'N/A')}\n"
    text += f"\nTeam 2:\n- {data.get('player3', 'N/A')} and {data.get('player4', 'N/A')}\n"
    if score1 > score2:
        text += f"\nTeam 1 wins against Team 2 for {score1} to {score2}.\n"
    else:
        text += f"\nTeam 2 wins against Team 1 for {score2} to {score1}.\n"
    text += addgame_success
    await cb_query.message.edit_text(text, reply_markup=None)
    logger.info(f"Game added successfully by user {cb_query.from_user.id}.")


@user_router.callback_query(F.data.casefold() == "addgame_conf_no")
async def cmd_addgame_notconf(cb_query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    score1 = data.get('score1', 'N/A')
    score2 = data.get('score2', 'N/A')

    text = addgame_title
    text += f"Team 1:\n- {data.get('player1', 'N/A')} and {data.get('player2', 'N/A')}\n"
    text += f"\nTeam 2:\n- {data.get('player3', 'N/A')} and {data.get('player4', 'N/A')}\n"
    if score1 > score2:
        text += f"\nTeam 1 wins against Team 2 for {score1} to {score2}.\n"
    else:
        text += f"\nTeam 2 wins against Team 1 for {score2} to {score1}.\n"
    text += addgame_canceled
    await cb_query.message.edit_text(text, reply_markup=None)
    logger.info(f"User {cb_query.from_user.id} canceled the game addition.")


@user_router.callback_query(F.data == 'ranking')
async def show_ranking_callback(cb_query: CallbackQuery):
    logger.info(f"User {cb_query.from_user.id} requested the ranking.")

    db = Database()
    # Fetch player data
    success, players_data = db.get_all_players()

    if not success:
        logger.error(f"Failed to load ranking data for user {cb_query.from_user.id}: {players_data}")
        await cb_query.message.answer("Error loading ranking data.")
        return

    logger.info(f"Successfully retrieved ranking data for user {cb_query.from_user.id}")

    # Generate HTML file and send it to the user
    try:
        html_file_path = ranking.generate_ranking_html(players_data)
        await cb_query.message.answer_document(FSInputFile(html_file_path, "ranking.html"))
        logger.info(f"Ranking file {html_file_path} sent to user {cb_query.from_user.id}.")
    except Exception as e:
        logger.error(f"Failed to generate or send ranking HTML for user {cb_query.from_user.id}: {e}")
        await cb_query.message.answer("Error generating ranking file.")