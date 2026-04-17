"""
api/index.py — Kiosko Azul (Vercel Serverless Entry Point)

Este archivo es el punto de entrada para Vercel. 
Importa la app FastAPI principal desde el módulo raíz.

NOTA IMPORTANTE SOBRE VERCEL + PYTHON:
- Vercel soporta FastAPI via serverless functions con @vercel/python
- La base de datos SQLite (kioskoazul.db) NO es persistente en Vercel
  (el sistema de archivos es efímero). Para producción real se recomienda
  migrar a una base de datos externa: PostgreSQL (Neon, Supabase) o similar.
- Las variables de entorno se configuran en el Dashboard de Vercel o en .env
- El directorio de uploads de imágenes tampoco es persistente; 
  se recomienda usar Cloudinary, S3 o Vercel Blob Storage.
"""
import sys
import os

# Agregar el directorio raíz al path de Python para poder importar backend.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import app  # noqa: F401 - Vercel detecta la variable `app`

# Vercel busca una variable llamada `app` que sea una ASGI application
# FastAPI es compatible con ASGI, por lo que funciona directamente.
