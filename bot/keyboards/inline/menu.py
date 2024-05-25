from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.filters.callbackdata import OffsetOfGameFactory


def main_keyboard() -> InlineKeyboardMarkup:
    """Use in main menu."""
    buttons = [
        [InlineKeyboardButton(text=_("games button"), callback_data="games")],
        [InlineKeyboardButton(text=_("profile button"), callback_data="profile")],
        [InlineKeyboardButton(text="Перейти к играм", web_app=WebAppInfo(url="https://tg-bot.bezabon.online:3000"))],
        # [InlineKeyboardButton(text=_("money button"), callback_data="money")],
        [InlineKeyboardButton(text=_("support button"), callback_data="support")],
    ]

    keyboard = InlineKeyboardBuilder(markup=buttons)

    keyboard.adjust(2, 1, 1)

    return keyboard.as_markup()


def games_keyboard(game_id: int, offset: int = 0) -> InlineKeyboardMarkup:
    """Use in games menu."""
    buttons = [
        [InlineKeyboardButton(text="Открыть игру!", web_app=WebAppInfo(url=f"https://tg-bot.bezabon.online:3000/{game_id}"))],
        [InlineKeyboardButton(text="<-", callback_data=OffsetOfGameFactory(offset=offset - 1).pack())],
        [InlineKeyboardButton(text="->", callback_data=OffsetOfGameFactory(offset=offset + 1).pack())],
        [InlineKeyboardButton(text="Вернутся в главное меню", callback_data="menu")]
    ]

    keyboard = InlineKeyboardBuilder(markup=buttons)

    keyboard.adjust(1, 2, 1)

    return keyboard.as_markup()


def profile_keyboard() -> InlineKeyboardMarkup:
    """Use in games menu."""
    buttons = [
        [InlineKeyboardButton(text="Пополнить", callback_data="add money")],
        [InlineKeyboardButton(text="Вернутся в главное меню", callback_data="menu")],
    ]

    keyboard = InlineKeyboardBuilder(markup=buttons)

    keyboard.adjust(1, 1)

    return keyboard.as_markup()


def only_go_to_main_keyboard() -> InlineKeyboardMarkup:
    """Use in games menu."""
    buttons = [
        [InlineKeyboardButton(text="Вернутся в главное меню", callback_data="menu")],
    ]

    keyboard = InlineKeyboardBuilder(markup=buttons)

    keyboard.adjust(1)

    return keyboard.as_markup()
