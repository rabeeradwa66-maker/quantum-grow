import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, Message
from sqlalchemy import select

from .config import settings
from .db import Base, SessionLocal, engine
from .models import DemoBalance, DepositRequest, InvestmentPlan, User, WithdrawalRequest

Base.metadata.create_all(bind=engine)
bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher()

PLANS = [
    (1, "Starter", 10, 7, 0.0),
    (2, "Basic", 25, 7, 0.0),
    (3, "Bronze", 50, 7, 0.0),
    (4, "Silver", 100, 7, 0.0),
    (5, "Gold", 250, 7, 0.0),
    (6, "Platinum", 500, 7, 0.0),
    (7, "Pro", 1000, 7, 0.0),
    (8, "Advanced", 2500, 7, 0.0),
    (9, "Premium", 5000, 7, 0.0),
    (10, "Elite", 10000, 7, 0.0),
    (11, "VIP", 15000, 7, 0.0),
    (12, "Quantum", 20000, 7, 0.0),
]

def seed_plans():
    with SessionLocal() as db:
        for pid, name, amount, days, rate in PLANS:
            if not db.scalar(select(InvestmentPlan).where(InvestmentPlan.id == pid)):
                db.add(InvestmentPlan(id=pid, name=name, amount=amount, duration_days=days,
                                      target_rate=rate, is_active=True))
        db.commit()

seed_plans()

def keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 خطط الاستثمار"), KeyboardButton(text="➕ الإيداع")],
            [KeyboardButton(text="➖ السحب"), KeyboardButton(text="💼 رصيدي")],
            [KeyboardButton(text="📊 استثماراتي"), KeyboardButton(text="🤖 حالة النظام")],
            [KeyboardButton(text="🌐 اللغة"), KeyboardButton(text="ℹ️ معلومات")],
        ],
        resize_keyboard=True,
    )

def payment_keyboard(prefix: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 USDT", callback_data=f"{prefix}:USDT")],
        [InlineKeyboardButton(text="🔵 USDC", callback_data=f"{prefix}:USDC")],
        [InlineKeyboardButton(text="🟠 BTC", callback_data=f"{prefix}:BTC")],
        [InlineKeyboardButton(text="🔷 ETH", callback_data=f"{prefix}:ETH")],
    ])

def payment_details(asset: str):
    data = {
        "USDT": (settings.usdt_network, settings.usdt_address),
        "USDC": (settings.usdc_network, settings.usdc_address),
        "BTC": (settings.btc_network, settings.btc_address),
        "ETH": (settings.eth_network, settings.eth_address),
    }
    return data[asset]

async def ensure_user(message: Message):
    uid = message.from_user.id
    username = message.from_user.username
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.telegram_id == uid))
        if not user:
            db.add(User(telegram_id=uid, username=username))
            db.add(Balance(telegram_id=uid, balance=0.0))
            db.commit()

@dp.message(CommandStart())
async def start(message: Message):
    await ensure_user(message)
    await message.answer(
        "🚀 مرحبًا بك في Quantum Grow\n\n"
        "منصة لإدارة طلبات الاستثمار والحساب.\n"
        "⚠️ الاستثمارات تنطوي على مخاطر ولا توجد أرباح مضمونة.\n\n"
        "اختر من القائمة:",
        reply_markup=keyboard(),
    )

@dp.message(F.text == "💰 خطط الاستثمار")
async def plans(message: Message):
    with SessionLocal() as db:
        rows = db.scalars(select(InvestmentPlan).where(InvestmentPlan.is_active == True).order_by(InvestmentPlan.amount)).all()
    text = "💰 خطط الاستثمار\n\n"
    for p in rows:
        text += f"🔹 {p.name}\n💵 الحد الأدنى: {p.amount:,.2f} USDT\n⏱ المدة: {p.duration_days} أيام\n━━━━━━━━━━━━━━\n"
    text += "\n⚠️ هذه الخطط ليست وعدًا بعائد ثابت. الأداء والنتيجة يخضعان لشروط الخدمة ومخاطر السوق."
    await message.answer(text)

@dp.message(F.text == "➕ الإيداع")
async def deposit(message: Message):
    await ensure_user(message)
    await message.answer("➕ الإيداع\n\nاختر العملة:", reply_markup=payment_keyboard("dep"))

@dp.callback_query(F.data.startswith("dep:"))
async def deposit_currency(callback):
    asset = callback.data.split(":", 1)[1]
    network, address = payment_details(asset)
    if not address:
        await callback.message.answer(f"⚠️ لم يتم إعداد عنوان {asset} بعد. تواصل مع الإدارة.")
    else:
        await callback.message.answer(
            f"➕ إيداع {asset}\n\n"
            f"🌐 الشبكة: {network}\n"
            f"📍 العنوان:\n{address}\n\n"
            "بعد التحويل، أرسل رقم المعاملة (TX Hash) إلى الإدارة لإتمام المراجعة."
        )
    await callback.answer()

@dp.message(F.text == "➖ السحب")
async def withdrawal(message: Message):
    await ensure_user(message)
    await message.answer(
        "➖ السحب\n\n"
        "لإنشاء طلب سحب، أرسل رسالة بهذا الشكل:\n"
        "/withdraw USDT TRC20 100 YOUR_WALLET_ADDRESS"
    )

@dp.message(Command("withdraw"))
async def withdraw_command(message: Message):
    parts = message.text.split(maxsplit=4)
    if len(parts) != 5:
        await message.answer("الصيغة الصحيحة:\n/withdraw USDT TRC20 100 YOUR_WALLET_ADDRESS")
        return
    _, asset, network, amount_s, wallet = parts
    try:
        amount = float(amount_s)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ المبلغ غير صحيح.")
        return
    with SessionLocal() as db:
        bal = db.scalar(select(Balance).where(Balance.telegram_id == message.from_user.id))
        if not bal or bal.balance < amount:
            await message.answer("❌ الرصيد المتاح غير كافٍ.")
            return
        req = WithdrawalRequest(telegram_id=message.from_user.id, asset=asset.upper(),
                                network=network, amount=amount, wallet_address=wallet)
        db.add(req)
        db.commit()
        rid = req.id
    await message.answer(f"✅ تم إنشاء طلب السحب رقم #{rid}. سيتم مراجعته قبل التنفيذ.")

@dp.message(F.text == "💼 رصيدي")
async def balance(message: Message):
    await ensure_user(message)
    with SessionLocal() as db:
        bal = db.scalar(select(Balance).where(Balance.telegram_id == message.from_user.id))
    await message.answer(f"💼 رصيد الحساب: {(bal.balance if bal else 0):,.2f} USDT")

@dp.message(F.text == "📊 استثماراتي")
async def investments(message: Message):
    with SessionLocal() as db:
        rows = db.scalars(select(Investment).where(Investment.telegram_id == message.from_user.id)).all()
    if not rows:
        await message.answer("📊 لا توجد استثمارات مسجلة على حسابك.")
        return
    text = "📊 استثماراتي\n\n"
    for x in rows:
        text += f"#{x.id} — {x.amount:,.2f} USDT — {x.status}\n"
    await message.answer(text)

@dp.message(F.text == "🤖 حالة النظام")
async def status(message: Message):
    await message.answer("🤖 حالة النظام\n\n🟢 البوت يعمل ويستقبل الطلبات.")

@dp.message(F.text == "🌐 اللغة")
async def language(message: Message):
    await message.answer("🌐 اللغة\n\n🇸🇦 العربية\n🇬🇧 English\n\nواجهة English الكاملة نضيفها بعد استقرار النسخة العربية.")

@dp.message(F.text == "ℹ️ معلومات")
async def about(message: Message):
    await message.answer(
        "🚀 Quantum Grow\n\n"
        "إدارة حسابات وطلبات إيداع وسحب واستثمار.\n"
        "⚠️ لا توجد أرباح مضمونة، وأي عملية مالية تخضع للمراجعة وشروط الخدمة."
    )

async def main():
    print("Quantum Grow bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

