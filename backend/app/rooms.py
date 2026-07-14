import random
import secrets
import string
from threading import Lock

from impostor.game import Game


def _generate_code(length=5):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Room:
    """Una partida en curso. Sirve tanto para modo local (el host agrega
    a todos los jugadores) como para modo online (cada jugador se une
    con su propio nombre desde su dispositivo)."""

    def __init__(self, code):
        self.code = code
        self.host_token = secrets.token_urlsafe(16)
        self.status = "lobby"  # "lobby" | "started"
        self.game = Game()
        self.word = None
        self.player_tokens = {}  # player_id -> token
        self.player_objs = {}    # player_id -> Players
        self._id_counter = 0
        self._lock = Lock()

    def add_player(self, name):
        with self._lock:
            if self.status != "lobby":
                raise ValueError("La sala ya inició la partida")

            player = self.game.add_player(name)  # valida vacío/repetido

            self._id_counter += 1
            player_id = str(self._id_counter)
            token = secrets.token_urlsafe(16)
            self.player_tokens[player_id] = token
            self.player_objs[player_id] = player
            return player_id, token

    def players_public(self):
        return [{"player_id": pid, "name": p.name} for pid, p in self.player_objs.items()]

    def start(self, host_token, num_spies, category_id):
        if host_token != self.host_token:
            raise PermissionError("Token de host inválido")
        if self.status != "lobby":
            raise ValueError("La partida ya inició")
        if len(self.game.names) < 3:
            raise ValueError("Se necesitan al menos 3 jugadores")

        self.game.validate_num_spies(num_spies, len(self.game.names))

        self.game.connect_database()
        try:
            categories = self.game.get_category()
            if category_id is None:
                selection = random.choice(categories)
            else:
                selection = next((c for c in categories if c[0] == category_id), None)
                if selection is None:
                    raise ValueError("Categoría inválida")
            self.word = self.game.choose_word(selection)
        finally:
            self.game.close_database()

        self.game.choose_spy()
        self.status = "started"

    def my_role(self, player_id, player_token):
        stored_token = self.player_tokens.get(player_id)
        if stored_token is None or stored_token != player_token:
            raise PermissionError("Token de jugador inválido")
        if self.status != "started":
            raise ValueError("La partida todavía no inició")

        player = self.player_objs[player_id]
        if player.is_spy:
            return {"is_spy": True, "word": None}
        return {"is_spy": False, "word": self.word}

    def reset(self, host_token):
        if host_token != self.host_token:
            raise PermissionError("Token de host inválido")
        self.game.reset_roles()
        self.word = None
        self.status = "lobby"


class RoomManager:
    def __init__(self):
        self._rooms = {}
        self._lock = Lock()

    def create_room(self):
        with self._lock:
            code = _generate_code()
            while code in self._rooms:
                code = _generate_code()
            room = Room(code)
            self._rooms[code] = room
            return room

    def get_room(self, code):
        room = self._rooms.get(code.upper())
        if room is None:
            raise KeyError("Sala no encontrada")
        return room


room_manager = RoomManager()
