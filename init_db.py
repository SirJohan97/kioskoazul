"""
init_db.py — Kiosko Azul
Inicializa la BD y pobla con los datos del menú actual.
Ejecutar una sola vez: python init_db.py
"""
from database import create_tables, SessionLocal, Admin, Categoria, MenuItem
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


def seed():
    create_tables()
    db = SessionLocal()

    try:
        # ── Admin por defecto ──────────────────────────────────────────────
        if not db.query(Admin).filter_by(username="jf").first():
            db.add(Admin(
                username="jf",
                password_hash=pwd_ctx.hash("kioskoazul0802"),
                nombre="Administrador Principal",
                rol="superadmin",
                activo=True,
            ))
            print("✅ Admin creado: jf / kioskoazul0802")

        # ── Categorías ────────────────────────────────────────────────────
        cats_data = [
            {"nombre": "Desayunos",  "emoji": "🌅", "slug": "desayunos",  "orden": 1},
            {"nombre": "Almuerzos",  "emoji": "☀️", "slug": "almuerzos",  "orden": 2},
            {"nombre": "Bebidas",   "emoji": "🍹", "slug": "bebidas",  "orden": 3},
            {"nombre": "Cenas",      "emoji": "🌙", "slug": "cenas",      "orden": 4},
        ]
        cats = {}
        for c in cats_data:
            obj = db.query(Categoria).filter_by(slug=c["slug"]).first()
            if not obj:
                obj = Categoria(**c)
                db.add(obj)
                db.flush()
            cats[c["slug"]] = obj
        print("✅ Categorías creadas")

        # ── Menú Items ────────────────────────────────────────────────────
        items_data = [
            # Desayunos
            {"nombre": "Empanadas de Cazón",       "descripcion": "Empanadas fritas rellenas de cazón fresco. Servidas con salsa criolla.", "precio_usd": 8,  "badge": "⭐ Popular",     "cat": "desayunos"},
            {"nombre": "Arepas Asadas",             "descripcion": "Arepas de maíz a la brasa con queso blanco, aguacate y mantequilla.", "precio_usd": 6,  "badge": None,             "cat": "desayunos"},
            {"nombre": "Pabellón Criollo",          "descripcion": "Caraotas negras, carne mechada, tajadas y arroz blanco. El desayuno venezolano por excelencia.", "precio_usd": 10, "badge": None, "cat": "desayunos"},
            {"nombre": "Fruta Tropical",            "descripcion": "Selección de frutas tropicales frescas con miel de agave y granola artesanal.", "precio_usd": 5, "badge": "Vegano", "cat": "desayunos"},
            {"nombre": "Huevos Revueltos del Mar",  "descripcion": "Huevos revueltos con camarones, cebollín, tomate y cilantro. Servidos con tostadas.", "precio_usd": 9, "badge": None, "cat": "desayunos"},
            {"nombre": "Café Capitán",              "descripcion": "Espresso doble de origen venezolano con espuma de leche o solo. El mejor inicio del día.", "precio_usd": 3, "badge": None, "cat": "desayunos"},
            # Almuerzos
            {"nombre": "Pescado Frito con Tostones", "descripcion": "Pescado del día frito crujiente, tostones, ensalada de repollo y salsa tártara de la casa.", "precio_usd": 14, "badge": "⭐ El Más Pedido", "cat": "almuerzos"},
            {"nombre": "Ceviche de Pulpo",           "descripcion": "Pulpo fresco curado en limón, cilantro, cebolla morada y ají amarillo peruano.", "precio_usd": 16, "badge": "Premium",  "cat": "almuerzos"},
            {"nombre": "Camarones al Ajillo",        "descripcion": "Camarones jumbo salteados con ajo, vino blanco, limón y hierbas. Servidos sobre arroz blanco.", "precio_usd": 15, "badge": None, "cat": "almuerzos"},
            {"nombre": "Arroz con Mariscos",         "descripcion": "Arroz cremoso estilo risotto con camarones, calamar, mejillones y almejas frescas.", "precio_usd": 18, "badge": None, "cat": "almuerzos"},
            {"nombre": "Banderilla de Atún",         "descripcion": "Atún fresco a la plancha con ensalada de mango, aguacate y vinagreta de maracuyá.", "precio_usd": 13, "badge": None, "cat": "almuerzos"},
            {"nombre": "Pasta del Mar Verde",        "descripcion": "Linguine con pesto de albahaca fresca, tomates cherry, aceitunas negras y queso de cabra.", "precio_usd": 11, "badge": "Vegetariano", "cat": "almuerzos"},
            # Bebidas
            {"nombre": "Limonada Frappé",    "descripcion": "Limonada frozen con hierbabuena fresca y toque de jengibre.", "precio_usd": 9,  "badge": "⭐ Signature", "cat": "bebidas"},
            {"nombre": "Sangría Tinta",            "descripcion": "Nuestra sangría especial con vino tinto y frutas tropicales curadas.", "precio_usd": 8, "badge": None, "cat": "bebidas"},
            {"nombre": "Jugo Natural de Maracuyá",         "descripcion": "Refrescante jugo natural de maracuyá (parchita) endulzado al gusto.", "precio_usd": 9, "badge": None, "cat": "bebidas"},
            {"nombre": "Sangría Blanca",              "descripcion": "Vino blanco, frutas cítricas y un toque de durazno, ideal para la playa.", "precio_usd": 10, "badge": None, "cat": "bebidas"},
            {"nombre": "Agua Mineral C/S Gas",           "descripcion": "Agua mineral gasificada o natural según preferencia.", "precio_usd": 5, "badge": "Sin Alcohol", "cat": "bebidas"},
            {"nombre": "Té Helado de Limón",     "descripcion": "Refrescante infusión de té negro con limón natural y mucho hielo.", "precio_usd": 12, "badge": None, "cat": "bebidas"},
            # Cenas
            {"nombre": "Linguine al Nero di Seppia", "descripcion": "Pasta negra al tinto de calamar con medallones de mariscos en bisque de langosta y Parmigiano.", "precio_usd": 22, "badge": "⭐ Chef's Special", "cat": "cenas"},
            {"nombre": "Lobster & Truffle Risotto",  "descripcion": "Risotto Arborio con cola de langosta, aceite de trufa negra y Parmesano añejado 24 meses.", "precio_usd": 35, "badge": "Signature",  "cat": "cenas"},
            {"nombre": "Brochetas de Langostinos",   "descripcion": "Langostinos tigre a la parrilla con mantequilla de ajo, chimichurri y limón tahitiano.", "precio_usd": 19, "badge": None, "cat": "cenas"},
            {"nombre": "Pulpo a la Brasa Gourmet",   "descripcion": "Pulpo entero a la parrilla sobre puré de papas ahumado, olivada negra y aceite de ají amarillo.", "precio_usd": 24, "badge": None, "cat": "cenas"},
            {"nombre": "Pargo Entero al Horno",      "descripcion": "Pargo rojo fresco al horno con vegetales mediterráneos, hierbas y salsa de vino blanco.", "precio_usd": 26, "badge": None, "cat": "cenas"},
            {"nombre": "Tiramisú de Coco",           "descripcion": "Nuestra versión tropical del clásico italiano: bizcochos de café con mousse de coco y cacao.", "precio_usd": 8,  "badge": None, "cat": "cenas"},
        ]

        for item in items_data:
            if not db.query(MenuItem).filter_by(nombre=item["nombre"]).first():
                db.add(MenuItem(
                    nombre=item["nombre"],
                    descripcion=item["descripcion"],
                    precio_usd=item["precio_usd"],
                    badge=item["badge"],
                    categoria_id=cats[item["cat"]].id,
                    activo=True,
                    destacado=item.get("badge", "").startswith("⭐") if item.get("badge") else False,
                ))

        db.commit()
        print(f"✅ {len(items_data)} platos importados")
        print("\n🎉 Base de datos inicializada correctamente.")
        print("   Archivo: kioskoazul.db")
        print("   Admin:   admin / kioskoazul2025")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
