import random

from impostor.models import Players
from impostor.database import get_connection


class Game:
    def __init__(self):
        self.num_players = 0
        self.names = []
        self.num_spies = 0
        self.cursor = None
        self.connection = None
        self.spies = []

    # ------------------------------------------------------------------ #
    # Base de datos
    # ------------------------------------------------------------------ #
    def connect_database(self):
        self.connection = get_connection()
        self.cursor = self.connection.cursor()

    def close_database(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def get_category(self):
        self.cursor.execute("SELECT DISTINCT id, name FROM categories ORDER BY name")
        return self.cursor.fetchall()

    def choose_word(self, selection):
        category_id = selection[0]
        self.cursor.execute(
            "SELECT word FROM words WHERE category_id = %s", (category_id,)
        )
        words = self.cursor.fetchall()

        if not words:
            raise ValueError(f"No hay palabras cargadas para la categoría {selection[1]!r}")

        return random.choice(words)[0]

    # ------------------------------------------------------------------ #
    # Configuracion de jugadores
    # ------------------------------------------------------------------ #
    def validate_num_players(self, num_players):
        if num_players < 3:
            raise ValueError("Debe haber al menos 3 jugadores")
        self.num_players = num_players
        return num_players

    def add_player(self, name):
        if name == "":
            raise ValueError("El nombre no puede estar vacío")

        if name in [p.name for p in self.names]:
            raise ValueError("El nombre no puede estar repetido")

        player = Players(name)
        self.names.append(player)
        return player

    # ------------------------------------------------------------------ #
    # Configuracion de espias
    # ------------------------------------------------------------------ #
    def max_spies(self, num_players):
        return num_players // 3

    def validate_num_spies(self, num_spies, num_players):
        if num_spies < 1:
            raise ValueError("Debe haber al menos 1 impostor")

        if num_spies > num_players:
            raise ValueError(
                "La cantidad de espías no puede ser mayor que la cantidad de jugadores"
            )

        max_allowed = self.max_spies(num_players)
        if num_spies > max_allowed:
            raise ValueError(
                f"La cantidad de impostores máxima para {num_players} jugadores es de {max_allowed}"
            )

        self.num_spies = num_spies
        return num_spies

    # ------------------------------------------------------------------ #
    # Roles
    # ------------------------------------------------------------------ #
    def reset_roles(self):
        for player in self.names:
            player.is_spy = False
        self.spies = []

    def choose_spy(self):
        self.reset_roles()
        self.spies = random.sample(self.names, self.num_spies)
        for player in self.spies:
            player.is_spy = True
        return self.spies

    # ------------------------------------------------------------------ #
    # Seleccion de categoria (logica pura, sin input/print)
    # ------------------------------------------------------------------ #
    def resolve_category_choice(self, choice, categories):
        """Dado un número elegido y la lista de categorías, devuelve la
        categoría seleccionada. La última opción (len(categories)+1)
        significa 'palabra aleatoria'."""
        random_option = len(categories) + 1

        if choice < 1 or choice > random_option:
            raise ValueError(f"Debe elegir una opción del 1 al {random_option}")

        if choice == random_option:
            return random.choice(categories)

        return categories[choice - 1]
