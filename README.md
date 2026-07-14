# Impostor

Juego de deducción social. Uno de los jugadores no sabe la palabra secreta y
tiene que disimular. Soporta dos modos:

- **Local**: un solo dispositivo se pasa entre jugadores.
- **Online**: cada jugador entra desde su propio celular/PC con un código de sala.

## Estructura

```
impostor_game/
├── src/impostor/       # Lógica del juego (paquete Python)
├── backend/            # API FastAPI (salas, roles, conexión a MySQL)
├── frontend/           # Página web (HTML/JS, sin build tooling)
├── sql/database.sql    # Schema + datos de categorías/palabras
├── tests/              # Tests de la lógica del juego
└── main.py             # Versión de consola original (sigue funcionando)
```

## 1. Base de datos

Si todavía no la creaste:

```bash
mysql -u root -p < sql/database.sql
```

## 2. Backend

```bash
python3 -m venv venv
source venv/bin/activate        # en Windows: venv\Scripts\activate

pip install -r requirements.txt
pip install -r backend/requirements.txt
pip install -e .                # instala el paquete "impostor" en modo editable

cp .env.example .env             # completar con tus credenciales reales de MySQL

cd backend
uvicorn app.main:app --reload --port 8000
```

Verificá que anduvo entrando a `http://localhost:8000/docs` (documentación
interactiva autogenerada por FastAPI).

## 3. Frontend

Con el backend corriendo, simplemente abrí `frontend/index.html` en el
navegador (doble clic, o "Abrir con" tu navegador). No necesita build ni
servidor propio.

Si el backend corre en otra IP (por ejemplo, para que otro jugador se conecte
desde su celular en la misma red Wi-Fi), cambiá esta línea en
`frontend/index.html`:

```js
const API_BASE = "http://localhost:8000";
```

por la IP de tu máquina, ej. `http://192.168.0.15:8000`. Además hay que correr
uvicorn con `--host 0.0.0.0` para que escuche en la red local:

```bash
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
```

## 4. Consola (versión original)

Sigue disponible si preferís jugar sin frontend:

```bash
python main.py
```

## Tests

```bash
pytest
```

Los tests que no requieren base de datos (16 de 19) corren siempre. Los que
sí la requieren necesitan la variable `.env` configurada y la DB accesible.
