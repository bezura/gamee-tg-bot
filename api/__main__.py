import datetime
import json
import random
import secrets
from typing import List, Dict, Annotated

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.responses import JSONResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

from api.dependenciest import get_session
from api.responseSchemas import UserDataResponse, GameBaseResponse, GameResponse, PlayingGameResponse, \
    UserDataForGameResponse
from bot.database.models import UserModel, GameModel

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


rooms: Dict[str, PlayingGameResponse] = {}

websocket_lists: Dict[str, List[WebSocket]] = {}


@app.post(
    "/games/create-room"
)
async def get_games_endpoint(
        game_id: int = Body(...),
        bet: int = Body(...),
        count_players: int = Body(...),
        db_session: Session = Depends(get_session)
):
    def create_room_id(set_game_id: int):
        return f"{set_game_id}_{secrets.token_hex(5)}"

    stmt = select(GameModel).where(GameModel.id == game_id).limit(1)
    query = await db_session.execute(stmt)
    game: GameModel = query.scalar()
    if not (
            game and game.is_active and game.max_players
    ):
        return JSONResponse({"error": "Game not found or not active"}, status_code=403)

    if bet == 0:
        return JSONResponse({"error": "Bet cannot be zero"}, status_code=403)

    if count_players < 2:
        return JSONResponse({"error": "Number of players cannot be less than 2"}, status_code=403)

    if count_players > game.max_players:
        return JSONResponse({"error": f"Number of players cannot be less than {game.max_players}"}, status_code=403)

    room_id = create_room_id(set_game_id=game.id)
    rooms[room_id] = PlayingGameResponse(
        title=game.title,
        game_id=game.id,
        description=game.description,
        websocket_uri=game.websocket_uri,
        bet=bet,
        count_players=count_players
    )
    print("created", rooms[room_id])

    return JSONResponse({"redirect_to_room_uri": f"{game.front_uri}/{room_id}"}, status_code=200)


def check_valid_room(room_id: str):
    # print("all", rooms, rooms[room_id].game_id != room_id.split("_")[0])
    if (room_id not in rooms or rooms[room_id].game_id != int(room_id.split("_")[0]) or
            rooms[room_id].game_started or rooms[room_id].game_finished):
        raise HTTPException(status_code=404, detail='not valid room')


@app.get(
    "/games/get_room/{room_id}",
    dependencies=[Depends(check_valid_room)]
)
async def get_room_info_endpoint(
        room_id: str
):
    return rooms[room_id]


async def send_for_all_in_room(room_id: str, json: dict):
    for player in websocket_lists[room_id]:
        await player.send_json(json)


async def close_connections_all_in_room(room_id: str):
    for player in websocket_lists[room_id]:
        await player.close()
    websocket_lists[room_id] = []


@app.websocket("/connect/ticktacktoe/{room_id}/{user_id}", dependencies=[Depends(check_valid_room)])
async def connect_to_room_endpoint(
        room_id: str,
        user_id: int,
        websocket: WebSocket,
        db_session: Session = Depends(get_session)
):
    stmt = select(UserModel).where(UserModel.id == user_id).limit(1)
    query = await db_session.execute(stmt)
    user: UserModel = query.scalar()
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=400)

    try:
        await websocket.accept()
        # await websocket.send_json({"message": "Connected"})

        if room_id not in websocket_lists:
            websocket_lists[room_id] = [websocket]
        else:
            websocket_lists[room_id].append(websocket)

        if user_id not in rooms[room_id].connected_players:
            rooms[room_id].connected_players[user_id] = (
                UserDataForGameResponse(
                    avatar_url=user.avatar_url,
                    last_name=user.last_name,
                    first_name=user.first_name,
                    username=user.username,
                )
            )
            # await websocket.send_json({"message": "Waits other players"})
        else:
            rooms[room_id].connected_players[user_id].append(
                UserDataForGameResponse(
                    avatar_url=user.avatar_url,
                    last_name=user.last_name,
                    first_name=user.first_name,
                    username=user.username,
                )
            )

        await send_for_all_in_room(room_id, rooms[room_id].model_dump())
        while True:
            ready = await websocket.receive_text()
            if ready == "ready":
                rooms[room_id].connected_players[user_id].is_ready = True
                # await send_for_all_in_room(room_id, "User is ready")
                await send_for_all_in_room(room_id, rooms[room_id].model_dump())
            elif ready == "not_ready":
                rooms[room_id].connected_players[user_id].is_ready = False
                # await send_for_all_in_room(room_id, "User is not ready")
                await send_for_all_in_room(room_id, rooms[room_id].model_dump())
            if len(rooms[room_id].connected_players) == rooms[room_id].count_players:
                all_players_ready = True
                for connected_user in rooms[room_id].connected_players.values():
                    if not connected_user.is_ready:
                        all_players_ready = False
                        break
                if all_players_ready:
                    rooms[room_id].game_started = True
                    # await send_for_all_in_room(room_id, "Game started")
                    await send_for_all_in_room(room_id, rooms[room_id].model_dump())
                    break
        if rooms[room_id].current_player_id is None:
            rooms[room_id].current_player_id = random.choice(
                list(rooms[room_id].connected_players.keys()))

        if rooms[room_id].game_progress is None:
            rooms[room_id].game_progress = [[{"user_id": None, "checked_at": None} for _ in range(4)] for _ in range(4)]

        await send_for_all_in_room(room_id, rooms[room_id].model_dump())
        while True:
            for i in range(4):
                if rooms[room_id].game_progress[i][0]["user_id"] == rooms[room_id].game_progress[i][1]["user_id"] == \
                        rooms[room_id].game_progress[i][2]["user_id"] == \
                        rooms[room_id].game_progress[i][3]["user_id"] is not None:
                    rooms[room_id].winner_id = rooms[room_id].game_progress[i][0]["user_id"]
                    rooms[room_id].game_finished = True
                    break
                if rooms[room_id].game_progress[0][i]["user_id"] == rooms[room_id].game_progress[1][i]["user_id"] == \
                        rooms[room_id].game_progress[2][i]["user_id"] == \
                        rooms[room_id].game_progress[3][i]["user_id"] is not None:
                    rooms[room_id].winner_id = rooms[room_id].game_progress[0][i]["user_id"]
                    rooms[room_id].game_finished = True
                    break
                if rooms[room_id].game_progress[0][0]["user_id"] == rooms[room_id].game_progress[1][1]["user_id"] == \
                        rooms[room_id].game_progress[2][2]["user_id"] == \
                        rooms[room_id].game_progress[3][3]["user_id"] is not None:
                    rooms[room_id].winner_id = rooms[room_id].game_progress[0][0]["user_id"]
                    rooms[room_id].game_finished = True
                    break
                if rooms[room_id].game_progress[3][0]["user_id"] == rooms[room_id].game_progress[2][1]["user_id"] == \
                        rooms[room_id].game_progress[1][2]["user_id"] == \
                        rooms[room_id].game_progress[0][3]["user_id"] is not None:
                    rooms[room_id].winner_id = rooms[room_id].game_progress[3][0]["user_id"]
                    rooms[room_id].game_finished = True
                    break

            board_full = True
            for x in range(4):
                for y in range(4):
                    if rooms[room_id].game_progress[x][y]["user_id"] is None:
                        board_full = False
            if board_full:
                rooms[room_id].game_finished = True
                break

            if rooms[room_id].game_finished:
                break

            move = await websocket.receive_text()
            if rooms[room_id].current_player_id == user_id:
                x, y = map(int, move.split(','))
                if rooms[room_id].game_progress[x][y]["user_id"] is None:
                    rooms[room_id].game_progress[x][y]["user_id"] = user_id
                    rooms[room_id].game_progress[x][y]["checked_at"] = datetime.datetime.now().isoformat()

                    rooms[room_id].current_player_id = list(rooms[room_id].connected_players.keys())[0]

                    is_next_player = False
                    for connected_user_id in rooms[room_id].connected_players.keys():
                        if is_next_player:
                            rooms[room_id].current_player_id = connected_user_id
                            break
                        if connected_user_id == user_id:
                            is_next_player = True

                    await send_for_all_in_room(room_id, rooms[room_id].model_dump())

        if rooms[room_id].winner_id == user_id is not None and rooms[room_id].game_finished:
            stmt = select(UserModel).where(UserModel.id == user_id).limit(1)
            query = await db_session.execute(stmt)
            user: UserModel = query.scalar()
            user.money = user.money + rooms[room_id].bet
            await db_session.commit()

        if rooms[room_id].winner_id != user_id is not None and rooms[room_id].game_finished:
            stmt = select(UserModel).where(UserModel.id == user_id).limit(1)
            query = await db_session.execute(stmt)
            user: UserModel = query.scalar()
            user.money = user.money - rooms[room_id].bet
            await db_session.commit()

        await send_for_all_in_room(room_id, rooms[room_id].model_dump())
        await close_connections_all_in_room(room_id)

    except WebSocketDisconnect:
        websocket_lists[room_id].remove(websocket)
        await send_for_all_in_room(room_id, "Disconnected user")

        if len(rooms[room_id].connected_players) >= 2:
            stmt = select(UserModel).where(UserModel.id == user_id).limit(1)
            query = await db_session.execute(stmt)
            user: UserModel = query.scalar()
            user.money = user.money - rooms[room_id].bet
            await db_session.commit()

        if len(rooms[room_id].connected_players) == 2 and rooms[room_id].game_started and not (
                rooms[room_id].game_finished):
            del rooms[room_id].connected_players[user_id]
            rooms[room_id].winner_id = list(rooms[room_id].connected_players.keys())[0]
            rooms[room_id].game_finished = True
            await close_connections_all_in_room(room_id)

        elif rooms[room_id].game_started and not (
                rooms[room_id].game_finished) and rooms[room_id].current_player_id == user_id:
            rooms[room_id].current_player_id = list(rooms[room_id].connected_players.keys())[0]

            is_next_player = False
            for connected_user_id in rooms[room_id].connected_players.keys():
                if is_next_player:
                    rooms[room_id].current_player_id = connected_user_id
                    break
                if connected_user_id == user_id:
                    is_next_player = True

        del rooms[room_id].connected_players[user_id]

        await send_for_all_in_room(room_id, rooms[room_id].model_dump())

        # await send_for_all_in_room(room_id, "Game ended because user out "
        #                                     "and last user is win")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
