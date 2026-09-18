import asyncio
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    Message,
)
from sqlalchemy import select

from .config import settings
from .db import Base, SessionLocal, engine
from .models import (
    DemoBalance,
    DepositRequest,
    Investment,
    InvestmentPlan,
    User,
    WithdrawalRequest,
)


Base.metadata.create_all(bind=engine)

bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher()


PLANS = [
    (1, "Starter", 10, 7, 0.18),
    (2, "Basic", 25, 7, 0.18),
    (3, "Bronze", 50, 7, 0.18),
    (4, "Silver", 100, 7, 0.18),
    (5, "Gold", 250, 7, 0.18),
    (6, "Platinum", 500, 7, 0.18),
    (7, "Pro", 1000, 7, 0.18),
    (8, "Advanced", 2500, 7, 0.18),
    (9, "Premium", 5000, 7, 0.18),
    (10, "Elite", 10000, 7, 0.18),
    (11, "VIP", 15000, 7, 0.18),
    (12, "Quantum", 20000, 7, 0.18),
]


def seed_plans():
    with SessionLocal() as db:
        for pid, name, amount, days, rate in PLANS:
            plan = db.scalar(
                select(InvestmentPlan).where(
                    InvestmentPlan.id == pid
                )
            )

            if not plan:
                db.add(
                    InvestmentPlan(
                        id=pid,
                        name=name,
                        amount=amount,
                        duration_days=days,
                        target_rate=rate,
                        is_active=True,
                    )
                )
            else:
                # Keep the existing plan synchronized
                plan.name = name
                plan.amount = amount
                plan.duration_days = days
                plan.target_rate = rate
                plan.is_active = True

        db.commit()


seed_plans()


def keyboard():
    buttons = [
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
            KeyboardButton(text="🤖 حالة النظام"),
        ],
        [
            KeyboardButton(text="🌐 اللغة"),
            KeyboardButton(text="ℹ️ معلومات"),
        ],
    ]

    if settings.admin_telegram_id:
        buttons.append(
            [KeyboardButton(text="👨‍💼 لوحة المسؤول")]
        )

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
    )


def payment_keyboard(prefix: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🟢 USDT",
                    callback_data=f"{prefix}:USDT",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔵 USDC",
                    callback_data=f"{prefix}:USDC",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🟠 BTC",
                    callback_data=f"{prefix}:BTC",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔷 ETH",
                    callback_data=f"{prefix}:ETH",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🇸🇾 شام كاش",
                    callback_data=f"{prefix}:SHAM_CASH",
                )
            ],
        ]
    )


def payment_details(asset: str):
    data = {
        "USDT": (
            settings.usdt_network,
            settings.usdt_address,
        ),
        "USDC": (
            settings.usdc_network,
            settings.usdc_address,
        ),
        "BTC": (
            settings.btc_network,
            settings.btc_address,
        ),
        "ETH": (
            settings.eth_network,
            settings.eth_address,
        ),
        "SHAM_CASH": (
            "Sham Cash",
            settings.sham_cash_id,
        ),
    }

    return data.get(asset, ("", ""))


async def ensure_user(message: Message):
    uid = message.from_user.id
    username = message.from_user.username

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.telegram_id == uid)
        )

        if not user:
            db.add(
                User(
                    telegram_id=uid,
                    username=username,
                )
            )

        balance = db.scalar(
            select(DemoBalance).where(
                DemoBalance.telegram_id == uid
            )
        )

        if not balance:
            db.add(
                DemoBalance(
                    telegram_id=uid,
                    balance=0.0,
                )
            )

        db.commit()


def is_admin(user_id: int) -> bool:
    return (
        settings.admin_telegram_id != 0
        and user_id == settings.admin_telegram_id
    )


async def send_admin_message(text: str, reply_markup=None):
    if not settings.admin_telegram_id:
        return

    await bot.send_message(
        chat_id=settings.admin_telegram_id,
        text=text,
        reply_markup=reply_markup,
    )


# =========================================================
# INVESTMENT SETTLEMENT
# =========================================================

async def settle_finished_investments():
    """
    Finds investments whose 7-day period has ended,
    returns the principal + configured target profit
    to the user's available balance, and marks them completed.
    """

    now = datetime.utcnow()

    with SessionLocal() as db:
        investments = db.scalars(
            select(Investment).where(
                Investment.status == "active",
                Investment.ends_at <= now,
            )
        ).all()

        completed_users = []

        for investment in investments:
            balance = db.scalar(
                select(DemoBalance).where(
                    DemoBalance.telegram_id == investment.telegram_id
                )
            )

            if not balance:
                balance = DemoBalance(
                    telegram_id=investment.telegram_id,
                    balance=0.0,
                )
                db.add(balance)

            total_return = (
                investment.amount
                + investment.target_profit
            )

            balance.balance += total_return

            investment.status = "completed"
            investment.completed_at = now

            completed_users.append(
                (
                    investment.telegram_id,
                    investment.id,
                    investment.amount,
                    investment.target_profit,
                    total_return,
                )
            )

        db.commit()

    for (
        user_id,
        investment_id,
        principal,
        profit,
        total,
    ) in completed_users:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=(
                    "🎉 انتهت دورة الاستثمار\n\n"
                    f"🆔 الاستثمار: #{investment_id}\n"
                    f"💰 أصل الاستثمار: {principal:,.2f} USDT\n"
                    f"📈 العائد المستهدف: {profit:,.2f} USDT\n"
                    f"💵 المبلغ المعاد للرصد: {total:,.2f} USDT\n\n"
                    "✅ أصبح المبلغ متاحًا في رصيدك."
                ),
            )
        except Exception:
            pass


async def investment_settlement_loop():
    while True:
        try:
            await settle_finished_investments()
        except Exception as exc:
            print(
                f"Investment settlement error: {exc}"
            )

        await asyncio.sleep(60)


# =========================================================
# START
# =========================================================

@dp.message(CommandStart())
async def start(message: Message):
    await ensure_user(message)

    await message.answer(
        "🚀 مرحبًا بك في Quantum Grow\n\n"
        "منصة لإدارة الحسابات والإيداعات "
        "والسحوبات والاستثمارات.\n\n"
        "⚠️ الاستثمارات تنطوي على مخاطر، "
        "والعائد المعروض هو عائد مستهدف وفق إعدادات الخطة "
        "وليس ضمانًا لنتيجة السوق.\n\n"
        "اختر من القائمة:",
        reply_markup=keyboard(),
    )


# =========================================================
# INVESTMENT PLANS
# =========================================================

def plan_keyboard(plans):
    rows = []

    for plan in plans:
        rows.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"💰 {plan.name} — "
                        f"{plan.amount:,.0f} USDT"
                    ),
                    callback_data=f"plan:{plan.id}",
                )
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=rows
    )


@dp.message(F.text == "💰 خطط الاستثمار")
async def plans(message: Message):
    await ensure_user(message)

    with SessionLocal() as db:
        rows = db.scalars(
            select(InvestmentPlan)
            .where(InvestmentPlan.is_active == True)
            .order_by(InvestmentPlan.amount)
        ).all()

    text = (
        "💰 خطط الاستثمار\n\n"
        "اختر الخطة التي تريد الاطلاع عليها:\n\n"
    )

    for p in rows:
        target_profit = p.amount * p.target_rate
        total_target = p.amount + target_profit

        text += (
            f"🔹 {p.name}\n"
            f"💵 الاستثمار: {p.amount:,.2f} USDT\n"
            f"⏱ المدة: {p.duration_days} أيام\n"
            f"📈 العائد المستهدف: "
            f"{p.target_rate * 100:.0f}%\n"
            f"🎯 الإجمالي المستهدف: "
            f"{total_target:,.2f} USDT\n"
            "━━━━━━━━━━━━━━\n"
        )

    text += (
        "\n⚠️ العائد المستهدف ليس ضمانًا للربح. "
        "النتيجة الفعلية تعتمد على أداء النظام "
        "وظروف السوق وشروط الخدمة."
    )

    await message.answer(
        text,
        reply_markup=plan_keyboard(rows),
    )


# =========================================================
# PLAN DETAILS
# =========================================================

@dp.callback_query(F.data.startswith("plan:"))
async def plan_details_callback(callback):
    plan_id = int(
        callback.data.split(":")[1]
    )

    with SessionLocal() as db:
        plan = db.scalar(
            select(InvestmentPlan).where(
                InvestmentPlan.id == plan_id,
                InvestmentPlan.is_active == True,
            )
        )

    if not plan:
        await callback.answer(
            "الخطة غير موجودة.",
            show_alert=True,
        )
        return

    target_profit = (
        plan.amount * plan.target_rate
    )

    total_target = (
        plan.amount + target_profit
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 شراء الخطة من الرصيد",
                    callback_data=f"buyplan:{plan.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 العودة للخطط",
                    callback_data="backplans",
                )
            ],
        ]
    )

    await callback.message.answer(
        "📋 تفاصيل الخطة\n\n"
        f"🔹 الخطة: {plan.name}\n"
        f"💵 المبلغ: {plan.amount:,.2f} USDT\n"
        f"⏱ المدة: {plan.duration_days} أيام\n"
        f"📈 العائد المستهدف: "
        f"{plan.target_rate * 100:.0f}%\n"
        f"💰 العائد المستهدف: "
        f"{target_profit:,.2f} USDT\n"
        f"🎯 الإجمالي المستهدف: "
        f"{total_target:,.2f} USDT\n\n"
        "🔒 بعد شراء الخطة يصبح المبلغ المستثمر "
        "محجوزًا حتى نهاية الدورة.\n\n"
        "⚠️ العائد المستهدف ليس ضمانًا للربح، "
        "والنتيجة الفعلية تعتمد على أداء النظام "
        "وظروف السوق وشروط الخدمة.",
        reply_markup=keyboard,
    )

    await callback.answer()


@dp.callback_query(F.data == "backplans")
async def back_to_plans(callback):
    with SessionLocal() as db:
        rows = db.scalars(
            select(InvestmentPlan)
            .where(InvestmentPlan.is_active == True)
            .order_by(InvestmentPlan.amount)
        ).all()

    await callback.message.answer(
        "💰 اختر الخطة:",
        reply_markup=plan_keyboard(rows),
    )

    await callback.answer()


# =========================================================
# BUY PLAN FROM BALANCE
# =========================================================

@dp.callback_query(F.data.startswith("buyplan:"))
async def buy_plan(callback):
    plan_id = int(
        callback.data.split(":")[1]
    )

    user_id = callback.from_user.id

    with SessionLocal() as db:
        plan = db.scalar(
            select(InvestmentPlan).where(
                InvestmentPlan.id == plan_id,
                InvestmentPlan.is_active == True,
            )
        )

        if not plan:
            await callback.answer(
                "الخطة غير موجودة.",
                show_alert=True,
            )
            return

        balance = db.scalar(
            select(DemoBalance).where(
                DemoBalance.telegram_id == user_id
            )
        )

        if not balance:
            balance = DemoBalance(
                telegram_id=user_id,
                balance=0.0,
            )
            db.add(balance)
            db.commit()

        if balance.balance < plan.amount:
            current = balance.balance
            required = plan.amount - current

            await callback.message.answer(
                "❌ لا يمكن شراء الخطة.\n\n"
                f"💰 سعر الخطة: {plan.amount:,.2f} USDT\n"
                f"💼 رصيدك المتاح: {current:,.2f} USDT\n"
                f"📥 المبلغ المطلوب: {required:,.2f} USDT\n\n"
                "يمكنك إيداع المبلغ المطلوب ثم شراء الخطة."
            )

            await callback.answer(
                "الرصيد غير كافٍ.",
                show_alert=True,
            )
            return

        now = datetime.utcnow()
        ends_at = now + timedelta(
            days=plan.duration_days
        )

        target_profit = (
            plan.amount * plan.target_rate
        )

        # Deduct from available balance.
        # The amount is now locked inside the investment.
        balance.balance -= plan.amount

        investment = Investment(
            telegram_id=user_id,
            plan_id=plan.id,
            amount=plan.amount,
            target_profit=target_profit,
            status="active",
            started_at=now,
            ends_at=ends_at,
        )

        db.add(investment)
        db.commit()

        investment_id = investment.id
        remaining_balance = balance.balance

    await callback.message.answer(
        "✅ تم شراء الخطة بنجاح\n\n"
        f"🆔 رقم الاستثمار: #{investment_id}\n"
        f"🔹 الخطة: {plan.name}\n"
        f"💵 المبلغ المستثمر: "
        f"{plan.amount:,.2f} USDT\n"
        f"⏱ المدة: {plan.duration_days} أيام\n"
        f"📅 تاريخ البداية: "
        f"{now.strftime('%Y-%m-%d %H:%M')} UTC\n"
        f"📅 تاريخ الانتهاء: "
        f"{ends_at.strftime('%Y-%m-%d %H:%M')} UTC\n\n"
        f"📈 العائد المستهدف: "
        f"{target_profit:,.2f} USDT\n\n"
        "🔒 تم حجز مبلغ الاستثمار حتى انتهاء الدورة.\n"
        "💼 رصيدك المتاح الآن: "
        f"{remaining_balance:,.2f} USDT\n\n"
        "⚠️ العائد المستهدف ليس ضمانًا لنتيجة السوق."
    )

    await callback.answer(
        "تم شراء الخطة."
    )


# =========================================================
# DEPOSIT
# =========================================================

@dp.message(F.text == "➕ الإيداع")
async def deposit(message: Message):
    await ensure_user(message)

    await message.answer(
        "➕ الإيداع\n\n"
        "اختر طريقة الدفع:",
        reply_markup=payment_keyboard("dep"),
    )


@dp.callback_query(F.data.startswith("dep:"))
async def deposit_currency(callback):
    asset = callback.data.split(":", 1)[1]

    network, address = payment_details(asset)

    if not address:
        await callback.message.answer(
            f"⚠️ لم يتم إعداد {asset} بعد.\n"
            "تواصل مع الإدارة."
        )

    elif asset == "SHAM_CASH":
        await callback.message.answer(
            "🇸🇾 إيداع عبر شام كاش\n\n"
            f"🆔 معرّف الاستلام:\n{address}\n\n"
            "بعد إرسال المبلغ، استخدم الأمر التالي "
            "لتسجيل العملية:\n\n"
            "/deposit SHAM_CASH SHAM_CASH المبلغ رقم_المرجع"
        )

    else:
        await callback.message.answer(
            f"➕ إيداع {asset}\n\n"
            f"🌐 الشبكة: {network}\n"
            f"📍 العنوان:\n{address}\n\n"
            "بعد التحويل استخدم الأمر التالي:\n\n"
            f"/deposit {asset} {network} المبلغ TX_HASH\n\n"
            "مثال:\n"
            f"/deposit {asset} {network} 100 TX123456"
        )

    await callback.answer()


@dp.message(Command("deposit"))
async def deposit_command(message: Message):
    parts = message.text.split(maxsplit=4)

    if len(parts) != 5:
        await message.answer(
            "❌ الصيغة غير صحيحة.\n\n"
            "للعملات الرقمية:\n"
            "/deposit USDT TRC20 100 TX_HASH\n\n"
            "لشام كاش:\n"
            "/deposit SHAM_CASH SHAM_CASH 100 REFERENCE"
        )
        return

    _, asset, network, amount_s, reference = parts

    asset = asset.upper()
    network = network.upper()

    if asset not in [
        "USDT",
        "USDC",
        "BTC",
        "ETH",
        "SHAM_CASH",
    ]:
        await message.answer(
            "❌ طريقة الدفع غير مدعومة."
        )
        return

    try:
        amount = float(amount_s)

        if amount <= 0:
            raise ValueError

    except ValueError:
        await message.answer(
            "❌ المبلغ غير صحيح."
        )
        return

    await ensure_user(message)

    with SessionLocal() as db:
        req = DepositRequest(
            telegram_id=message.from_user.id,
            asset=asset,
            network=network,
            amount=amount,
            tx_hash=reference,
            status="pending",
        )

        db.add(req)
        db.commit()

        request_id = req.id

    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ قبول الإيداع",
                    callback_data=f"depapprove:{request_id}",
                ),
                InlineKeyboardButton(
                    text="❌ رفض",
                    callback_data=f"depreject:{request_id}",
                ),
            ]
        ]
    )

    username = (
        message.from_user.username
        or "بدون اسم"
    )

    admin_text = (
        "📥 طلب إيداع جديد\n\n"
        f"🆔 الطلب: #{request_id}\n"
        f"👤 المستخدم: @{username}\n"
        f"Telegram ID: {message.from_user.id}\n"
        f"💳 الطريقة: {asset}\n"
        f"🌐 الشبكة: {network}\n"
        f"💰 المبلغ: {amount:,.2f}\n"
        f"🧾 المرجع / TX Hash:\n{reference}\n\n"
        "اختر الإجراء:"
    )

    await send_admin_message(
        admin_text,
        reply_markup=admin_keyboard,
    )

    await message.answer(
        f"✅ تم تسجيل طلب الإيداع #{request_id}.\n\n"
        "⏳ الطلب بانتظار مراجعة الإدارة."
    )


# =========================================================
# ADMIN DEPOSIT ACTIONS
# =========================================================

@dp.callback_query(F.data.startswith("depapprove:"))
async def approve_deposit(callback):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "⛔ غير مصرح لك.",
            show_alert=True,
        )
        return

    request_id = int(
        callback.data.split(":")[1]
    )

    with SessionLocal() as db:
        req = db.scalar(
            select(DepositRequest).where(
                DepositRequest.id == request_id
            )
        )

        if not req:
            await callback.answer(
                "الطلب غير موجود.",
                show_alert=True,
            )
            return

        if req.status != "pending":
            await callback.answer(
                "تمت معالجة هذا الطلب مسبقًا.",
                show_alert=True,
            )
            return

        bal = db.scalar(
            select(DemoBalance).where(
                DemoBalance.telegram_id == req.telegram_id
            )
        )

        if not bal:
            bal = DemoBalance(
                telegram_id=req.telegram_id,
                balance=0.0,
            )
            db.add(bal)

        bal.balance += req.amount
        req.status = "approved"

        db.commit()

        user_id = req.telegram_id
        amount = req.amount
        asset = req.asset

    await bot.send_message(
        chat_id=user_id,
        text=(
            "✅ تم قبول الإيداع\n\n"
            f"🆔 الطلب: #{request_id}\n"
            f"💳 العملة: {asset}\n"
            f"💰 المبلغ: {amount:,.2f}\n\n"
            "تم تحديث رصيد حسابك."
        ),
    )

    await callback.message.edit_text(
        callback.message.text
        + "\n\n✅ تم قبول الطلب وتحديث الرصيد."
    )

    await callback.answer(
        "تم قبول الإيداع."
    )


@dp.callback_query(F.data.startswith("depreject:"))
async def reject_deposit(callback):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "⛔ غير مصرح لك.",
            show_alert=True,
        )
        return

    request_id = int(
        callback.data.split(":")[1]
    )

    with SessionLocal() as db:
        req = db.scalar(
            select(DepositRequest).where(
                DepositRequest.id == request_id
            )
        )

        if not req:
            await callback.answer(
                "الطلب غير موجود.",
                show_alert=True,
            )
            return

        if req.status != "pending":
            await callback.answer(
                "تمت معالجة هذا الطلب مسبقًا.",
                show_alert=True,
            )
            return

        req.status = "rejected"
        db.commit()

        user_id = req.telegram_id

    await bot.send_message(
        chat_id=user_id,
        text=(
            f"❌ تم رفض طلب الإيداع #{request_id}.\n\n"
            "يرجى التواصل مع الإدارة إذا كنت تعتقد أن هناك خطأ."
        ),
    )

    await callback.message.edit_text(
        callback.message.text
        + "\n\n❌ تم رفض الطلب."
    )

    await callback.answer(
        "تم رفض الإيداع."
    )


# =========================================================
# BALANCE
# =========================================================

@dp.message(F.text == "💼 رصيدي")
async def balance(message: Message):
    await ensure_user(message)

    with SessionLocal() as db:
        bal = db.scalar(
            select(DemoBalance).where(
                DemoBalance.telegram_id == message.from_user.id
            )
        )

        active_investments = db.scalars(
            select(Investment).where(
                Investment.telegram_id == message.from_user.id,
                Investment.status == "active",
            )
        ).all()

    current_balance = (
        bal.balance if bal else 0.0
    )

    locked = sum(
        inv.amount
        for inv in active_investments
    )

    await message.answer(
        "💼 رصيد الحساب\n\n"
        f"💵 الرصيد المتاح: "
        f"{current_balance:,.2f} USDT\n"
        f"🔒 المبلغ المستثمر والمحجوز: "
        f"{locked:,.2f} USDT\n\n"
        f"📊 الاستثمارات النشطة: "
        f"{len(active_investments)}"
    )


# =========================================================
# WITHDRAWAL
# =========================================================

@dp.message(F.text == "➖ السحب")
async def withdrawal(message: Message):
    await ensure_user(message)

    await message.answer(
        "➖ السحب\n\n"
        "لإنشاء طلب سحب أرسل:\n\n"
        "/withdraw USDT TRC20 100 YOUR_WALLET_ADDRESS\n\n"
        "⚠️ لا يمكن سحب الأموال المحجوزة داخل "
        "استثمار نشط."
    )


@dp.message(Command("withdraw"))
async def withdraw_command(message: Message):
    parts = message.text.split(maxsplit=4)

    if len(parts) != 5:
        await message.answer(
            "❌ الصيغة الصحيحة:\n"
            "/withdraw USDT TRC20 100 YOUR_WALLET_ADDRESS"
        )
        return

    _, asset, network, amount_s, wallet = parts

    asset = asset.upper()

    allowed_assets = [
        "USDT",
        "USDC",
        "BTC",
        "ETH",
        "SHAM_CASH",
    ]

    if asset not in allowed_assets:
        await message.answer(
            "❌ عملة السحب غير مدعومة."
        )
        return

    try:
        amount = float(amount_s)

        if amount <= 0:
            raise ValueError

    except ValueError:
        await message.answer(
            "❌ المبلغ غير صحيح."
        )
        return

    await ensure_user(message)

    with SessionLocal() as db:
        bal = db.scalar(
            select(DemoBalance).where(
                DemoBalance.telegram_id == message.from_user.id
            )
        )

        if not bal or bal.balance < amount:
            available = (
                bal.balance if bal else 0.0
            )

            await message.answer(
                "❌ الرصيد المتاح غير كافٍ.\n\n"
                f"💼 المتاح: {available:,.2f} USDT\n"
                f"💸 المطلوب: {amount:,.2f} USDT\n\n"
                "الأموال الموجودة داخل الاستثمارات "
                "النشطة غير قابلة للسحب."
            )
            return

        req = WithdrawalRequest(
            telegram_id=message.from_user.id,
            asset=asset,
            network=network,
            amount=amount,
            wallet_address=wallet,
            status="pending",
        )

        db.add(req)
        db.commit()

        request_id = req.id

    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ قبول السحب",
                    callback_data=f"withapprove:{request_id}",
                ),
                InlineKeyboardButton(
                    text="❌ رفض",
                    callback_data=f"withreject:{request_id}",
                ),
            ]
        ]
    )

    username = (
        message.from_user.username
        or "بدون اسم"
    )

    admin_text = (
        "💸 طلب سحب جديد\n\n"
        f"🆔 الطلب: #{request_id}\n"
        f"👤 المستخدم: @{username}\n"
        f"Telegram ID: {message.from_user.id}\n"
        f"💳 العملة: {asset}\n"
        f"🌐 الشبكة: {network}\n"
        f"💰 المبلغ: {amount:,.2f}\n"
        f"📍 محفظة المستلم:\n{wallet}\n\n"
        "اختر الإجراء:"
    )

    await send_admin_message(
        admin_text,
        reply_markup=admin_keyboard,
    )

    await message.answer(
        f"✅ تم إنشاء طلب السحب #{request_id}.\n\n"
        "⏳ الطلب بانتظار مراجعة الإدارة."
    )


# =========================================================
# ADMIN WITHDRAWAL ACTIONS
# =========================================================

@dp.callback_query(F.data.startswith("withapprove:"))
async def approve_withdrawal(callback):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "⛔ غير مصرح لك.",
            show_alert=True,
        )
        return

    request_id = int(
        callback.data.split(":")[1]
    )

    with SessionLocal() as db:
        req = db.scalar(
            select(WithdrawalRequest).where(
                WithdrawalRequest.id == request_id
            )
        )

        if not req:
            await callback.answer(
                "الطلب غير موجود.",
                show_alert=True,
            )
            return

        if req.status != "pending":
            await callback.answer(
                "تمت معالجة هذا الطلب مسبقًا.",
                show_alert=True,
            )
            return

        bal = db.scalar(
            select(DemoBalance).where(
                DemoBalance.telegram_id == req.telegram_id
            )
        )

        if not bal or bal.balance < req.amount:
            await callback.answer(
                "الرصيد غير كافٍ.",
                show_alert=True,
            )
            return

        bal.balance -= req.amount
        req.status = "approved"

        db.commit()

        user_id = req.telegram_id
        amount = req.amount
        asset = req.asset

    await bot.send_message(
        chat_id=user_id,
        text=(
            "✅ تمت الموافقة على طلب السحب\n\n"
            f"🆔 الطلب: #{request_id}\n"
            f"💳 العملة: {asset}\n"
            f"💰 المبلغ: {amount:,.2f}\n\n"
            "سيتم تنفيذ التحويل ومشاركة TX Hash "
            "بعد إتمام العملية."
        ),
    )

    await callback.message.edit_text(
        callback.message.text
        + "\n\n✅ تمت الموافقة وخصم المبلغ من الرصيد."
    )

    await callback.answer(
        "تمت الموافقة على السحب."
    )


@dp.callback_query(F.data.startswith("withreject:"))
async def reject_withdrawal(callback):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "⛔ غير مصرح لك.",
            show_alert=True,
        )
        return

    request_id = int(
        callback.data.split(":")[1]
    )

    with SessionLocal() as db:
        req = db.scalar(
            select(WithdrawalRequest).where(
                WithdrawalRequest.id == request_id
            )
        )

        if not req:
            await callback.answer(
                "الطلب غير موجود.",
                show_alert=True,
            )
            return

        if req.status != "pending":
            await callback.answer(
                "تمت معالجة هذا الطلب مسبقًا.",
                show_alert=True,
            )
            return

        req.status = "rejected"
        db.commit()

        user_id = req.telegram_id

    await bot.send_message(
        chat_id=user_id,
        text=(
            f"❌ تم رفض طلب السحب #{request_id}.\n\n"
            "لم يتم خصم أي مبلغ من رصيدك."
        ),
    )

    await callback.message.edit_text(
        callback.message.text
        + "\n\n❌ تم رفض طلب السحب."
    )

    await callback.answer(
        "تم رفض السحب."
    )


# =========================================================
# ADMIN PANEL
# =========================================================

@dp.message(Command("admin"))
async def admin_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(
            "⛔ غير مصرح لك."
        )
        return

    await message.answer(
        "👨‍💼 لوحة المسؤول\n\n"
        "📥 /pending_deposits\n"
        "💸 /pending_withdrawals\n"
        "💰 /user_balance TELEGRAM_ID\n"
        "📊 /system"
    )


@dp.message(F.text == "👨‍💼 لوحة المسؤول")
async def admin_button(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(
            "⛔ غير مصرح لك."
        )
        return

    await message.answer(
        "👨‍💼 لوحة المسؤول\n\n"
        "📥 /pending_deposits\n"
        "💸 /pending_withdrawals\n"
        "💰 /user_balance TELEGRAM_ID\n"
        "📊 /system"
    )


@dp.message(Command("pending_deposits"))
async def pending_deposits(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(
            "⛔ غير مصرح لك."
        )
        return

    with SessionLocal() as db:
        rows = db.scalars(
            select(DepositRequest)
            .where(
                DepositRequest.status == "pending"
            )
            .order_by(DepositRequest.id.desc())
        ).all()

    if not rows:
        await message.answer(
            "📥 لا توجد طلبات إيداع معلقة."
        )
        return

    text = "📥 طلبات الإيداع المعلقة\n\n"

    for req in rows:
        text += (
            f"#{req.id} | {req.asset} | "
            f"{req.amount:,.2f}\n"
            f"👤 {req.telegram_id}\n"
            f"🌐 {req.network}\n"
            f"🧾 {req.tx_hash}\n"
            "━━━━━━━━━━━━━━\n"
        )

    await message.answer(text)


@dp.message(Command("pending_withdrawals"))
async def pending_withdrawals(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(
            "⛔ غير مصرح لك."
        )
        return

    with SessionLocal() as db:
        rows = db.scalars(
            select(WithdrawalRequest)
            .where(
                WithdrawalRequest.status == "pending"
            )
            .order_by(WithdrawalRequest.id.desc())
        ).all()

    if not rows:
        await message.answer(
            "💸 لا توجد طلبات سحب معلقة."
        )
        return

    text = "💸 طلبات السحب المعلقة\n\n"

    for req in rows:
        text += (
            f"#{req.id} | {req.asset} | "
            f"{req.amount:,.2f}\n"
            f"👤 {req.telegram_id}\n"
            f"🌐 {req.network}\n"
            f"📍 {req.wallet_address}\n"
            "━━━━━━━━━━━━━━\n"
        )

    await message.answer(text)


@dp.message(Command("user_balance"))
async def user_balance(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(
            "⛔ غير مصرح لك."
        )
        return

    parts = message.text.split()

    if len(parts) != 2:
        await message.answer(
            "الصيغة:\n/user_balance TELEGRAM_ID"
        )
        return

    try:
        telegram_id = int(parts[1])
    except ValueError:
        await message.answer(
            "❌ Telegram ID غير صحيح."
        )
        return

    with SessionLocal() as db:
        bal = db.scalar(
            select(DemoBalance).where(
                DemoBalance.telegram_id == telegram_id
            )
        )

        investments = db.scalars(
            select(Investment).where(
                Investment.telegram_id == telegram_id,
                Investment.status == "active",
            )
        ).all()

    amount = (
        bal.balance if bal else 0.0
    )

    locked = sum(
        inv.amount
        for inv in investments
    )

    await message.answer(
        f"💰 رصيد المستخدم\n\n"
        f"Telegram ID: {telegram_id}\n"
        f"💵 الرصيد المتاح: "
        f"{amount:,.2f} USDT\n"
        f"🔒 المبلغ المستثمر: "
        f"{locked:,.2f} USDT\n"
        f"📊 الاستثمارات النشطة: "
        f"{len(investments)}"
    )


@dp.message(Command("system"))
async def admin_system(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(
            "⛔ غير مصرح لك."
        )
        return

    with SessionLocal() as db:
        deposits = db.scalars(
            select(DepositRequest)
            .where(
                DepositRequest.status == "pending"
            )
        ).all()

        withdrawals = db.scalars(
            select(WithdrawalRequest)
            .where(
                WithdrawalRequest.status == "pending"
            )
        ).all()

        users = db.scalars(
            select(User)
        ).all()

        active_investments = db.scalars(
            select(Investment).where(
                Investment.status == "active"
            )
        ).all()

    await message.answer(
        "📊 حالة النظام\n\n"
        "🟢 البوت يعمل\n"
        f"👥 المستخدمون: {len(users)}\n"
        f"📥 إيداعات معلقة: {len(deposits)}\n"
        f"💸 سحوبات معلقة: {len(withdrawals)}\n"
        f"📊 استثمارات نشطة: "
        f"{len(active_investments)}"
    )


# =========================================================
# USER INVESTMENTS
# =========================================================

@dp.message(F.text == "📊 استثماراتي")
async def investments(message: Message):
    await ensure_user(message)

    await settle_finished_investments()

    with SessionLocal() as db:
        rows = db.scalars(
            select(Investment)
            .where(
                Investment.telegram_id
                == message.from_user.id
            )
            .order_by(Investment.id.desc())
        ).all()

        plans_map = {
            p.id: p
            for p in db.scalars(
                select(InvestmentPlan)
            ).all()
        }

    if not rows:
        await message.answer(
            "📊 استثماراتي\n\n"
            "لا توجد استثمارات مسجلة حاليًا."
        )
        return

    text = "📊 استثماراتي\n\n"

    now = datetime.utcnow()

    for inv in rows:
        plan = plans_map.get(inv.plan_id)

        plan_name = (
            plan.name
            if plan
            else f"Plan #{inv.plan_id}"
        )

        if inv.status == "active":
            remaining = inv.ends_at - now

            if remaining.total_seconds() > 0:
                days = remaining.days
                hours = (
                    remaining.seconds // 3600
                )

                text += (
                    f"🟢 #{inv.id} — {plan_name}\n"
                    f"💰 المبلغ: "
                    f"{inv.amount:,.2f} USDT\n"
                    f"🔒 الحالة: نشط ومحجوز\n"
                    f"⏳ المتبقي تقريبًا: "
                    f"{days} يوم و {hours} ساعة\n"
                    f"📅 الانتهاء: "
                    f"{inv.ends_at.strftime('%Y-%m-%d %H:%M')} UTC\n"
                    "━━━━━━━━━━━━━━\n"
                )
            else:
                text += (
                    f"🟡 #{inv.id} — {plan_name}\n"
                    "⏳ بانتظار التسوية...\n"
                    "━━━━━━━━━━━━━━\n"
                )

        elif inv.status == "completed":
            total = (
                inv.amount
                + inv.target_profit
            )

            text += (
                f"✅ #{inv.id} — {plan_name}\n"
                f"💰 الأصل: "
                f"{inv.amount:,.2f} USDT\n"
                f"📈 العائد المستهدف: "
                f"{inv.target_profit:,.2f} USDT\n"
                f"💵 الإجمالي المسوى: "
                f"{total:,.2f} USDT\n"
                "🔓 أصبحت الأموال متاحة.\n"
                "━━━━━━━━━━━━━━\n"
            )

    text += (
        "\n⚠️ العائد المذكور هو عائد مستهدف "
        "وليس ضمانًا للربح."
    )

    await message.answer(text)


# =========================================================
# STATUS / LANGUAGE / INFO
# =========================================================

@dp.message(F.text == "🤖 حالة النظام")
async def status(message: Message):
    await message.answer(
        "🤖 حالة النظام\n\n"
        "🟢 البوت يعمل ويستقبل الطلبات.\n"
        "🟢 تتم مراقبة الاستثمارات المنتهية "
        "وتسويتها تلقائيًا."
    )


@dp.message(F.text == "🌐 اللغة")
async def language(message: Message):
    await message.answer(
        "🌐 اللغة\n\n"
        "🇸🇦 العربية\n"
        "🇬🇧 English\n\n"
        "واجهة English الكاملة نضيفها "
        "بعد استقرار النسخة العربية."
    )


@dp.message(F.text == "ℹ️ معلومات")
async def about(message: Message):
    await message.answer(
        "🚀 Quantum Grow\n\n"
        "إدارة الحسابات والإيداعات والسحوبات "
        "والاستثمارات.\n\n"
        "📅 مدة الدورة: 7 أيام\n"
        "📈 العائد المستهدف حسب إعدادات الخطة.\n\n"
        "⚠️ لا توجد أرباح مضمونة، والنتيجة الفعلية "
        "تعتمد على أداء النظام وظروف السوق "
        "وشروط الخدمة."
    )


# =========================================================
# MAIN
# =========================================================

async def main():
    print("Quantum Grow bot is starting...")

    settlement_task = asyncio.create_task(
        investment_settlement_loop()
    )

    try:
        await dp.start_polling(bot)
    finally:
        settlement_task.cancel()

        try:
            await settlement_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
