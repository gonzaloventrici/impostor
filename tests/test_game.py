import pytest

from impostor import Game, Players


@pytest.fixture
def game_instance():
    """Crea una instancia limpia de Game para cada test."""
    g = Game()
    g.names = [Players("A"), Players("B"), Players("C"), Players("D")]
    g.num_players = 4
    g.num_spies = 1
    return g


@pytest.fixture
def db_session(game_instance):
    """Fixture con yield para manejar la conexión a la DB."""
    game_instance.connect_database()
    yield game_instance
    game_instance.close_database()


# --- TESTS DE LÓGICA (no requieren DB) ------------------------------------ #

def test_validar_nombre_repetido(game_instance):
    with pytest.raises(ValueError, match="repetido"):
        game_instance.add_player("A")


def test_validar_nombre_vacio(game_instance):
    with pytest.raises(ValueError, match="vacío"):
        game_instance.add_player("")


def test_validar_nombre_valido(game_instance):
    player = game_instance.add_player("Z")
    assert player.name == "Z"
    assert "Z" in [p.name for p in game_instance.names]


def test_rol_inicial_falso():
    p = Players("Nico")
    assert p.is_spy is False


def test_asignacion_impostores(game_instance):
    spies = game_instance.choose_spy()
    assert len(spies) == game_instance.num_spies

    spies_en_lista = [p for p in game_instance.names if p.is_spy]
    assert len(spies_en_lista) == game_instance.num_spies


@pytest.mark.parametrize("jugadores, espias_esperados", [
    (3, 1),  # 3 // 3 = 1
    (5, 1),  # 5 // 3 = 1
    (6, 2),  # 6 // 3 = 2
    (9, 3),  # 9 // 3 = 3
])
def test_proporcion_espias_variable(game_instance, jugadores, espias_esperados):
    assert game_instance.max_spies(jugadores) == espias_esperados


def test_limite_maximo_impostores(game_instance):
    # Para 4 jugadores, 4 // 3 debe ser 1
    assert game_instance.max_spies(game_instance.num_players) == 1


def test_validar_num_spies_excede_maximo(game_instance):
    with pytest.raises(ValueError, match="máxima"):
        game_instance.validate_num_spies(2, 4)  # max_spies(4) == 1


def test_validar_num_spies_mayor_a_jugadores(game_instance):
    with pytest.raises(ValueError, match="mayor que"):
        game_instance.validate_num_spies(10, 4)


def test_validar_num_spies_menor_a_uno(game_instance):
    with pytest.raises(ValueError, match="al menos 1"):
        game_instance.validate_num_spies(0, 4)


def test_reinicio_de_roles(game_instance):
    """Verifica que correr choose_spy dos veces no acumule espías."""
    game_instance.choose_spy()
    spies = game_instance.choose_spy()  # reset_roles() se llama internamente

    assert len(spies) == 1
    assert sum(1 for p in game_instance.names if p.is_spy) == 1


def test_resolve_category_choice_random():
    game = Game()
    categorias = [(1, "Lugar"), (2, "Animal")]
    seleccion = game.resolve_category_choice(3, categorias)  # opción "aleatoria"
    assert seleccion in categorias


def test_resolve_category_choice_fuera_de_rango():
    game = Game()
    categorias = [(1, "Lugar"), (2, "Animal")]
    with pytest.raises(ValueError, match="opción"):
        game.resolve_category_choice(5, categorias)


# --- TESTS DE BASE DE DATOS (requieren conexión) --------------------------- #

def test_conexion_db_exitosa(db_session):
    assert db_session.connection is not None
    assert db_session.connection.is_connected()


def test_obtener_categorias_no_vacio(db_session):
    categorias = db_session.get_category()
    assert isinstance(categorias, list)
    assert len(categorias) > 0


def test_palabra_secreta_valida(db_session):
    categorias = db_session.get_category()
    categoria = categorias[0]  # usamos una categoría real de la DB
    palabra = db_session.choose_word(categoria)
    assert isinstance(palabra, str)
    assert len(palabra) > 0
