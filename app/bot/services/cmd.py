from aiogram.fsm.state import State, StatesGroup

dflt_opts = ["Start", "Help"]

yesno_rk_opts = ["Yes", "No"]

cancel_ik_opts  = [
    ("Cancel", "cancel")
]

# Main menu options
mainMenu_opts = [
    ("Admin", "menu_admin"),
    ("My profile", "menu_profile"),
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

class AddPlayer(StatesGroup):
    firstname = State()
    lastname = State()
    nickname = State()
    admin = State()
    confirm = State()

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
    ("Show statistics", "show_stats"),
    ("Edit", "myprofile_edit_player"),
    ("🔙 Back", "menu_main"),
]

# Edit My Profile menu options
editMyProfileMenu_opts = __editPlayerMenu_opts