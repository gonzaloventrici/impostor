class Players:
    """Representa a un jugador de la partida."""

    def __init__(self, name):
        self.name = name
        self.is_spy = False

    def __repr__(self):
        # Hace que se muestre el nombre automaticamente al llamarlo
        return self.name
