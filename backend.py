"""
backend.py — Kiosko Azul
API FastAPI con autenticación JWT, CRUD de menú, promociones, pedidos e imágenes.
"""
import os
import shutil
from datetime import datetime, timedelta
from typing import Optional, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string

from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
import asyncio
import concurrent.futures

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import (
    get_db, create_tables,
    Admin, Cliente, Categoria, MenuItem, Promocion, PromocionItem,
    Pedido, PedidoItem, AuditLog, DeliveryZona, Direccion, PwdReset
)

# ─────────────────────────────────────────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────────────────────────────────────────
SECRET_KEY  = os.environ.get("SECRET_KEY", "kioskoazul-secret-2025-xK9mPqR")
ALGORITHM   = "HS256"
TOKEN_HOURS = 24

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8741738690:AAG_ONxfjhzIQ6NA0RrzMJ9AhW61_cdA-wY")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "6526066600")

SMTP_EMAIL    = os.environ.get("SMTP_EMAIL", "tucorreo@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "tu-app-password")

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "site", "public", "assets", "menu")
os.makedirs(UPLOAD_DIR, exist_ok=True)

pwd_ctx = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

app = FastAPI(title="Kiosko Azul API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear tablas al arrancar
create_tables()


# ─────────────────────────────────────────────────────────────────────────────
# Schemas Pydantic
# ─────────────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type:   str
    admin:        dict

class CategoriaOut(BaseModel):
    id: int; nombre: str; emoji: str; slug: str; orden: int; activa: bool
    class Config: from_attributes = True

class MenuItemIn(BaseModel):
    nombre:      str
    descripcion: Optional[str] = None
    precio_usd:  float
    imagen_url:  Optional[str] = None
    badge:       Optional[str] = None
    categoria_id: int
    activo:      bool = True
    destacado:   bool = False

class MenuItemOut(BaseModel):
    id: int; nombre: str; descripcion: Optional[str]; precio_usd: float
    imagen_url: Optional[str]; badge: Optional[str]; activo: bool
    destacado: bool; categoria_id: int; categoria: Optional[CategoriaOut]
    class Config: from_attributes = True

class PromocionIn(BaseModel):
    nombre:       str
    descripcion:  Optional[str] = None
    tipo:         str = "porcentaje"
    valor:        float
    aplica_a:     str = "item"
    categoria_id: Optional[int] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin:    Optional[datetime] = None
    activa:       bool = True
    item_ids:     List[int] = []
    precio_original: Optional[float] = None
    precio_final: Optional[float] = None

class PromocionOut(BaseModel):
    id: int; nombre: str; descripcion: Optional[str]; tipo: str; valor: float
    aplica_a: str; categoria_id: Optional[int]; fecha_inicio: Optional[datetime]
    fecha_fin: Optional[datetime]; activa: bool
    precio_original: Optional[float] = None
    precio_final: Optional[float] = None
    class Config: from_attributes = True

class CartItem(BaseModel):
    name:  str
    price: float
    qty:   int

class OrderRequest(BaseModel):
    customer_name:  str
    customer_phone: str
    payment_method: str
    payment_ref:    str
    tipo_entrega:   str = "pickup"
    items:          List[CartItem]
    total:          float
    tasa_bcv:       Optional[float] = None
    crear_cuenta:   bool = False
    correo:         Optional[str] = None
    direccion:      Optional[str] = None
    zona_id:        Optional[int] = None
    password:       Optional[str] = None

class ZonaIn(BaseModel):
    nombre: str
    precio: float

class ZonaOut(ZonaIn):
    id: int
    activa: bool
    class Config: from_attributes = True

class PedidoEstadoIn(BaseModel):
    estado: str   # pendiente | preparando | listo | entregado | cancelado

class BatchPrecioIn(BaseModel):
    categoria_id:   Optional[int] = None
    porcentaje:     float   # positivo = aumento, negativo = descuento

class ClienteRegistroIn(BaseModel):
    nombre: str
    telefono: str
    password: str
    correo: Optional[str] = None
    direccion: Optional[str] = None

class ClienteLoginIn(BaseModel):
    telefono: str
    password: str

class ClienteOut(BaseModel):
    id: int; nombre: str; telefono: str
    correo: Optional[str]; direccion: Optional[str]
    class Config: from_attributes = True

class DireccionIn(BaseModel):
    alias: str
    direccion_texto: str

class DireccionOut(DireccionIn):
    id: int
    class Config: from_attributes = True

class RecuperarInfo(BaseModel):
    correo: str

class ResetInfo(BaseModel):
    correo: str
    codigo: str
    nueva_password: str


# ─────────────────────────────────────────────────────────────────────────────
# Auth helpers
# ─────────────────────────────────────────────────────────────────────────────

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=TOKEN_HOURS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def send_recovery_email(destinatario: str, codigo: str):
    if SMTP_EMAIL == "tucorreo@gmail.com":
        print(f"⚠️ SIMULACIÓN SMTP: Código enviado a {destinatario} -> {codigo}")
        return
        
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = destinatario
        msg['Subject'] = "Kiosko Azul - Código de Recuperación"
        
        body = f"Hola,\n\nHas solicitado recuperar tu contraseña.\nTu código es: {codigo}\n\nEs válido por 15 minutos. Si no fuiste tú, ignora este correo."
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✉️ Correo de recuperación enviado a {destinatario}")
    except Exception as e:
        print(f"❌ Error SMTP enviando correo a {destinatario}: {e}")

def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Admin:
    cred_exc = HTTPException(status_code=401, detail="Token inválido o expirado",
                             headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise cred_exc
    except JWTError:
        raise cred_exc
    admin = db.query(Admin).filter_by(username=username, activo=True).first()
    if not admin:
        raise cred_exc
    return admin

def log_action(db: Session, admin_id: int, accion: str, tabla: str,
               registro_id: int = None, detalle: dict = None):
    db.add(AuditLog(admin_id=admin_id, accion=accion, tabla=tabla,
                    registro_id=registro_id, detalle=detalle))


# ─────────────────────────────────────────────────────────────────────────────
# Telegram
# ─────────────────────────────────────────────────────────────────────────────

telegram_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

def send_telegram(message: str, reply_markup: dict = None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        r = requests.post(url, json=payload, timeout=5)
        return r.ok
    except Exception:
        return False

async def telegram_polling_loop():
    offset = 0
    url_base = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    
    while True:
        try:
            loop = asyncio.get_running_loop()
            resp = await loop.run_in_executor(
                telegram_executor, 
                lambda: requests.get(f"{url_base}/getUpdates?offset={offset}&timeout=20", timeout=25)
            )
            data = resp.json()
            if "result" in data:
                for update in data["result"]:
                    offset = update["update_id"] + 1
                    if "callback_query" in update:
                        cb = update["callback_query"]
                        cb_id = cb["id"]
                        cb_data = cb.get("data", "")
                        
                        if cb_data.startswith("verify_") or cb_data.startswith("reject_"):
                            action, order_ref = cb_data.split("_", 1)
                            
                            db = next(get_db())
                            pedido = db.query(Pedido).filter_by(order_ref=order_ref).first()
                            text_answer = "Error. Pedido no encontrado."
                            
                            if pedido and pedido.estado == "pendiente":
                                if action == "verify":
                                    pedido.estado = "preparando"
                                    text_answer = "✅ Pago Verificado. Pedido en Preparación."
                                else:
                                    pedido.estado = "cancelado"
                                    text_answer = "❌ Pedido Cancelado (Pago Rechazado)."
                                db.commit()
                            
                                # Edit message reply markup to remove buttons
                                chat_id = cb["message"]["chat"]["id"]
                                msg_id = cb["message"]["message_id"]
                                await loop.run_in_executor(telegram_executor, lambda: requests.post(f"{url_base}/editMessageReplyMarkup", json={"chat_id": chat_id, "message_id": msg_id, "reply_markup": {"inline_keyboard": []}}, timeout=5))
                                
                                # Confirm in chat if successful
                                estado_str = "PREPARANDO 🍳✅" if action == "verify" else "CANCELADO ❌"
                                await loop.run_in_executor(telegram_executor, lambda: requests.post(f"{url_base}/sendMessage", json={"chat_id": chat_id, "text": f"✅ Orden {order_ref} actualizada a: {estado_str}"}, timeout=5))
                            
                            elif pedido and pedido.estado != "pendiente":
                                text_answer = "Ya fue procesado."
                            
                            # Answer callback at the end
                            await loop.run_in_executor(telegram_executor, lambda: requests.post(f"{url_base}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": text_answer, "show_alert": True}, timeout=5))
                                
        except Exception as e:
            pass
        await asyncio.sleep(2)


# ─────────────────────────────────────────────────────────────────────────────
# Rutas
# ─────────────────────────────────────────────────────────────────────────────



# ── Auth ─────────────────────────────────────────────────────────────

@app.post("/api/auth/login", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = db.query(Admin).filter_by(username=form.username, activo=True).first()
    if not admin or not verify_password(form.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    admin.ultimo_login = datetime.utcnow()
    db.commit()
    token = create_token({"sub": admin.username, "rol": admin.rol})
    return {"access_token": token, "token_type": "bearer",
            "admin": {"id": admin.id, "username": admin.username,
                      "nombre": admin.nombre, "rol": admin.rol}}

@app.get("/api/auth/me")
async def me(current: Admin = Depends(get_current_admin)):
    return {"id": current.id, "username": current.username,
            "nombre": current.nombre, "rol": current.rol}


# ── Categorías ────────────────────────────────────────────────────────

@app.get("/api/categorias", response_model=List[CategoriaOut])
async def list_categorias(db: Session = Depends(get_db)):
    return db.query(Categoria).filter_by(activa=True).order_by(Categoria.orden).all()

@app.post("/api/categorias", response_model=CategoriaOut)
async def create_categoria(nombre: str, emoji: str = "🍽️", slug: str = "",
                            orden: int = 0, db: Session = Depends(get_db),
                            current: Admin = Depends(get_current_admin)):
    if not slug:
        slug = nombre.lower().replace(" ", "_")
    cat = Categoria(nombre=nombre, emoji=emoji, slug=slug, orden=orden)
    db.add(cat); db.commit(); db.refresh(cat)
    log_action(db, current.id, "crear_categoria", "categorias", cat.id, {"nombre": nombre})
    db.commit()
    return cat


# ── Menú Items ────────────────────────────────────────────────────────

@app.get("/api/menu", response_model=List[MenuItemOut])
async def public_menu(categoria: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(MenuItem).filter_by(activo=True)
    if categoria:
        cat = db.query(Categoria).filter_by(slug=categoria).first()
        if cat:
            q = q.filter_by(categoria_id=cat.id)
    return q.all()

@app.get("/api/menu/admin", response_model=List[MenuItemOut])
async def admin_menu(db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    return db.query(MenuItem).all()

@app.post("/api/menu", response_model=MenuItemOut)
async def create_item(item: MenuItemIn, db: Session = Depends(get_db),
                       current: Admin = Depends(get_current_admin)):
    obj = MenuItem(**item.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    log_action(db, current.id, "crear_item", "menu_items", obj.id, {"nombre": obj.nombre})
    db.commit()
    return obj

@app.put("/api/menu/{item_id}", response_model=MenuItemOut)
async def update_item(item_id: int, item: MenuItemIn, db: Session = Depends(get_db),
                       current: Admin = Depends(get_current_admin)):
    obj = db.query(MenuItem).filter_by(id=item_id).first()
    if not obj:
        raise HTTPException(404, "Plato no encontrado")
    antes = {"nombre": obj.nombre, "precio_usd": obj.precio_usd}
    for k, v in item.model_dump().items():
        setattr(obj, k, v)
    obj.actualizado = datetime.utcnow()
    db.commit(); db.refresh(obj)
    log_action(db, current.id, "editar_item", "menu_items", obj.id,
               {"antes": antes, "despues": {"nombre": obj.nombre, "precio_usd": obj.precio_usd}})
    db.commit()
    return obj

@app.delete("/api/menu/{item_id}")
async def delete_item(item_id: int, db: Session = Depends(get_db),
                       current: Admin = Depends(get_current_admin)):
    obj = db.query(MenuItem).filter_by(id=item_id).first()
    if not obj:
        raise HTTPException(404, "Plato no encontrado")
    obj.activo = False; obj.actualizado = datetime.utcnow()
    log_action(db, current.id, "desactivar_item", "menu_items", obj.id, {"nombre": obj.nombre})
    db.commit()
    return {"status": "ok", "message": f"'{obj.nombre}' desactivado"}

@app.post("/api/menu/{item_id}/imagen")
async def upload_imagen(item_id: int, file: UploadFile = File(...),
                         db: Session = Depends(get_db),
                         current: Admin = Depends(get_current_admin)):
    obj = db.query(MenuItem).filter_by(id=item_id).first()
    if not obj:
        raise HTTPException(404, "Plato no encontrado")
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("jpg", "jpeg", "png", "webp"):
        raise HTTPException(400, "Solo se permiten imágenes JPG, PNG o WEBP")
    filename = f"item_{item_id}.{ext}"
    dest = os.path.join(UPLOAD_DIR, filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    obj.imagen_url = f"/assets/menu/{filename}"
    obj.actualizado = datetime.utcnow()
    log_action(db, current.id, "subir_imagen", "menu_items", obj.id, {"archivo": filename})
    db.commit()
    return {"status": "ok", "imagen_url": obj.imagen_url}

@app.put("/api/menu/precios/batch")
async def batch_precios(data: BatchPrecioIn, db: Session = Depends(get_db),
                         current: Admin = Depends(get_current_admin)):
    q = db.query(MenuItem).filter_by(activo=True)
    if data.categoria_id:
        q = q.filter_by(categoria_id=data.categoria_id)
    items = q.all()
    factor = 1 + (data.porcentaje / 100)
    for i in items:
        i.precio_usd = round(i.precio_usd * factor, 2)
        i.actualizado = datetime.utcnow()
    log_action(db, current.id, "ajuste_precios_batch", "menu_items", None,
               {"porcentaje": data.porcentaje, "categoria_id": data.categoria_id, "items": len(items)})
    db.commit()
    return {"status": "ok", "items_actualizados": len(items), "factor": factor}


# ── Promociones ───────────────────────────────────────────────────────

def _hydrate_promocion(p: Promocion) -> PromocionOut:
    po = p.precio_original
    pf = p.precio_final
    
    if po is None and pf is None and p.aplica_a == "item" and p.items_aplicados:
        suma = sum((i.menu_item.precio_usd for i in p.items_aplicados if i.menu_item))
        po = round(suma, 2)
        if p.tipo == "porcentaje":
            pf = round(suma * (1 - p.valor / 100), 2)
        elif p.tipo == "precio_fijo":
            pf = round(p.valor, 2)
        else:
            pf = round(suma - p.valor, 2)
            if pf < 0: pf = 0.0

    return PromocionOut(
        id=p.id, nombre=p.nombre, descripcion=p.descripcion, tipo=p.tipo,
        valor=p.valor, aplica_a=p.aplica_a, categoria_id=p.categoria_id,
        fecha_inicio=p.fecha_inicio, fecha_fin=p.fecha_fin, activa=p.activa,
        precio_original=po, precio_final=pf
    )

@app.get("/api/promociones", response_model=List[PromocionOut])
async def public_promociones(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    q = db.query(Promocion).filter_by(activa=True)
    promos = []
    for p in q.all():
        if (not p.fecha_inicio or p.fecha_inicio <= now) and (not p.fecha_fin or p.fecha_fin >= now):
            promos.append(_hydrate_promocion(p))
    return promos

@app.get("/api/promociones/admin", response_model=List[PromocionOut])
async def admin_promociones(db: Session = Depends(get_db),
                             current: Admin = Depends(get_current_admin)):
    return [_hydrate_promocion(p) for p in db.query(Promocion).all()]

@app.post("/api/promociones", response_model=PromocionOut)
async def create_promo(promo: PromocionIn, db: Session = Depends(get_db),
                        current: Admin = Depends(get_current_admin)):
    item_ids = promo.item_ids
    data = promo.model_dump(exclude={"item_ids"})
    obj = Promocion(**data)
    db.add(obj); db.flush()
    for iid in item_ids:
        db.add(PromocionItem(promocion_id=obj.id, menu_item_id=iid))
    log_action(db, current.id, "crear_promocion", "promociones", obj.id, {"nombre": obj.nombre})
    db.commit(); db.refresh(obj)
    return obj

@app.put("/api/promociones/{promo_id}", response_model=PromocionOut)
async def update_promo(promo_id: int, promo: PromocionIn, db: Session = Depends(get_db),
                        current: Admin = Depends(get_current_admin)):
    obj = db.query(Promocion).filter_by(id=promo_id).first()
    if not obj:
        raise HTTPException(404, "Promoción no encontrada")
    item_ids = promo.item_ids
    for k, v in promo.model_dump(exclude={"item_ids"}).items():
        setattr(obj, k, v)
    db.query(PromocionItem).filter_by(promocion_id=promo_id).delete()
    for iid in item_ids:
        db.add(PromocionItem(promocion_id=promo_id, menu_item_id=iid))
    log_action(db, current.id, "editar_promocion", "promociones", promo_id, {"nombre": obj.nombre})
    db.commit(); db.refresh(obj)
    return obj

@app.delete("/api/promociones/{promo_id}")
async def delete_promo(promo_id: int, db: Session = Depends(get_db),
                        current: Admin = Depends(get_current_admin)):
    obj = db.query(Promocion).filter_by(id=promo_id).first()
    if not obj:
        raise HTTPException(404, "Promoción no encontrada")
    obj.activa = False
    log_action(db, current.id, "desactivar_promocion", "promociones", promo_id, {"nombre": obj.nombre})
    db.commit()
    return {"status": "ok"}


# ── Pedidos ───────────────────────────────────────────────────────────

order_counter = 100  # contador en memoria, se sincroniza con BD al arrancar

@app.on_event("startup")
async def sync_counter():
    global order_counter
    db = next(get_db())
    last = db.query(Pedido).order_by(Pedido.id.desc()).first()
    if last:
        try:
            order_counter = int(last.order_ref.split("-")[-1])
        except Exception:
            pass
    asyncio.create_task(telegram_polling_loop())

@app.post("/api/orden")
async def create_order(order: OrderRequest, db: Session = Depends(get_db)):
    # BLOQUEO HORARIO (08:00 - 20:00)
    # hora_actual = datetime.now().hour
    # if hora_actual < 8 or hora_actual >= 20:
    #     raise HTTPException(status_code=403, detail="El horario de recepción de pedidos es de 08:00 AM a 08:00 PM.")

    global order_counter
    order_counter += 1
    ref = f"#ORD-{order_counter}"

    # Obligamos a que exista la cuenta (para Mis Pedidos)
    cliente = db.query(Cliente).filter_by(telefono=order.customer_phone).first()
    if not cliente:
        # Auto-crear si no existe por seguridad, aunque el front debería forzar el registro primero
        cliente = Cliente(
            nombre=order.customer_name,
            telefono=order.customer_phone,
            correo=order.correo,
            direccion=order.direccion,
            password_hash=pwd_ctx.hash(order.password) if order.password else None,
        )
        db.add(cliente); db.flush()
    else:
        # Actualizar datos de entrega si cambiaron
        if order.direccion and order.tipo_entrega == "delivery":
            cliente.direccion = order.direccion
            db.flush()

    # Calcular costo de delivery si aplica
    costo_delivery = 0.0
    if order.tipo_entrega == "delivery" and order.zona_id:
        zona = db.query(DeliveryZona).filter_by(id=order.zona_id).first()
        if zona:
            costo_delivery = zona.precio

    total_final = order.total + costo_delivery

    pedido = Pedido(
        order_ref=ref,
        cliente_id=cliente.id,
        cliente_nombre=cliente.nombre,
        cliente_telefono=cliente.telefono,
        metodo_pago=order.payment_method,
        referencia_pago=order.payment_ref,
        tipo_entrega=order.tipo_entrega,
        direccion=order.direccion if order.tipo_entrega == "delivery" else None,
        total=total_final,
        tasa_bcv=order.tasa_bcv,
        estado="pendiente",
    )
    db.add(pedido); db.flush()

    for it in order.items:
        menu_item = db.query(MenuItem).filter_by(nombre=it.name).first()
        db.add(PedidoItem(
            pedido_id=pedido.id,
            menu_item_id=menu_item.id if menu_item else None,
            nombre=it.name,
            precio_usd=it.price,
            cantidad=it.qty,
            subtotal=round(it.price * it.qty, 2),
        ))

    db.commit()

    # Notificación Telegram ajustada
    items_text = "\n".join([f"• {i.qty}x {i.name} (${i.price * i.qty:.2f})" for i in order.items])
    entrega_txt = f"🛵 <b>Delivery a:</b> {order.direccion}" if order.tipo_entrega == "delivery" else "🏪 <b>Pick-Up en Tienda</b>"
    if costo_delivery > 0:
        entrega_txt += f" (+${costo_delivery:.2f} zona de envío)"
    
    total_bs = order.total * order.tasa_bcv if hasattr(order, 'tasa_bcv') and order.tasa_bcv else 0.0

    msg = (
        f"🔔 <b>NUEVA ORDEN {ref}</b>\n\n"
        f"👤 <b>Cliente:</b> {cliente.nombre} ({cliente.telefono})\n"
        f"{entrega_txt}\n\n"
        f"🛒 <b>PEDIDO:</b>\n{items_text}\n"
        f"💰 <b>Total:</b> ${order.total:.2f} (Bs. {total_bs:.2f})\n\n"
        f"💳 <b>Pago:</b> {order.payment_method}\n"
        f"📋 <b>Ref:</b> {order.payment_ref}\n\n"
        f"⚠️ <i>Toca un botón para verificar el pago y procesar orden:</i>"
    )
    
    markup = {
        "inline_keyboard": [
            [
                {"text": "✅ Recibido (Preparar)", "callback_data": f"verify_{ref}"}
            ],
            [
                {"text": "❌ Falta Pago (Cancelar)", "callback_data": f"reject_{ref}"}
            ]
        ]
    }
    send_telegram(msg, markup)

    return {"status": "success", "order_id": ref, "message": "Orden en verificación."}

@app.get("/api/rastreo/{order_ref}")
async def rastrear_pedido(order_ref: str, db: Session = Depends(get_db)):
    """Endpoint público para que los clientes vean el progreso de su orden"""
    pedido = db.query(Pedido).filter_by(order_ref=order_ref).first()
    if not pedido:
        raise HTTPException(404, "Pedido no encontrado")
        
    return {
        "order_ref": pedido.order_ref,
        "cliente_nombre": pedido.cliente_nombre,
        "total": pedido.total,
        "estado": pedido.estado,
        "creado_en": pedido.creado_en.isoformat(),
        "metodo_pago": pedido.metodo_pago,
        "items": [{"nombre": i.nombre, "cantidad": i.cantidad, "subtotal": i.subtotal} for i in pedido.items]
    }

@app.get("/api/pedidos")
async def list_pedidos(skip: int = 0, limit: int = 50, estado: Optional[str] = None,
                        db: Session = Depends(get_db),
                        current: Admin = Depends(get_current_admin)):
    q = db.query(Pedido).order_by(Pedido.creado_en.desc())
    if estado:
        q = q.filter_by(estado=estado)
    pedidos = q.offset(skip).limit(limit).all()
    result = []
    for p in pedidos:
        result.append({
            "id": p.id, "order_ref": p.order_ref, "cliente_nombre": p.cliente_nombre,
            "cliente_telefono": p.cliente_telefono, "metodo_pago": p.metodo_pago,
            "total": p.total, "estado": p.estado,
            "creado_en": p.creado_en.isoformat(),
            "items": [{"nombre": i.nombre, "cantidad": i.cantidad, "subtotal": i.subtotal}
                      for i in p.items],
        })
    return result

@app.put("/api/pedidos/{pedido_id}/estado")
async def update_estado(pedido_id: int, data: PedidoEstadoIn, db: Session = Depends(get_db),
                         current: Admin = Depends(get_current_admin)):
    p = db.query(Pedido).filter_by(id=pedido_id).first()
    if not p:
        raise HTTPException(404, "Pedido no encontrado")
    estados_validos = {"pendiente", "preparando", "listo", "entregado", "cancelado"}
    if data.estado not in estados_validos:
        raise HTTPException(400, f"Estado inválido. Opciones: {estados_validos}")
    p.estado = data.estado; p.actualizado = datetime.utcnow()
    log_action(db, current.id, "cambiar_estado_pedido", "pedidos", pedido_id,
               {"estado": data.estado})
    db.commit()
    return {"status": "ok", "order_ref": p.order_ref, "nuevo_estado": data.estado}

@app.get("/api/stats")
async def stats(db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    today = datetime.utcnow().date()
    start_of_today = datetime(today.year, today.month, today.day)
    
    # Obtener todos los pedidos de hoy
    todos_hoy = db.query(Pedido).filter(Pedido.creado_en >= start_of_today).all()
    
    # Excluir cancelados para métricas positivas
    validos_hoy = [p for p in todos_hoy if p.estado != "cancelado"]
    ingresos_hoy = sum(p.total for p in validos_hoy)
    
    # Nuevas lógicas funcionales
    ticket_promedio = (ingresos_hoy / len(validos_hoy)) if validos_hoy else 0.0
    pendientes = db.query(Pedido).filter(Pedido.estado.in_(["pendiente", "preparando"])).count()
    
    total_platos  = db.query(MenuItem).filter_by(activo=True).count()
    total_pedidos = db.query(Pedido).filter(Pedido.estado != "cancelado").count()
    
    return {
        "pedidos_hoy":  len(validos_hoy),
        "ingresos_hoy": round(ingresos_hoy, 2),
        "total_platos": total_platos,
        "total_pedidos": total_pedidos,
        "pendientes": pendientes,
        "ticket_promedio": round(ticket_promedio, 2)
    }

@app.get("/api/admin/analytics/ventas")
async def analytics_ventas(db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    hoy = datetime.utcnow().date()
    hace_7_dias = hoy - timedelta(days=6)
    
    pedidos = db.query(Pedido).filter(Pedido.creado_en >= datetime(hace_7_dias.year, hace_7_dias.month, hace_7_dias.day)).all()
    
    dias_labels = []
    ventas_dict = {}
    for i in range(7):
        d = hoy - timedelta(days=6 - i)
        str_d = d.strftime("%d/%m")
        dias_labels.append(str_d)
        ventas_dict[str_d] = 0.0

    for p in pedidos:
        if p.estado != "cancelado":
            str_d = p.creado_en.strftime("%d/%m")
            if str_d in ventas_dict:
                ventas_dict[str_d] += p.total

    return {
        "labels": dias_labels,
        "data": [round(ventas_dict[lbl], 2) for lbl in dias_labels]
    }
# ── Zonas de Delivery ──────────────────────────────────────────────────
@app.get("/api/zonas", response_model=List[ZonaOut])
async def get_zonas(db: Session = Depends(get_db)):
    return db.query(DeliveryZona).filter_by(activa=True).all()

@app.post("/api/zonas", response_model=ZonaOut)
async def create_zona(data: ZonaIn, db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    obj = DeliveryZona(**data.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@app.put("/api/zonas/{id}", response_model=ZonaOut)
async def update_zona(id: int, data: ZonaIn, db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    obj = db.query(DeliveryZona).filter_by(id=id).first()
    if not obj: raise HTTPException(404)
    for k, v in data.model_dump().items(): setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return obj

@app.delete("/api/zonas/{id}")
async def delete_zona(id: int, db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    obj = db.query(DeliveryZona).filter_by(id=id).first()
    if not obj: raise HTTPException(404)
    obj.activa = False
    db.commit()
    return {"status": "ok"}

# ── Clientes ──────────────────────────────────────────────────────

@app.get("/api/clientes/{telefono}/direcciones", response_model=List[DireccionOut])
async def get_direcciones(telefono: str, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter_by(telefono=telefono).first()
    if not cliente: raise HTTPException(404, "Cliente no encontrado")
    return cliente.direcciones

@app.post("/api/clientes/{telefono}/direcciones", response_model=DireccionOut)
async def add_direccion(telefono: str, data: DireccionIn, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter_by(telefono=telefono).first()
    if not cliente: raise HTTPException(404, "Cliente no encontrado")
    obj = Direccion(cliente_id=cliente.id, alias=data.alias, direccion_texto=data.direccion_texto)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@app.post("/api/clientes/registro")
async def cliente_registro(data: ClienteRegistroIn, db: Session = Depends(get_db)):
    existente = db.query(Cliente).filter_by(telefono=data.telefono).first()
    if existente:
        raise HTTPException(400, "Ya existe una cuenta con este teléfono")
    
    nuevo_cliente = Cliente(
        nombre=data.nombre,
        telefono=data.telefono,
        correo=data.correo,
        direccion=data.direccion,
        password_hash=pwd_ctx.hash(data.password)
    )
    db.add(nuevo_cliente); db.commit(); db.refresh(nuevo_cliente)
    return {
        "status": "ok",
        "cliente": {
            "id": nuevo_cliente.id, "nombre": nuevo_cliente.nombre,
            "telefono": nuevo_cliente.telefono, "correo": nuevo_cliente.correo,
            "direccion": nuevo_cliente.direccion
        }
    }

@app.post("/api/clientes/login")
async def cliente_login(data: ClienteLoginIn, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter_by(telefono=data.telefono).first()
    if not cliente or not cliente.password_hash:
        raise HTTPException(401, "Teléfono no registrado o sin contraseña")
    if not pwd_ctx.verify(data.password, cliente.password_hash):
        raise HTTPException(401, "Contraseña incorrecta")
    return {
        "status": "ok",
        "cliente": {"id": cliente.id, "nombre": cliente.nombre,
                    "telefono": cliente.telefono, "correo": cliente.correo,
                    "direccion": cliente.direccion}
    }

@app.post("/api/auth/recuperar-password")
async def recuperar_password(data: RecuperarInfo, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter_by(correo=data.correo).first()
    if not cliente:
        # Previene enumeración de correos
        return {"status": "ok", "msg": "Si el correo está registrado, recibirás un código."}
        
    # Inactivar códigos viejos
    db.query(PwdReset).filter_by(correo=data.correo, usado=False).update({"usado": True})
    
    codigo = ''.join(random.choices(string.digits, k=6))
    nuevo_reset = PwdReset(correo=data.correo, codigo=codigo)
    db.add(nuevo_reset)
    db.commit()
    
    send_recovery_email(data.correo, codigo)
    return {"status": "ok", "msg": "Si el correo está registrado, recibirás un código."}

@app.post("/api/auth/reset-password")
async def reset_password(data: ResetInfo, db: Session = Depends(get_db)):
    ahora = datetime.utcnow()
    bloque = db.query(PwdReset).filter(
        PwdReset.correo == data.correo,
        PwdReset.codigo == data.codigo,
        PwdReset.usado == False
    ).first()
    
    if not bloque:
        raise HTTPException(400, "Código inválido o ya expirado.")
        
    # Verificar 15 minutos de caducidad
    if (ahora - bloque.creado_en).total_seconds() > 900:
        bloque.usado = True
        db.commit()
        raise HTTPException(400, "El código ha expirado tras 15 minutos.")
        
    cliente = db.query(Cliente).filter_by(correo=data.correo).first()
    if not cliente:
        raise HTTPException(404, "Usuario no encontrado")
        
    cliente.password_hash = pwd_ctx.hash(data.nueva_password)
    bloque.usado = True
    db.commit()
    return {"status": "ok", "msg": "Contraseña restablecida exitosamente."}

@app.get("/api/clientes/{telefono}/pedidos")
async def mis_pedidos(telefono: str, db: Session = Depends(get_db)):
    """Retorna todo el historial de pedidos de este cliente"""
    cliente = db.query(Cliente).filter_by(telefono=telefono).first()
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")
    
    pedidos = db.query(Pedido).filter_by(cliente_id=cliente.id).order_by(Pedido.creado_en.desc()).all()
    resultado = []
    for p in pedidos:
        resultado.append({
            "order_ref": p.order_ref,
            "estado": p.estado,
            "total": p.total,
            "creado_en": p.creado_en.isoformat(),
            "tipo_entrega": p.tipo_entrega,
            "items_resumen": ", ".join([f"{i.cantidad}x {i.nombre}" for i in p.items])
        })
    return resultado

@app.get("/api/clientes/buscar")
async def buscar_cliente(telefono: str, db: Session = Depends(get_db)):
    """Buscar datos de un cliente por teléfono (para autocompletado)"""
    cliente = db.query(Cliente).filter_by(telefono=telefono).first()
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")
    return {
        "id": cliente.id, "nombre": cliente.nombre,
        "telefono": cliente.telefono, "correo": cliente.correo,
        "direccion": cliente.direccion
    }


# ─────────────────────────────────────────────────────────────────────────────
# SERVIR FRONTEND ESTÁTICO (debe ir al FINAL después de todas las rutas API)
# ─────────────────────────────────────────────────────────────────────────────
STATIC_DIR = os.path.join(os.path.dirname(__file__), "site", "public")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend:app", host="0.0.0.0", port=3000, reload=True)
