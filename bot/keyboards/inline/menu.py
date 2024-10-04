from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.filters.callbackdata import OffsetOfGameFactory


def main_keyboard() -> InlineKeyboardMarkup:
    """Use in main menu."""
    buttons = [
        [InlineKeyboardButton(text="Перейти к играм", web_app=WebAppInfo(url="https://tg-bot.bezabon.online:3000"))],
        # [InlineKeyboardButton(text=_("money button"), callback_data="money")],
        # [InlineKeyboardButton(text=_("support button"), callback_data="support")],
    ]

    keyboard = InlineKeyboardBuilder(markup=buttons)

    keyboard.adjust(1)

    return keyboard.as_markup()