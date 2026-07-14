import os

from impostor.game import Game


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def starting():
    msj_error = ""
    while True:
        clear()
        print("IMPOSTOR")

        if msj_error:
            print(msj_error)
            msj_error = ""

        start = input("Empezamos? Y/N: ").upper()

        match start:
            case "N":
                print("Cerrando el juego")
                exit()
            case "Y":
                print("Comenzemos...")
                return
            case _:
                msj_error = "Error, seleccione Y or N"


def ask_num_players(game: Game):
    msj_error = ""
    while True:
        clear()
        print("CONFIGURACION DE JUGADORES")

        if msj_error:
            print(msj_error)
            msj_error = ""

        try:
            num_players = int(input("Numero de jugadores: "))
            return game.validate_num_players(num_players)
        except ValueError as err:
            msj_error = str(err) if "al menos" in str(err) else "La cantidad debe ser un número"


def ask_players_names(game: Game, num_players):
    game.names = []
    for i in range(num_players):
        while True:
            name = input(f"Nombre Jugador {i + 1}: ")
            try:
                game.add_player(name)
                break
            except ValueError as err:
                print(err)
    return game.names


def ask_num_spies(game: Game, num_players):
    max_spies = game.max_spies(num_players)
    msj_error = ""
    while True:
        clear()
        print("CONFIGURACION DE IMPOSTORES\n")

        if msj_error:
            print(msj_error)
            msj_error = ""

        try:
            num_spies = int(input("Con cuantos impostores quiere jugar?: "))
            return game.validate_num_spies(num_spies, num_players)
        except ValueError as err:
            msj_error = str(err) if any(
                s in str(err) for s in ("al menos", "mayor que", "máxima")
            ) else "La cantidad de espías debe ser un número"


def choose_category(game: Game):
    categories = game.get_category()
    msj_error = ""
    msj = ""

    while True:
        clear()
        print("\nELIGE UNA CATEGORIA\n")

        for i, category in enumerate(categories, start=1):
            print(f"{i}) {category[1]}")

        print(f"{len(categories) + 1}) Palabra aleatoria")

        if msj_error:
            print(msj_error)
            msj_error = ""
        if msj:
            print(msj)
            msj = ""

        try:
            choice = int(input("\nSeleccion: "))
            selection = game.resolve_category_choice(choice, categories)

            if choice == len(categories) + 1:
                msj = ' Seleccion: "Palabra aleatoria"'
            else:
                msj = f' Seleccion: "{selection[1].upper()}"\n'

            clear()
            print(msj)
            input("\nPresiona Enter para comenzar...")
            return selection

        except ValueError as err:
            msj_error = str(err) if "opción" in str(err) else (
                "Error, debe seleccionar el número correspondiente a la categoría elegida"
            )


def show_roles(game: Game, secret_word):
    for player in game.names:
        clear()
        input(f"Turno de {player.name}. Presiona Enter para ver tu rol...")

        if player.is_spy:
            print("SOS EL IMPOSTOR")
        else:
            print(f"La palabra es: {secret_word.upper()}")

        input("\nPresiona Enter para borrar la pantalla y pasar al siguiente...")
        clear()


def play_again():
    msj_error = ""
    while True:
        clear()

        if msj_error:
            print(msj_error)
            msj_error = ""

        start = input("¿Jugamos de nuevo? Y/N: ").upper()

        match start:
            case "N":
                print("Cerrando el juego...")
                return False
            case "Y":
                print("Comenzemos...")
                return True
            case _:
                msj_error = "Error, seleccione Y or N"


def main():
    game = Game()
    game.connect_database()

    try:
        playing = True
        while playing:
            game.reset_roles()

            starting()

            num_players = ask_num_players(game)
            ask_players_names(game, num_players)
            ask_num_spies(game, num_players)

            selection = choose_category(game)
            word = game.choose_word(selection)

            game.choose_spy()
            show_roles(game, word)

            playing = play_again()
    finally:
        game.close_database()


if __name__ == "__main__":
    main()
