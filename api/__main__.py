import datetime
import json
from typing import List

import uvicorn
from fastapi import FastAPI, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

from bot.api.dependenciest import get_session
from bot.api.responseSchemas import UserDataResponse, GameBaseResponse, GameResponse
from bot.database.models import UserModel, GameModel
from bot.enums.game_types import GameType

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # can alter with time
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/user/{user_id}",
    response_model=UserDataResponse,
)
async def get_user_data_endpoint(
        user_id: int,
        db_session: Session = Depends(get_session)
):
    stmt = select(UserModel).where(UserModel.id == user_id).limit(1)
    query = await db_session.execute(stmt)
    user: UserModel = query.scalar()
    return user


@app.get(
    "/games",
    response_model=list[GameBaseResponse],
)
async def get_games_endpoint(
        db_session: Session = Depends(get_session)
):
    stmt = select(GameModel).where(GameModel.is_active.is_(True)).order_by(GameModel.id.desc())
    query = await db_session.execute(stmt)
    games = query.scalars()
    return games


@app.get(
    "/games/{game_id}",
    response_model=GameResponse,
)
async def get_games_endpoint(
        game_id: int,
        db_session: Session = Depends(get_session)
):
    stmt = select(GameModel).where(GameModel.id == game_id).limit(1)
    query = await db_session.execute(stmt)
    game = query.scalar()
    return game


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket)
    now = datetime.datetime.now()
    current_time = now.strftime("%H:%M")
    try:
        while True:
            data = await websocket.receive_text()
            # await manager.send_personal_message(f"You wrote: {data}", websocket)
            message = {"time": current_time, "userId": user_id, "message": data}
            await manager.broadcast(json.dumps(message))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        message = {"time": current_time, "userId": user_id, "message": "Offline"}
        await manager.broadcast(json.dumps(message))


# @app.post("/games/{game_id}/create-session")
# async def start_game_endpoint(
#         game_id: int,
#         db_session: Session = Depends(get_session)
# ):
#     stmt = select(GameModel).where(GameModel.id == game_id).limit(1)
#     query = db_session.execute(stmt)
#     game = query.scalar()
#     if game.game_type == GameType.tick_tack_toe:
#         return JSONResponse({"success": "Game Tick-Tac-Toe started"}, status_code=200)
#
#     return JSONResponse({"error": "Type of game not founded"}, status_code=402)


@app.websocket("/ws/room/{user_id}")
async def game_room_websocket_endpoint(
        websocket: WebSocket,
        user_id: int
):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # await manager.send_personal_message(f"You wrote: {data}", websocket)
            message = {
                "userId": user_id,
                "message": data
            }
            await manager.broadcast(json.dumps(message))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        message = {"userId": user_id, "message": "Disconnected"}
        await manager.broadcast(json.dumps(message))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8087)
