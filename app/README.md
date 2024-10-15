# Project Title

This directory containes sourse code writted in python of the Foosball Elo Ranking Telegram Bot

## Table of Contents

- [Project Title](#project-title)
  - [Table of Contents](#table-of-contents)
  - [Installation Instructions](#installation-instructions)
  - [Usage](#usage)
  - [Bugs](#bugs)
  - [TO Do list](#to-do-list)
    - [Start](#start)
    - [Administrators menu](#administrators-menu)
      - [Manage players](#manage-players)
      - [Add new player](#add-new-player)
      - [Pending games](#pending-games)
    - [Add game](#add-game)
    - [Database](#database)

## Installation Instructions

1. Clone the repository:
   ```bash
   $ git clone <ssh-repo-link>
   ```
   
## Usage

Create a .env file in "app" directory with the followings:
- API_TOKEN: telegram bot api token from bot father
- DB_PATH: relative path (from "app" directory) to the sqlite database
- ROOTADMIN_INFO: root admin information formatted as json:
```json
  {
    "first_name": <first-name>,
    "last_name": <last-name>, 
    "admin": true, 
    "tg_uid": <uid>, 
    "nickname": <nickname>
  }
```

Create a python environment.
```bash
$ python -m venv venv
```
Then activate the virtual environment and install required packages.
```bash
$ source venv/bin/activate
```

Before running the application remember to source the environment variables in .env file. You can use the following command.
```bash
$ set -o allexport && source ./.env && set +o allexport
```

## Bugs
- [ ] Unable to restore keybaord after finishing an operation

## TO Do list

### Start
- [ ] Welcome: "First time here?" question to connect user to database player table. 
  - [ ] Bot asks user to give their nickname. The bot will propose the list of gameed players, then the user will select the player. Then bot makes an inline message with buttons to ask for confirmation.
- [ ] Main Menu
  - [ ] [Admins menu](#administrators-menu)
  - [ ] [My profile](#my-profile-menu)
  - [ ] [Add game](#add-game)

### Administrators menu
- [ ] Add options to select between 
  - [ ] [Manage players](#manage-players)
  - [ ] [Pending games](#pending-games)
  - [ ] Back

#### Manage players
- [ ] [Add new player](#add-new-player) 
- [ ] [Edit player](#edit-player)
- [ ] Back

#### Add new player
- [x] Ask first name, last name, nickname and privileges
- [x] Show summary (yes or cancel options)
- [ ] Add user admin check
- [ ] Push players to db table of players

#### Pending games
- [ ] Add user admin check
- [ ] Get game from db table of pending games one-by-one
- [ ] Build a message with inline keyboard asking for confirmation
- [ ] Ask before confirm (place a cancel button)

### Add game
- [ ] Setup aiogram fsm
- [ ] Create handlers for fsm states
- [ ] Add user id check to prevent unregistered user to add games
- [ ] Ask for confirmation after all game data insertion
- [ ] Push game to db table of pending games
- [ ] Notify admins to approve a game

### Database
- [x] Create database file under services module
- [x] Create all tables:
  - [x] players:
    - id: primery key
    - first name (only letters)
    - last name (only letters)
    - admin (flag)
    - tgid (int)
    - nickname (letters and symbols)
    - date
  - [x] games
    - id: primery key
    - first team (json: player1, player2)
    - second team (json: player1, player2)
    - score (json: first team, second team)
    - date
    - confirm admin id (foreign id key of players table)
    - confirm date
  - [x] pending games
    - id: primery key
    - first team (json: player1, player2 (foreign id key of players table))
    - second team (json: player1, player2 (foreign id key of players table))
    - score (json: first team, second team (only numbers between 0 and 10))
    - date
  - [x] Create function to insert the root admin as player getting the info from the config module
  - [x] Create function to check if nickname exists in players table
  - [x] Create function to get the list of all nicknames of the registered players
  - [ ] Create function to insert a player in database
  - [ ] Create function to insert game in pending games table
  - [ ] Create function to fetch pending games from pending games table
  - [ ] Create function to insert game in games tables