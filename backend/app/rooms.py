import random
import secrets
import string
import time
from threading import Lock

from impostor.game import Game

DEFAULT_ROUNDS_TO_WIN = 2
ROUND_RESULT_DISPLAY_SECONDS = 8


def _generate_code(length=5):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Room:
    """Una partida en curso. Sirve tanto para modo local (el host agrega
    a todos los jugadores) como para modo online (cada jugador se une
    con su propio nombre desde su dispositivo).

    Ciclo de una partida ya iniciada:
        lobby -> discuss -> vote -> round_result -> (discuss de nuevo | finished)

    El avance de fases es perezoso: no hay hilos en background. Cada vez
    que alguien consulta el estado (get_phase_state) se revisa si el tiempo
    de la fase actual venció y, si es así, se avanza a la fase siguiente.
    Todos los dispositivos calculan su cuenta regresiva en base al mismo
    phase_ends_at que devuelve el servidor, así queda sincronizado.
    """

    def __init__(self, code):
        self.code = code
        self.host_token = secrets.token_urlsafe(16)
        self.status = "lobby"  # "lobby" | "started" (compat con /rooms/{code})
        self.game = Game()
        self.word = None
        self.category = None
        self.player_tokens = {}  # player_id -> token
        self.player_objs = {}    # player_id -> Players
        self._id_counter = 0
        self._lock = Lock()

        # Estado de ronda / votación
        self.phase = "lobby"
        self.round_number = 0
        self.rounds_to_win = DEFAULT_ROUNDS_TO_WIN
        self.discuss_seconds = 60
        self.vote_seconds = 45
        self.phase_ends_at = None  # epoch seconds (float) o None
        self.alive_ids = []
        self.eliminated_ids = []
        self.votes = {}  # voter_player_id -> target_player_id
        self.last_round_result = None
        self.winner = None  # None | "crew" | "spies"

    # ------------------------------------------------------------------ #
    # Lobby
    # ------------------------------------------------------------------ #
    def add_player(self, name):
        with self._lock:
            if self.phase != "lobby":
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

    # ------------------------------------------------------------------ #
    # Arranque de partida
    # ------------------------------------------------------------------ #
    def start(self, host_token, num_spies, category_id, discuss_seconds, vote_seconds, rounds_to_win):
        if host_token != self.host_token:
            raise PermissionError("Token de host inválido")
        if self.phase != "lobby":
            raise ValueError("La partida ya inició")

        num_players = len(self.game.names)
        if num_players < 3:
            raise ValueError("Se necesitan al menos 3 jugadores")

        self.game.validate_num_spies(num_spies, num_players)

        # Solo se puede configurar la cantidad de rondas para ganar si hay
        # más de 6 jugadores. Con 6 o menos, siempre son 2 rondas.
        if num_players > 6 and rounds_to_win:
            self.rounds_to_win = max(1, int(rounds_to_win))
        else:
            self.rounds_to_win = DEFAULT_ROUNDS_TO_WIN

        self.discuss_seconds = max(10, int(discuss_seconds or 60))
        self.vote_seconds = max(10, int(vote_seconds or 45))

        self.game.connect_database()
        try:
            categories = self.game.get_category()
            if category_id is None:
                self.category = random.choice(categories)
            else:
                self.category = next((c for c in categories if c[0] == category_id), None)
                if self.category is None:
                    raise ValueError("Categoría inválida")
        finally:
            self.game.close_database()

        self.game.choose_spy()
        self.alive_ids = list(self.player_objs.keys())
        self.eliminated_ids = []
        self.round_number = 0
        self.winner = None
        self.status = "started"
        self._start_round()

    def _pick_word(self):
        self.game.connect_database()
        try:
            self.word = self.game.choose_word(self.category)
        finally:
            self.game.close_database()

    def _start_round(self):
        self.round_number += 1
        self._pick_word()
        self.votes = {}
        self.last_round_result = None
        self.phase = "vote"
        self.phase_ends_at = time.monotonic() + self.vote_seconds

    # ------------------------------------------------------------------ #
    # Avance de fases (perezoso, sin hilos en background)
    # ------------------------------------------------------------------ #
    def _advance_if_needed(self):
        with self._lock:
            if self.phase_ends_at is None:
                return
            if time.monotonic() < self.phase_ends_at:
                return

            if self.phase == "vote":
                self._tally_votes()

            elif self.phase == "round_result":
                if self.winner is not None:
                    self.phase = "finished"
                    self.phase_ends_at = None
                else:
                    self._start_round()

    def _tally_votes(self):
        tally = {}
        for target in self.votes.values():
            tally[target] = tally.get(target, 0) + 1

        eliminated_id = None
        if tally:
            max_votes = max(tally.values())
            top = [pid for pid, v in tally.items() if v == max_votes]
            if len(top) == 1:
                eliminated_id = top[0]

        was_spy = False
        eliminated_name = None
        if eliminated_id is not None:
            self.alive_ids.remove(eliminated_id)
            self.eliminated_ids.append(eliminated_id)
            player = self.player_objs[eliminated_id]
            was_spy = player.is_spy
            eliminated_name = player.name

        alive_spies = [pid for pid in self.alive_ids if self.player_objs[pid].is_spy]

        self.last_round_result = {
            "eliminated_id": eliminated_id,
            "eliminated_name": eliminated_name,
            "was_spy": was_spy,
            "word": self.word,
            "round_number": self.round_number,
        }

        if not alive_spies:
            self.winner = "crew"
        elif self.round_number >= self.rounds_to_win:
            self.winner = "spies"

        self.phase = "round_result"
        self.phase_ends_at = time.monotonic() + ROUND_RESULT_DISPLAY_SECONDS

    # ------------------------------------------------------------------ #
    # Votación
    # ------------------------------------------------------------------ #
    def submit_vote(self, player_id, player_token, target_id):
        self._advance_if_needed()
        with self._lock:
            stored = self.player_tokens.get(player_id)
            if stored is None or stored != player_token:
                raise PermissionError("Token de jugador inválido")
            if self.phase != "vote":
                raise ValueError("No es momento de votar")
            if player_id not in self.alive_ids:
                raise ValueError("Los jugadores eliminados no votan")
            if target_id not in self.alive_ids:
                raise ValueError("Solo se puede votar a jugadores vivos")
            if target_id == player_id:
                raise ValueError("No podés votarte a vos mismo")
            self.votes[player_id] = target_id
            if len(self.votes) >= len(self.alive_ids):
                self._tally_votes()

    def skip_phase(self, host_token):
            if host_token != self.host_token:
                raise PermissionError("Token de host inválido")
            if self.phase != "vote":
                raise ValueError("No hay nada para saltear ahora")
            self.phase_ends_at = time.monotonic()

    def begin_vote(self, host_token):
        if host_token != self.host_token:
            raise PermissionError("Token de host inválido")
        if self.phase != "discuss":
            raise ValueError("No se puede pasar a votación ahora")
        self.phase = "vote"
        self.phase_ends_at = time.monotonic() + self.vote_seconds        
    # ------------------------------------------------------------------ #
    # Consultas de estado
    # ------------------------------------------------------------------ #
    def get_phase_state(self):
        self._advance_if_needed()
        remaining = None
        if self.phase_ends_at is not None:
            remaining = max(0, round(self.phase_ends_at - time.monotonic()))
        return {
            "phase": self.phase,
            "round_number": self.round_number,
            "rounds_to_win": self.rounds_to_win,
            "phase_ends_at": self.phase_ends_at,
            "remaining_seconds": remaining,
            "winner": self.winner,
            "players": [
                {"player_id": pid, "name": p.name, "alive": pid in self.alive_ids}
                for pid, p in self.player_objs.items()
            ],
            "last_round_result": self.last_round_result,
        }

    def my_role(self, player_id, player_token):
        stored_token = self.player_tokens.get(player_id)
        if stored_token is None or stored_token != player_token:
            raise PermissionError("Token de jugador inválido")
        if self.phase == "lobby":
            raise ValueError("La partida todavía no inició")

        player = self.player_objs[player_id]
        if player.is_spy:
            return {"is_spy": True, "word": None}
        return {"is_spy": False, "word": self.word}

    # ------------------------------------------------------------------ #
    # Reinicio
    # ------------------------------------------------------------------ #
    def reset(self, host_token):
        if host_token != self.host_token:
            raise PermissionError("Token de host inválido")
        self.game.reset_roles()
        self.word = None
        self.category = None
        self.phase = "lobby"
        self.status = "lobby"
        self.round_number = 0
        self.alive_ids = []
        self.eliminated_ids = []
        self.votes = {}
        self.last_round_result = None
        self.winner = None
        self.phase_ends_at = None


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