import datetime
import json
from typing import List, Dict

import uvicorn
from fastapi import FastAPI, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.responses import JSONResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

from api.dependenciest import get_session
from api.responseSchemas import UserDataResponse, GameBaseResponse, GameResponse
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


# class ConnectionManager:
#     def __init__(self):
#         self.active_connections: List[WebSocket] = []
#
#     async def connect(self, websocket: WebSocket):
#         await websocket.accept()
#         self.active_connections.append(websocket)
#
#     def disconnect(self, websocket: WebSocket):
#         self.active_connections.remove(websocket)
#
#     async def send_personal_message(self, message: str, websocket: WebSocket):
#         await websocket.send_text(message)
#
#     async def broadcast(self, message: str):
#         for connection in self.active_connections:
#             await connection.send_text(message)
#
#
# manager = ConnectionManager()
#
#
# @app.websocket("/ws/{user_id}")
# async def websocket_endpoint(websocket: WebSocket, user_id: int):
#     await manager.connect(websocket)
#     now = datetime.datetime.now()
#     current_time = now.strftime("%H:%M")
#     try:
#         while True:
#             data = await websocket.receive_text()
#             # await manager.send_personal_message(f"You wrote: {data}", websocket)
#             message = {"time": current_time, "userId": user_id, "message": data}
#             await manager.broadcast(json.dumps(message))
#
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         message = {"time": current_time, "userId": user_id, "message": "Offline"}
#         await manager.broadcast(json.dumps(message))
#
#
# # @app.post("/games/{game_id}/create-session")
# # async def start_game_endpoint(
# #         game_id: int,
# #         db_session: Session = Depends(get_session)
# # ):
# #     stmt = select(GameModel).where(GameModel.id == game_id).limit(1)
# #     query = db_session.execute(stmt)
# #     game = query.scalar()
# #     if game.game_type == GameType.tick_tack_toe:
# #         return JSONResponse({"success": "Game Tick-Tac-Toe started"}, status_code=200)
# #
# #     return JSONResponse({"error": "Type of game not founded"}, status_code=402)
#
#
# @app.websocket("/ws/room/{user_id}")
# async def game_room_websocket_endpoint(
#         websocket: WebSocket,
#         user_id: int
# ):
#     await manager.connect(websocket)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             # await manager.send_personal_message(f"You wrote: {data}", websocket)
#             message = {
#                 "userId": user_id,
#                 "message": data
#             }
#             await manager.broadcast(json.dumps(message))
#
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         message = {"userId": user_id, "message": "Disconnected"}
#         await manager.broadcast(json.dumps(message))

# Словарь для хранения текущих игровых комнат
rooms: Dict[str, List[WebSocket]] = {}

# Словарь для отслеживания готовности игроков в комнатах
ready_players: Dict[str, List[str]] = {}


@app.websocket("/ws/{room_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player_id: str):
    # Подключаем игрока к комнате
    await websocket.accept()
    await websocket.send_json({"message": "Connected"})

    # Добавляем игрока в соответствующую комнату
    if room_id not in rooms:
        rooms[room_id] = [websocket]
        ready_players[room_id] = []
    else:
        rooms[room_id].append(websocket)

    # Ожидание готовности игрока
    await websocket.send_json({"message": "Press ready when you are ready to play"})
    ready = await websocket.receive_text()
    if ready == "ready":
        ready_players[room_id].append(player_id)
        await websocket.send_json({"message": "Waiting for other player to be ready"})
    else:
        await websocket.send_json({"message": "You need to press ready to start the game"})

    # Если в комнате достаточно игроков и они оба готовы, начинаем игру
    if len(rooms[room_id]) == 2 and len(ready_players[room_id]) == 2:
        await start_game(room_id)


async def start_game(room_id: str):
    # Логика начала игры, инициализация поля и игрового состояния
    board = [[' ' for _ in range(4)] for _ in range(4)]
    current_player = 0  # Индекс текущего игрока в списке комнаты

    # Отправляем сообщение о начале игры всем игрокам в комнате
    for player in rooms[room_id]:
        await player.send_json({"message": "Game started"})

    # Отправляем игрокам начальное состояние игры (пустое поле)
    for player in rooms[room_id]:
        await player.send_json({"board": board})

    # Ожидаем и обрабатываем ходы игроков до завершения игры
    while True:
        winner = check_winner(board)
        if winner:
            for player in rooms[room_id]:
                await player.send_json({"message": f"Game over! Winner is {winner}"})
            break  # Завершаем игру
        # Получаем ход от текущего игрока
        player = rooms[room_id][current_player]
        move = await player.receive_text()
        # Обновляем игровое поле с учетом хода
        row, col = map(int, move.split(','))
        if board[row][col] == ' ':
            board[row][col] = 'X' if current_player == 0 else 'O'
            current_player = 1 - current_player  # Переключаем игрока
            # Отправляем обновленное состояние игры обоим игрокам
            for player in rooms[room_id]:
                await player.send_json({"board": board})
        else:
            await player.send_json({"message": "Invalid move"})


def check_winner(board: List[List[str]]) -> str:
    # Проверяем строки, столбцы и диагонали на наличие победителя
    for i in range(4):
        # Проверка строк
        if board[i][0] == board[i][1] == board[i][2] == board[i][3] != ' ':
            return board[i][0]
        # Проверка столбцов
        if board[0][i] == board[1][i] == board[2][i] == board[3][i] != ' ':
            return board[0][i]
    # Проверка главной диагонали
    if board[0][0] == board[1][1] == board[2][2] == board[3][3] != ' ':
        return board[0][0]
    # Проверка побочной диагонали
    if board[0][3] == board[1][2] == board[2][1] == board[3][0] != ' ':
        return board[0][3]
    # Если никто не победил
    return None


if __name__ == "__main__":
    uvicorn.run(app, host="192.168.5.253", port=443,
                ssl_keyfile="./localhost+2-key.pem",
                ssl_certfile="./localhost+2.pem")
    #на проде можно вручную впечатьать, todo вынести в env
