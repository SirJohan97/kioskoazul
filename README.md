# Kiosko Azul

Plataforma de comercio electrónico para restaurante de cocina costera.

## Requisitos

```
fastapi
uvicorn
sqlalchemy
python-jose
passlib
python-multipart
requests
python-dotenv
websockets
```

## Instalación

```bash
# Crear entorno virtual
python -m venv venv

# Activar (Windows)
.\venv\Scripts\Activate

# Instalar dependencias
pip install fastapi uvicorn sqlalchemy python-jose passlib python-multipart requests python-dotenv websockets

# Copiar variables de entorno
copy .env.example .env
```

## Ejecución

```bash
.\start.bat
```

El servidor corre en `http://localhost:3000`

## Estructura

- `backend.py` - API FastAPI
- `database.py` - Modelos SQLAlchemy
- `site/public/` - Frontend estático
- `.env.example` - Variables de entorno

## Credenciales Admin

- Usuario: `admin`
- Contraseña: `kioskoazul2025`

## Endpoints

- Frontend: `http://localhost:3000`
- Menu: `http://localhost:3000/menu.html`
- Admin: `http://localhost:3000/admin-login.html`
- API Docs: `http://localhost:3000/docs`
- Sitemap: `http://localhost:3000/sitemap.xml`