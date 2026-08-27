
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from sqlalchemy import select

from .config import settings
from .db import Base, SessionLocal, engine
from .models import DemoBalance, User, InvestmentPlan


bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher()

Base.metadata.create_all(bind=engine)
def seed_investment_plans():
    plans = [
        (1, "Starter", 10),
        (2, "Basic", 25),
        (3, "Bronze", 50),
        (4, "Silver", 100),
        (5, "Gold", 250),
        (6, "Platinum", 500),
        (7, "Pro", 1000),
        (8, "Advanced", 2500),
        (9, "Premium", 5000),
        (10, "Elite", 10000),
        (11, "VIP", 15000),
        (12, "Quantum", 20000),
    ]

    with SessionLocal() as db:
        for plan_id, name, amount in plans:
            existing = db.scalar(
                select(InvestmentPlan).where(
                    InvestmentPlan.id == plan_id
                )
            )

            if not existing:
                db.add(
                    InvestmentPlan(
                        id=plan_id,
                        name=name,
                        amount=amount,
                        duration_days=7,
                        target_rate=0.18,
                        is_active=True,
                    )
                )

        db.commit()


seed_investment_plans()

def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💰 خطط الاستثمار"),
                KeyboardButton(text="➕ الإيداع"),
            ],
            [
                KeyboardButton(text="➖ السحب"),
                KeyboardButton(text="💼 رصيدي"),
            ],
            [
                KeyboardButton(text="📊 استثماراتي"),
                KeyboardButton(text="🤖 حالة AI"),
            ],
            [
                KeyboardButton(text="🌐 اللغة"),
                KeyboardButton(text="ℹ️ معلومات المشروع"),
            ],
        ],
        resize_keyboard=True
    )
    @dp.message(F.text == "💰 خطط الاستثمار")
    async def investment_plans(message: Message):
    with SessionLocal() as db:
        plans = db.scalars(
            select(InvestmentPlan).where(
                InvestmentPlan.is_active == True
            ).order_by(InvestmentPlan.amount)
        ).all()

    if not plans:
        await message.answer("لا توجد خطط استثمار متاحة حاليًا.")
        return

    text = "💰 خطط Quantum Grow\n\n"

    for plan in plans:
        expected = plan.amount * plan.target_rate

        text += (
            f"🔹 {plan.name}\n"
            f"💵 المبلغ: {plan.amount:,.2f} USDT\n"
            f"⏱ المدة المستهدفة: {plan.duration_days} أيام\n"
            f"📈 العائد المستهدف: {plan.target_rate * 100:.0f}%\n"
            f"💰 العائد المستهدف: {expected:,.2f} USDT\n"
            f"━━━━━━━━━━━━━━\n"
        )

    text += (
        "\n⚠️ ملاحظة مهمة:\n"
        "الدورة المستهدفة لمدة 7 أيام، والعائد المستهدف 18%. "
        "النتيجة الفعلية تعتمد على أداء النظام وظروف السوق. "
        "قد ينطبق برنامج التعويض وفق شروط الخدمة المعلنة."
    )

    await message.answer(text)


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
        "هذه نسخة تجريبية من المنصة.\n"
        "لا توجد أموال حقيقية في هذه النسخة.\n\n"
        "اختر من القائمة:",
        reply_markup=main_keyboard(),
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


@dp.message(F.text == "📈 التداول التجريبي")
async def demo_trading(message: Message):
    await message.answer(
        "📈 التداول التجريبي\n\n"
        "هذه الخاصية مخصصة للتجربة فقط.\n"
        "يمكننا لاحقًا إضافة شاشة للأصول والأسعار "
        "وأوامر الشراء والبيع التجريبية."
    )


@dp.message(F.text == "🌐 اللغة")
async def language(message: Message):
    await message.answer(
        "🌐 اللغة / Language\n\n"
        "🇸🇦 العربية\n"
        "🇬🇧 English\n\n"
        "دعم اللغتين سيتم تفعيله في الواجهة التالية."
    )


@dp.message(F.text == "ℹ️ معلومات المشروع")
async def about(message: Message):
    await message.answer(
        "🚀 Quantum Grow\n\n"
        "منصة تجريبية لواجهة التداول والاستثمار.\n\n"
        "⚠️ هذه النسخة لا تستقبل أموالًا حقيقية "
        "ولا تنفذ عمليات مالية."
    )


async def main():
    print("Quantum Grow bot is starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
