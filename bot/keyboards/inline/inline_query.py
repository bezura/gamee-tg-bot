from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def inline_query_markup(game_id: int) -> InlineKeyboardMarkup:
    """Use in inline query"""
    buttons = [
        [InlineKeyboardButton(text="Открыть игру!",
                              url=f"https://t.me/gamees_pay_bot/play?startapp=game_id_{game_id}&startApp=game_id_{game_id}")
         ]
    ]

    keyboard = InlineKeyboardBuilder(markup=buttons)

    keyboard.adjust(1)

    return keyboard.as_markup()
