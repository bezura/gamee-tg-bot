from aiogram import Router


def get_handlers_router() -> Router:
    from . import export_users, start

    router = Router()
    router.include_router(start.router)
    router.include_router(export_users.router)

    return router
