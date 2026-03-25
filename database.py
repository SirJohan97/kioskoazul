"""
database.py — Kiosko Azul
Modelos SQLAlchemy + configuración de BD SQLite
"""
import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'kioskoazul.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─────────────────────────────────────────────────────────────────────────────
# TABLAS
# ─────────────────────────────────────────────────────────────────────────────

class Admin(Base):
    __tablename__ = "admins"
    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre        = Column(String(100))
    rol           = Column(String(20), default="editor")   # superadmin | editor
    activo        = Column(Boolean, default=True)
    creado_en     = Column(DateTime, default=datetime.utcnow)
    ultimo_login  = Column(DateTime, nullable=True)

    logs = relationship("AuditLog", back_populates="admin")


class Cliente(Base):
    __tablename__ = "clientes"
    id            = Column(Integer, primary_key=True, index=True)
    nombre        = Column(String(120), nullable=False)
    telefono      = Column(String(30), nullable=False, unique=True, index=True)
    correo        = Column(String(120), nullable=True)
    direccion     = Column(Text, nullable=True)
    password_hash = Column(String(255), nullable=True)  # opcional para login rápido
    creado_en     = Column(DateTime, default=datetime.utcnow)

    pedidos = relationship("Pedido", back_populates="cliente")
    direcciones = relationship("Direccion", back_populates="cliente")


class Categoria(Base):
    __tablename__ = "categorias"
    id        = Column(Integer, primary_key=True, index=True)
    nombre    = Column(String(50), unique=True, nullable=False)
    emoji     = Column(String(10), default="🍽️")
    slug      = Column(String(50), unique=True, nullable=False)   # desayunos, almuerzos…
    orden     = Column(Integer, default=0)
    activa    = Column(Boolean, default=True)

    items = relationship("MenuItem", back_populates="categoria")


class MenuItem(Base):
    __tablename__ = "menu_items"
    id           = Column(Integer, primary_key=True, index=True)
    nombre       = Column(String(120), nullable=False)
    descripcion  = Column(Text)
    precio_usd   = Column(Float, nullable=False)
    imagen_url   = Column(String(255), nullable=True)
    badge        = Column(String(50), nullable=True)   # Ej: "⭐ Popular", "Vegano"
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    activo       = Column(Boolean, default=True)
    destacado    = Column(Boolean, default=False)
    creado_en    = Column(DateTime, default=datetime.utcnow)
    actualizado  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    categoria   = relationship("Categoria", back_populates="items")
    pedido_items = relationship("PedidoItem", back_populates="menu_item")
    promociones  = relationship("PromocionItem", back_populates="menu_item")


class Promocion(Base):
    __tablename__ = "promociones"
    id              = Column(Integer, primary_key=True, index=True)
    nombre          = Column(String(120), nullable=False)
    descripcion     = Column(Text, nullable=True)
    tipo            = Column(String(20), default="porcentaje")  # porcentaje | monto_fijo
    valor           = Column(Float, nullable=False)             # % o $ de descuento
    aplica_a        = Column(String(20), default="item")        # item | categoria | total
    categoria_id    = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    fecha_inicio    = Column(DateTime, nullable=True)
    fecha_fin       = Column(DateTime, nullable=True)
    activa          = Column(Boolean, default=True)
    precio_original = Column(Float, nullable=True)
    precio_final    = Column(Float, nullable=True)
    creado_en       = Column(DateTime, default=datetime.utcnow)

    items_aplicados = relationship("PromocionItem", back_populates="promocion")


class PromocionItem(Base):
    """Relación many-to-many entre Promocion y MenuItem"""
    __tablename__ = "promocion_items"
    id           = Column(Integer, primary_key=True)
    promocion_id = Column(Integer, ForeignKey("promociones.id"))
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"))

    promocion  = relationship("Promocion", back_populates="items_aplicados")
    menu_item  = relationship("MenuItem", back_populates="promociones")


class Pedido(Base):
    __tablename__ = "pedidos"
    id               = Column(Integer, primary_key=True, index=True)
    order_ref        = Column(String(20), unique=True, nullable=False)  # #ORD-101
    cliente_id       = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    cliente_nombre   = Column(String(120), nullable=False)
    cliente_telefono = Column(String(30))
    metodo_pago      = Column(String(50))
    referencia_pago  = Column(String(100))
    tipo_entrega     = Column(String(20), default="pickup") # pickup | delivery
    direccion        = Column(Text, nullable=True)
    subtotal         = Column(Float, default=0.0)
    descuento        = Column(Float, default=0.0)
    total            = Column(Float, nullable=False)
    estado           = Column(String(20), default="pendiente")
    # pendiente | preparando | listo | entregado | cancelado
    notas            = Column(Text, nullable=True)
    tasa_bcv         = Column(Float, nullable=True)   # tasa del momento del pedido
    creado_en        = Column(DateTime, default=datetime.utcnow)
    actualizado      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items   = relationship("PedidoItem", back_populates="pedido")
    cliente = relationship("Cliente", back_populates="pedidos")


class PedidoItem(Base):
    __tablename__ = "pedido_items"
    id           = Column(Integer, primary_key=True)
    pedido_id    = Column(Integer, ForeignKey("pedidos.id"))
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=True)
    nombre       = Column(String(120), nullable=False)  # snapshot del nombre
    precio_usd   = Column(Float, nullable=False)        # snapshot del precio
    cantidad     = Column(Integer, default=1)
    subtotal     = Column(Float, nullable=False)

    pedido    = relationship("Pedido", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="pedido_items")


class AuditLog(Base):
    __tablename__ = "audit_log"
    id         = Column(Integer, primary_key=True)
    admin_id   = Column(Integer, ForeignKey("admins.id"), nullable=True)
    accion     = Column(String(100), nullable=False)   # "crear_item", "editar_precio"…
    tabla      = Column(String(50))
    registro_id = Column(Integer, nullable=True)
    detalle    = Column(JSON, nullable=True)            # datos antes/después
    creado_en  = Column(DateTime, default=datetime.utcnow)

    admin = relationship("Admin", back_populates="logs")

class DeliveryZona(Base):
    __tablename__ = "delivery_zonas"
    id     = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    precio = Column(Float, default=0.0)
    activa = Column(Boolean, default=True)

class Direccion(Base):
    __tablename__ = "direcciones"
    id              = Column(Integer, primary_key=True)
    cliente_id      = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    alias           = Column(String(50), nullable=True) # e.g. "Casa", "Trabajo"
    direccion_texto = Column(Text, nullable=False)
    
    cliente = relationship("Cliente", back_populates="direcciones")

class Config(Base):
    __tablename__ = "config"
    key   = Column(String(50), primary_key=True)
    value = Column(String(255), nullable=True)

class PwdReset(Base):
    __tablename__ = "pwd_resets"
    id        = Column(Integer, primary_key=True)
    correo    = Column(String(120), nullable=False)
    codigo    = Column(String(6), nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow)
    usado     = Column(Boolean, default=False)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_db():
    """Dependency FastAPI para inyectar sesión de BD"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)
