# 🚀 Deploy en Vercel — Kiosko Azul

## Requisitos previos
- Cuenta en [vercel.com](https://vercel.com)
- [Vercel CLI](https://vercel.com/docs/cli): `npm i -g vercel`
- Git con el repositorio vinculado (GitHub, GitLab o Bitbucket)

---

## ⚠️ Limitaciones importantes de Vercel + SQLite

> Vercel usa un sistema de archivos **efímero** (serverless). Esto significa que:
> - La base de datos SQLite (`kioskoazul.db`) **no persiste** entre requests.
> - Las imágenes subidas al servidor **se pierden** en cada deploy.

### Soluciones recomendadas para producción:

| Componente | Alternativa en la nube |
|---|---|
| SQLite → | [Neon PostgreSQL](https://neon.tech) (gratis) o [Supabase](https://supabase.com) |
| Imágenes → | [Cloudinary](https://cloudinary.com) o [Vercel Blob](https://vercel.com/docs/storage/vercel-blob) |
| WebSockets → | [Upstash](https://upstash.com) o [Ably](https://ably.com) |

---

## 📦 Variables de entorno (configurar en Vercel Dashboard)

En **Vercel → Project Settings → Environment Variables**, agrega:

```
SECRET_KEY=tu-clave-secreta-muy-segura-aqui
TOKEN_HOURS=24
ALLOWED_ORIGINS=https://tu-dominio.vercel.app,https://tu-dominio-personalizado.com
TELEGRAM_BOT_TOKEN=tu-token-de-telegram
TELEGRAM_CHAT_ID=tu-chat-id
SMTP_EMAIL=tu-correo@gmail.com
SMTP_PASSWORD=tu-app-password-gmail
DATABASE_URL=postgresql://usuario:password@host/dbname  (si migras a PostgreSQL)
```

---

## 🛠️ Pasos para hacer el deploy

### Opción 1: Deploy con Vercel CLI (recomendado)

```bash
# 1. Instalar Vercel CLI
npm i -g vercel

# 2. Dentro del directorio del proyecto
cd kioskoazul

# 3. Login en Vercel
vercel login

# 4. Deploy de prueba (preview)
vercel

# 5. Deploy a producción
vercel --prod
```

### Opción 2: Deploy desde GitHub (automático)

1. Sube el proyecto a GitHub (repositorio privado recomendado)
2. Ve a [vercel.com/new](https://vercel.com/new)
3. Importa el repositorio de GitHub
4. Vercel detecta automáticamente el `vercel.json`
5. Configura las variables de entorno
6. Haz clic en **Deploy**

---

## 📁 Estructura del proyecto (Vercel)

```
kioskoazul/
├── api/
│   └── index.py          ← Punto de entrada FastAPI para Vercel
├── site/
│   └── public/           ← Archivos estáticos (HTML, CSS, JS)
│       ├── index.html
│       ├── menu.html
│       └── ...
├── backend.py            ← API FastAPI principal
├── database.py           ← Modelos SQLAlchemy
├── requirements.txt      ← Dependencias Python
├── vercel.json           ← Configuración de rutas Vercel
└── .vercelignore         ← Archivos a excluir del deploy
```

---

## 🔍 Verificar el deploy

Después del deploy, revisa:
- `https://tu-app.vercel.app/` → Página principal
- `https://tu-app.vercel.app/menu.html` → Menú
- `https://tu-app.vercel.app/api/menu` → API (debería devolver JSON)
- `https://tu-app.vercel.app/api/categorias` → Categorías

---

## 💡 Tip: Dominio personalizado

En **Vercel → Project → Domains**, puedes agregar tu dominio personalizado (ej: `kioskoazul.com`) gratuitamente con SSL automático.
