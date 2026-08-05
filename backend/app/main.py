from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from impostor.game import Game
from app.rooms import room_manager
from app.schemas import (
    CreateRoomResponse, JoinRoomRequest, JoinRoomResponse, RoomStateResponse,
    StartGameRequest, CategoryOut, MyRoleResponse, VoteRequest,
)

app = FastAPI(title="Impostor API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/categories", response_model=list[CategoryOut])
def list_categories():
    game = Game()
    game.connect_database()
    try:
        categories = game.get_category()
    finally:
        game.close_database()
    return [{"id": c[0], "name": c[1]} for c in categories]


@app.post("/rooms", response_model=CreateRoomResponse)
def create_room():
    room = room_manager.create_room()
    return {"room_code": room.code, "host_token": room.host_token}


@app.post("/rooms/{code}/join", response_model=JoinRoomResponse)
def join_room(code: str, body: JoinRoomRequest):
    try:
        room = room_manager.get_room(code)
        player_id, token = room.add_player(body.name)
    except KeyError:
        raise HTTPException(404, "Sala no encontrada")
    except ValueError as err:
        raise HTTPException(400, str(err))
    return {"player_id": player_id, "player_token": token}


@app.get("/rooms/{code}", response_model=RoomStateResponse)
def room_state(code: str):
    try:
        room = room_manager.get_room(code)
    except KeyError:
        raise HTTPException(404, "Sala no encontrada")
    return {"room_code": room.code, "status": room.status, "players": room.players_public()}


@app.post("/rooms/{code}/start")
def start_room(code: str, body: StartGameRequest):
    try:
        room = room_manager.get_room(code)
        room.start(body.host_token, body.num_spies, body.category_id,
                   body.discuss_seconds, body.vote_seconds, body.rounds_to_win)
    except KeyError:
        raise HTTPException(404, "Sala no encontrada")
    except PermissionError as err:
        raise HTTPException(403, str(err))
    except ValueError as err:
        raise HTTPException(400, str(err))
    return {"status": "started"}


@app.get("/rooms/{code}/players/{player_id}/role", response_model=MyRoleResponse)
def my_role(code: str, player_id: str, player_token: str):
    try:
        room = room_manager.get_room(code)
        return room.my_role(player_id, player_token)
    except KeyError:
        raise HTTPException(404, "Sala o jugador no encontrado")
    except PermissionError as err:
        raise HTTPException(403, str(err))
    except ValueError as err:
        raise HTTPException(400, str(err))


@app.get("/rooms/{code}/phase")
def get_phase(code: str):
    try:
        room = room_manager.get_room(code)
        return room.get_phase_state()
    except KeyError:
        raise HTTPException(404, "Sala no encontrada")


@app.post("/rooms/{code}/vote")
def submit_vote(code: str, body: VoteRequest):
    try:
        room = room_manager.get_room(code)
        room.submit_vote(body.player_id, body.player_token, body.target_id)
    except KeyError:
        raise HTTPException(404, "Sala no encontrada")
    except PermissionError as err:
        raise HTTPException(403, str(err))
    except ValueError as err:
        raise HTTPException(400, str(err))
    return {"status": "ok"}


@app.post("/rooms/{code}/reset")
def reset_room(code: str, host_token: str):
    try:
        room = room_manager.get_room(code)
        room.reset(host_token)
    except KeyError:
        raise HTTPException(404, "Sala no encontrada")
    except PermissionError as err:
        raise HTTPException(403, str(err))
    return {"status": "lobby"}


# Servimos el frontend directamente desde el backend, en el mismo puerto.
# Esto evita que el navegador trate front y back como "orígenes" distintos
# (algo que iOS bloquea de forma silenciosa entre puertos en la red local).
# IMPORTANTE: este mount va al final, después de todas las rutas de la API,
# para que /categories, /rooms, etc. sigan resolviendo antes que esto.
_frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")