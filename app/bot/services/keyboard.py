from aiogram.types import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)

from bot.services import cmd

def create_inline_2c(options: list) -> InlineKeyboardMarkup:
    """Create a custom inline keyboard formatted in max 2 buttons per row.
    In case of odd number of elements, the last is displayed in a single row.

    Args:
        options (list): list of tuples formatted as (<displayed-text>,<callback-text>)

    Returns:
        InlineKeyboardMarkup: Formatted Inline keyboard markup.
    """
       
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for i in range(0, len(options), 2):
        row_buttons = []
        
        for j in range(2):
            if i + j < len(options):
                text, callback_data = options[i + j]
                row_buttons.append(InlineKeyboardButton(text=text, callback_data=callback_data))

        keyboard.inline_keyboard.append(row_buttons)
    return keyboard

def create_inline_5c(options: list) -> InlineKeyboardMarkup:
    """Create a custom inline keyboard formatted with a maximum of 5 buttons per row.
    If there are fewer than 5 elements in the last row, they will spread across the entire row.

    Args:
        options (list): list of tuples formatted as (<displayed-text>, <callback-text>)

    Returns:
        InlineKeyboardMarkup: Formatted Inline keyboard markup.
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for i in range(0, len(options), 5):
        row_buttons = []
        for j in range(5):
            if i + j < len(options):
                text, callback_data = options[i + j]
                row_buttons.append(InlineKeyboardButton(text=text, callback_data=callback_data))
                
        keyboard.inline_keyboard.append(row_buttons)
    return keyboard

def create_reply(options: list) -> ReplyKeyboardMarkup:
    """Create a custom reply keyboard.

    Args:
        options (list): list of strings formatted as <displayed-text>

    Returns:
        ReplyKeyboardMarkup: Formatted Reply keyboard markup.
    """
    
    button_list = [KeyboardButton(text=option) for option in options]
    keyboard = ReplyKeyboardMarkup(
        keyboard=[button_list],
        resize_keyboard=True,
    )
    return keyboard

def reset_reply() -> ReplyKeyboardMarkup:
    """Reset reply keyboard.

    Returns:
        ReplyKeyboardMarkup: _description_
    """
    return ReplyKeyboardRemove()