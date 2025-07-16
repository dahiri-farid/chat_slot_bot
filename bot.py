import os
import random
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

DB_PATH = "slotbot.db"

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 1000,
        spins INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0
    )""")
    conn.commit()
    conn.close()

def get_or_create_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if row is None:
        cur.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        balance = 1000
    else:
        balance = row[0]
    conn.close()
    return balance

def update_balance(user_id, amount, win=False):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + ?, spins = spins + 1, wins = wins + ? WHERE user_id = ?",
                (amount, int(win), user_id))
    conn.commit()
    conn.close()

SYMBOLS = ['🍒', '🍋', '🍉', '⭐️', '🔔']

def generate_grid():
    return [[random.choice(SYMBOLS) for _ in range(3)] for _ in range(3)]

def check_win(grid):
    center_row = grid[1]
    return len(set(center_row)) == 1, center_row[0] if len(set(center_row)) == 1 else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = get_or_create_user(user_id)
    await update.message.reply_text(f"🎰 Welcome to SlotBot!\nYour balance: {balance}🪙\nType /spin to play!")

async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = get_or_create_user(user_id)
    if balance < 100:
        await update.message.reply_text("❌ Not enough coins to spin. Each spin costs 100🪙.")
        return

    grid = generate_grid()
    win, symbol = check_win(grid)
    win_amount = 300 if win else 0
    update_balance(user_id, -100 + win_amount, win)

    grid_display = '\n'.join([' '.join(row) for row in grid])
    result = f"🎰 SPINNING...\n\n{grid_display}"
    if win:
        result += f"\n\n🎉 YOU WIN! {symbol}{symbol}{symbol} +300🪙"
    else:
        result += "\n\n😢 No win this time."

    new_balance = get_or_create_user(user_id)
    result += f"\nBalance: {new_balance}🪙"
    await update.message.reply_text(result)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT balance, spins, wins FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        balance, spins, wins = row
        await update.message.reply_text(f"📊 Stats:\nBalance: {balance}🪙\nSpins: {spins}\nWins: {wins}")
    else:
        await update.message.reply_text("No stats found. Try /start first.")

if __name__ == "__main__":
    init_db()
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("spin", spin))
    app.add_handler(CommandHandler("stats", stats))
    app.run_polling()
