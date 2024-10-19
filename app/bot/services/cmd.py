from aiogram.fsm.state import State, StatesGroup

dflt_opts = ["Start", "Help"]

yesno_rk_opts = ["Yes", "No"]

yesno_ik_opts = [
    ("Yes", "yes"),
    ("No", "no"),
]

yesnoskip_ik_opts = [
    ("Yes", "yes"),
    ("No", "no"),
    ("Skip", "skip"),
    ("Finish", "finish")
]

cancel_ik_opts  = [
    ("Cancel", "cancel")
]

# Main menu options
mainMenu_opts = [
    ("Admin", "menu_admin"),
    ("My profile", "menu_myprofile"),
    ("Add game", "menu_addgame")
]

# Admin menu options
adminMenu_opts = [
    ("Manage players", "mng_players"),
    ("Pending games", "pending_games"),
    ("🔙 Back", "menu_main") 
]

# Manage admins menu options
mngPlayersMenu_opts = [
    ("Add new player", "add_player"),
    ("Edit player", "edit_player"),
    ("🔙 Back", "menu_admin") 
]

# Edit players menu options
__editPlayerMenu_opts = [
    ("Edit first name", "edit_firstname"),
    ("Edit last name", "edit_lastname"),
    ("Edit nickname", "edit_nickname"),
    ("Edit privileges", "edit_privileges")
]

# Admin Edit player
adminEditPlayer_opts = __editPlayerMenu_opts + [
    ("⚠️ Delete", "delete_player"),
    ("🔙 Back", "mng_players") 
]

# My Profile menu options
myProfileMenu_opts = [
    ("Show statistics", "myprofile_stats"),
    ("Edit", "myprofile_edit"),
    ("🔙 Back", "menu_main"),
]

# My profile edit
myProfileEdit_opts = [
    ("Edit first name", "myprofile_edit_first_name"),
    ("Edit last name", "myprofile_edit_last_name"),
    ("Edit nickname", "myprofile_edit_nickname"),
    ("🔙 Back", "menu_myprofile")
]

# Edit My Profile menu options
editMyProfileMenu_opts = __editPlayerMenu_opts

# Finite State Machine classes

class AddPlayer(StatesGroup):
    firstname = State()
    lastname = State()
    nickname = State()
    admin = State()
    confirm = State()
    
class AddGame(StatesGroup):
    player1 = State()
    player2 = State()
    player3 = State()
    player4 = State()
    score1 = State()
    score2 = State()
    confirm = State()
    

class GameStates(StatesGroup):
    show_pgame = State()
    
class EditProfileStates(StatesGroup):
    field = State()
    value = State()
    confirm = State()