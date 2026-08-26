from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy import select

from .config import settings
from .db import Base, SessionLocal, engine
from .models import DemoBalance, User


bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher()


Base.metadata.create_all(bind=engine)


@dp.message(CommandStart())
async def start(message: Message):
    telegram_id = message.from_user.id
    username = message.from_user.username

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )

        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                language="ar",
            )
            db.add(user)

            balance = DemoBalance(
                telegram_id=telegram_id,
                balance=0.0,
                currency="USDT",
            )
            db.add(balance)
            db.commit()

    await message.answer(
        "مرحبًا بك في Quantum Grow 🚀\n\n"
        "هذه نسخة تجريبية من المنصة.\n\n"
        "اختر من القائمة:\n"
        "💰 الرصيد التجريبي\n"
        "🌐 اللغة\n"
        "ℹ️ معلومات المشروع"
    )


@dp.message(F.text == "💰 الرصيد التجريبي")
async def demo_balance(message: Message):
    telegram_id = message.from_user.id

    with SessionLocal() as db:
        balance = db.scalar(
            select(DemoBalance).where(
                DemoBalance.telegram_id == telegram_id
            )
        )

    amount = balance.balance if balance else 0.0

    await message.answer(
        f"💰 رصيدك التجريبي:\n\n"
        f"{amount:.2f} USDT\n\n"
        "هذا الرصيد تجريبي ولا يمثل أموالًا حقيقية."
    )


@dp.message(F.text == "🌐 اللغة")
async def language(message: Message):
    await message.answer(
        "🌐 Language / اللغة\n\n"
        "🇸🇦 العربية\n"
        "🇬🇧 English"
    )


@dp.message(F.text == "ℹ️ معلومات المشروع")
async def about(message: Message):
    await message.answer(
        "🚀 Quantum Grow\n\n"
        "منصة تجريبية لواجهة تداول واستثمار.\n\n"
        "⚠️ هذه النسخة لا تستقبل أموالًا حقيقية "
        "ولا تنفذ عمليات مالية."
    )


async def main():
    print("Quantum Grow bot is starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
