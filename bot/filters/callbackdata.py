from aiogram.filters.callback_data import CallbackData


class OffsetOfGameFactory(CallbackData, prefix="games"):
    offset: int = 0
