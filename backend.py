import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI(title="Kiosko Azul - API de Pagos")

# Allow requests from our frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Kiosko Azul API está activa. Los pedidos se procesan en /api/orden"}

# Telegram Bot Configuration
# IMPORTANTE: Reemplaza estos valores con tu bot real
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8741738690:AAG_ONxfjhzIQ6NA0RrzMJ9AhW61_cdA-wY")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "6526066600")

class CartItem(BaseModel):
    name: str
    price: float
    qty: int

class OrderRequest(BaseModel):
    customer_name: str
    customer_phone: str
    payment_method: str
    payment_ref: str
    items: list[CartItem]
    total: float

def send_telegram_message(message: str):
    if TELEGRAM_BOT_TOKEN == "TU_TOKEN_AQUI":
        print(f"SIMULATED TELEGRAM MSG:\n{message}")
        return True
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, json=payload)
    return response.ok

# In-memory counter for orders
order_counter = 100

@app.post("/api/orden")
async def create_order(order: OrderRequest):
    global order_counter
    order_counter += 1
    order_id = f"#ORD-{order_counter}"
    
    # Build Telegram Message
    items_text = "\n".join([f"• {item.qty}x {item.name} (${item.price * item.qty})" for item in order.items])
    
    message = (
        f"🔔 <b>NUEVA ORDEN {order_id}</b>\n\n"
        f"👤 <b>Cliente:</b> {order.customer_name}\n"
        f"📞 <b>Teléfono:</b> {order.customer_phone}\n\n"
        f"🛒 <b>PEDIDO:</b>\n"
        f"{items_text}\n"
        f"💰 <b>Total a Pagar:</b> ${order.total}\n\n"
        f"💳 <b>MÉTODO PAGO:</b> {order.payment_method}\n"
        f"📋 <b>REFERENCIA:</b> {order.payment_ref}\n\n"
        f"⚠️ <i>Por favor verifiquen el pago antes de despachar.</i>"
    )
    
    success = send_telegram_message(message)
    
    if not success:
        # We don't fail the user request if telegram fails, but log it
        print("Failed to send Telegram message.")
        
    return {
        "status": "success", 
        "order_id": order_id, 
        "message": "Orden procesada y notificada a cocina."
    }

if __name__ == "__main__":
    import uvicorn
    # To run: python backend.py
    uvicorn.run(app, host="0.0.0.0", port=8000)
