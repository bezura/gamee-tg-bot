from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import LinkPreviewOptions
from aiogram.utils.i18n import gettext as _
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.callbackdata import OffsetOfGameFactory
from bot.filters.state import EarnMoney
from bot.keyboards.inline.menu import main_keyboard, profile_keyboard, only_go_to_main_keyboard, games_keyboard
from bot.services.games import get_game_by_offset, get_games_count
from bot.services.users import get_user_money, get_user_data, add_money_by_id

router = Router(name="menu")


@router.message(Command(commands=["menu", "main"]))
async def menu_handler(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    """Return main menu."""
    await message.answer(_("title main keyboard"), reply_markup=main_keyboard())


@router.callback_query(F.data == "menu")
async def callback_menu_handler(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback_query.message.edit_text(_("title main keyboard"), reply_markup=main_keyboard())


@router.callback_query(F.data == "games")
@router.callback_query(OffsetOfGameFactory.filter())
async def callback_menu_handler(callback_query: types.CallbackQuery, state: FSMContext, session: AsyncSession,
                                callback_data: OffsetOfGameFactory = OffsetOfGameFactory()) -> None:
    await state.clear()
    offset = callback_data.offset
    if offset < 0:
        offset = await get_games_count(session=session) - 1
        game = await get_game_by_offset(session=session, offset=offset)

    else:
        game = await get_game_by_offset(session=session, offset=offset)
        if game is None:
            offset = 0
            game = await get_game_by_offset(session=session, offset=offset)

    await callback_query.message.edit_text(f"{game.title}\n{game.description}",
                                           reply_markup=games_keyboard(offset=offset),
                                           link_preview_options=LinkPreviewOptions(
                                               is_disabled=False,
                                               url=game.thumbnail_url or "https://docs.python-telegram-bot.org/en/"
                                                                         "v13.10/_static/ptb-logo-orange.png",
                                               show_above_text=True,
                                               prefer_large_media=True
                                           ), )


@router.callback_query(F.data == "support")
async def callback_menu_handler(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback_query.message.edit_text("Вы можете связаться с администрацией написав на данный аккаунт @hardzz",
                                           reply_markup=only_go_to_main_keyboard())


@router.callback_query(F.data == "profile")
async def profile_handler(callback_query: types.CallbackQuery, session: AsyncSession) -> None:
    user = await get_user_data(session=session, user_id=callback_query.from_user.id)

    await callback_query.message.edit_text(text=
                                           f"Приветствуем, {user.first_name}🖖\n\n"
                                           f"В твоем профиле ты можешь:\n"
                                           f" * Пополнить счет💸\n"
                                           f" * Просмотреть статистику и историю игр📈\n"
                                           f" * Узнать свой текущий баланс💰: <b>{user.money or 0.0:.2f} рублей</b>\n\n",
                                           reply_markup=profile_keyboard())


@router.callback_query(F.data == "add money")
async def profile_handler(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await callback_query.message.edit_text(text=f"Назовите, ответным сообщением сумму, Господин",
                                           reply_markup=only_go_to_main_keyboard())
    await state.set_state(EarnMoney.chose_counting)


@router.message(EarnMoney.chose_counting, F.text.regexp(r"\d+[\.]?\d+"))
async def add_money_handler(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    old_money = await get_user_money(session=session, user_id=message.from_user.id)
    add_money = float(message.text)
    new_count_money = old_money + add_money
    await add_money_by_id(session=session, user_id=message.from_user.id, new_count_money=new_count_money)
    await message.answer(text=f"Вам пополнен баланс на +{add_money}\nСейчас у вас {new_count_money} рублей")
    await state.clear()
    await message.answer(_("title main keyboard"), reply_markup=main_keyboard())


@router.message(EarnMoney.chose_counting)
async def add_money_handler_exception(message: types.Message) -> None:
    await message.answer(text=f"Извините, но это не похоже на число.\n "
                              f"Возможно дробное значение надо вводить через знак \".\"\n\n"
                              f"Но если вы передумали вы можете нажать на /menu и вернуться в меню")
