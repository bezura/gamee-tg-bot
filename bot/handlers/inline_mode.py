from typing import Optional

from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, LinkPreviewOptions
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.games import get_inline_games

router = Router(name="inline_mode")


@router.inline_query()
async def show_games(inline_query: InlineQuery, session: AsyncSession):
    def get_message_text(
            title: str,
            description: Optional[str]
    ) -> str:
        response_parts = [f'<b><i>{title}</i></b>']
        if description:
            response_parts.append(f"<i>{description}</i>")

        return "\n".join(response_parts)

    games = await get_inline_games(session=session, inline_query=inline_query.query)
    results = []
    for game in games:
        results.append(InlineQueryResultArticle(
            id=str(game.id),
            title=game.title,
            description=game.description,
            thumbnail_url=game.thumbnail_url or "https://docs.python-telegram-bot.org/en/"
                                                "v13.10/_static/ptb-logo-orange.png",
            input_message_content=InputTextMessageContent(
                message_text=get_message_text(
                    title=game.title,
                    description=game.description
                ),
                link_preview_options=LinkPreviewOptions(
                    is_disabled=False,
                    url=game.thumbnail_url or "https://docs.python-telegram-bot.org/en/"
                                              "v13.10/_static/ptb-logo-orange.png",
                    show_above_text=False,
                    prefer_large_media=True
                ),
                parse_mode="HTML"
            )
        )
        )
    return await inline_query.answer(results, is_personal=True, cache_time=1,)
