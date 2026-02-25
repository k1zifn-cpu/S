import asyncio
import sqlite3
import json
import threading
from flask import Flask, request, jsonify, render_template_string
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils import executor

# ================== CONFIG ==================

BOT_TOKEN = "8720523641:AAG4TpijdPzoVn7K_l8r803W10dbxxo8xQM"
ADMIN_ID = 6724600945
DOMAIN = "https://s-vslf.onrender.com"  # ОБЯЗАТЕЛЬНО HTTPS

# ============================================

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)
app = Flask(__name__)

# ================= DATABASE =================

db = sqlite3.connect("market.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    balance REAL DEFAULT 0,
    total_orders INTEGER DEFAULT 0,
    referred_by INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    price INTEGER,
    image TEXT,
    link TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER
)
""")

db.commit()

# демо товары
cursor.execute("SELECT COUNT(*) FROM products")
if cursor.fetchone()[0] == 0:
    cursor.execute("""
    INSERT INTO products (name, description, price, image, link)
    VALUES 
    ('Premium VPN', '30 дней доступа', 100, 'https://via.placeholder.com/300', 'https://google.com'),
    ('ChatGPT Pro Pack', 'Премиум инструменты', 250, 'https://via.placeholder.com/300', 'https://google.com')
    """)
    db.commit()

# ================= BOT =================

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "user"

    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (id, username) VALUES (?,?)",
            (user_id, username)
        )
        db.commit()

    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            "👻 Открыть Маркет 🥷",
            web_app=WebAppInfo(url=DOMAIN)
        )
    )

    await message.answer_photo(
        photo="https://via.placeholder.com/600x300",
        caption=f"{username}, теперь маркет в приложении 👇",
        reply_markup=kb
    )

@dp.message_handler(commands=["amenu"])
async def admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            "📊 Админ Панель",
            web_app=WebAppInfo(url=f"{DOMAIN}/admin")
        )
    )

    await message.answer("Админка:", reply_markup=kb)

# ================= WEB APP =================

MAIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
body {
  margin:0;
  font-family: system-ui;
  background: var(--tg-theme-bg-color);
  color: var(--tg-theme-text-color);
}
.header {
  padding:16px;
  font-size:20px;
  font-weight:bold;
}
.card {
  background: var(--tg-theme-secondary-bg-color);
  margin:12px;
  padding:12px;
  border-radius:16px;
}
button {
  width:100%;
  padding:10px;
  border:none;
  border-radius:10px;
  background:#2AABEE;
  color:white;
}
</style>
</head>
<body>
<div class="header">🛒 Маркет</div>
<div id="products"></div>

<script>
fetch("/api/products")
.then(r=>r.json())
.then(data=>{
  let div = document.getElementById("products");
  data.forEach(p=>{
    div.innerHTML += `
      <div class="card">
        <img src="${p.image}" width="100%">
        <h3>${p.name}</h3>
        <p>${p.description}</p>
        <p>${p.price} ⭐</p>
        <button onclick="buy(${p.id})">Купить</button>
      </div>
    `
  })
})

function buy(id){
 fetch("/api/buy",{
  method:"POST",
  headers:{"Content-Type":"application/json"},
  body:JSON.stringify({product_id:id})
 })
 alert("Товар добавлен в покупки")
}
</script>
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body{font-family:system-ui;padding:20px}
.card{background:#eee;padding:15px;margin-bottom:15px;border-radius:12px}
</style>
</head>
<body>
<h2>Админ Панель</h2>
<div id="stats"></div>

<script>
fetch("/api/admin/stats")
.then(r=>r.json())
.then(data=>{
 document.getElementById("stats").innerHTML =
   "<div class='card'>Пользователи: "+data.users+"</div>" +
   "<div class='card'>Заказы: "+data.orders+"</div>"
})
</script>
</body>
</html>
"""

@app.route("/")
def main():
    return render_template_string(MAIN_HTML)

@app.route("/admin")
def admin_page():
    return render_template_string(ADMIN_HTML)

@app.route("/api/products")
def get_products():
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    return jsonify([
        {"id":r[0],"name":r[1],"description":r[2],
         "price":r[3],"image":r[4]}
        for r in rows
    ])

@app.route("/api/buy", methods=["POST"])
def buy():
    data = request.json
    cursor.execute(
        "INSERT INTO orders (user_id, product_id) VALUES (?,?)",
        (1, data["product_id"])
    )
    db.commit()
    return jsonify({"status":"ok"})

@app.route("/api/admin/stats")
def stats():
    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders")
    orders = cursor.fetchone()[0]
    return jsonify({"users":users,"orders":orders})

# ================= RUN =================

def run_flask():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    executor.start_polling(dp)

