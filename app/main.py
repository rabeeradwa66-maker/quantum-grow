import asyncio

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
    InvestmentPlan,
    User,
    WithdrawalRequest,
)


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
            if not db.scalar(
                select(InvestmentPlan).where(InvestmentPlan.id == pid)
            ):
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


# =========================
# START
# =========================

@dp.message(CommandStart())
async def start(message: Message):
    await ensure_user(message)

    await message.answer(
        "🚀 مرحبًا بك في Quantum Grow\n\n"
        "منصة لإدارة طلبات الاستثمار والحساب.\n\n"
        "⚠️ الاستثمارات تنطوي على مخاطر، "
        "ولا توجد أرباح مضمونة.\n\n"
        "اختر من القائمة:",
        reply_markup=keyboard(),
    )


# =========================
# INVESTMENT PLANS
# =========================

@dp.message(F.text == "💰 خطط الاستثمار")
async def plans(message: Message):
    with SessionLocal() as db:
        rows = db.scalars(
            select(InvestmentPlan)
            .where(InvestmentPlan.is_active == True)
            .order_by(InvestmentPlan.amount)
        ).all()

    text = "💰 خطط الاستثمار\n\n"

    for p in rows:
        text += (
            f"🔹 {p.name}\n"
            f"💵 الحد الأدنى: {p.amount:,.2f} USDT\n"
            f"⏱ المدة: {p.duration_days} أيام\n"
            "━━━━━━━━━━━━━━\n"
        )

    text += (
        "\n⚠️ هذه الخطط ليست وعدًا بعائد ثابت. "
        "الأداء والنتيجة يخضعان لشروط الخدمة ومخاطر السوق."
    )

    await message.answer(text)


# =========================
# DEPOSIT
# =========================

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

    if asset not in ["USDT", "USDC", "BTC", "ETH", "SHAM_CASH"]:
        await message.answer("❌ طريقة الدفع غير مدعومة.")
        return

    try:
        amount = float(amount_s)

        if amount <= 0:
            raise ValueError

    except ValueError:
        await message.answer("❌ المبلغ غير صحيح.")
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

    username = message.from_user.username or "بدون اسم"

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


# =========================
# ADMIN DEPOSIT ACTIONS
# =========================

@dp.callback_query(F.data.startswith("depapprove:"))
async def approve_deposit(callback):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "⛔ غير مصرح لك.",
            show_alert=True,
        )
        return

    request_id = int(callback.data.split(":")[1])

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

    await callback.answer("تم قبول الإيداع.")


@dp.callback_query(F.data.startswith("depreject:"))
async def reject_deposit(callback):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "⛔ غير مصرح لك.",
            show_alert=True,
        )
        return

    request_id = int(callback.data.split(":")[1])

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

    await callback.answer("تم رفض الإيداع.")


# =========================
# BALANCE
# =========================

@dp.message(F.text == "💼 رصيدي")
async def balance(message: Message):
    await ensure_user(message)

    with SessionLocal() as db:
        bal = db.scalar(
            select(DemoBalance).where(
                DemoBalance.telegram_id == message.from_user.id
            )
        )

    current_balance = bal.balance if bal else 0.0

    await message.answer(
        "💼 رصيد الحساب\n\n"
        f"💵 {current_balance:,.2f} USDT"
    )


# =========================
# WITHDRAWAL
# =========================

@dp.message(F.text == "➖ السحب")
async def withdrawal(message: Message):
    await ensure_user(message)

    await message.answer(
        "➖ السحب\n\n"
        "لإنشاء طلب سحب أرسل:\n\n"
        "/withdraw USDT TRC20 100 YOUR_WALLET_ADDRESS\n\n"
        "مثال:\n"
        "/withdraw USDT TRC20 100 TXyz123..."
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
        await message.answer("❌ المبلغ غير صحيح.")
        return

    await ensure_user(message)

    with SessionLocal() as db:
        bal = db.scalar(
            select(DemoBalance).where(
                DemoBalance.telegram_id == message.from_user.id
            )
        )

        if not bal or bal.balance < amount:
            await message.answer(
                "❌ الرصيد المتاح غير كافٍ."
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

    username = message.from_user.username or "بدون اسم"

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


# =========================
# ADMIN WITHDRAWAL ACTIONS
# =========================

@dp.callback_query(F.data.startswith("withapprove:"))
async def approve_withdrawal(callback):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "⛔ غير مصرح لك.",
            show_alert=True,
        )
        return

    request_id = int(callback.data.split(":")[1])

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

    await callback.answer("تمت الموافقة على السحب.")


@dp.callback_query(F.data.startswith("withreject:"))
async def reject_withdrawal(callback):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "⛔ غير مصرح لك.",
            show_alert=True,
        )
        return

    request_id = int(callback.data.split(":")[1])

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

    await callback.answer("تم رفض السحب.")


# =========================
# ADMIN PANEL
# =========================

@dp.message(Command("admin"))
async def admin_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ غير مصرح لك.")
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
        await message.answer("⛔ غير مصرح لك.")
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
        await message.answer("⛔ غير مصرح لك.")
        return

    with SessionLocal() as db:
        rows = db.scalars(
            select(DepositRequest)
            .where(DepositRequest.status == "pending")
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
        await message.answer("⛔ غير مصرح لك.")
        return

    with SessionLocal() as db:
        rows = db.scalars(
            select(WithdrawalRequest)
            .where(WithdrawalRequest.status == "pending")
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
        await message.answer("⛔ غير مصرح لك.")
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
        await message.answer("❌ Telegram ID غير صحيح.")
        return

    with SessionLocal() as db:
        bal = db.scalar(
            select(DemoBalance).where(
                DemoBalance.telegram_id == telegram_id
            )
        )

    amount = bal.balance if bal else 0.0

    await message.answer(
        f"💰 رصيد المستخدم\n\n"
        f"Telegram ID: {telegram_id}\n"
        f"الرصيد: {amount:,.2f} USDT"
    )


@dp.message(Command("system"))
async def admin_system(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ غير مصرح لك.")
        return

    with SessionLocal() as db:
        deposits = db.scalars(
            select(DepositRequest)
            .where(DepositRequest.status == "pending")
        ).all()

        withdrawals = db.scalars(
            select(WithdrawalRequest)
            .where(WithdrawalRequest.status == "pending")
        ).all()

        users = db.scalars(select(User)).all()

    await message.answer(
        "📊 حالة النظام\n\n"
        "🟢 البوت يعمل\n"
        f"👥 المستخدمون: {len(users)}\n"
        f"📥 إيداعات معلقة: {len(deposits)}\n"
        f"💸 سحوبات معلقة: {len(withdrawals)}"
    )


# =========================
# USER INVESTMENTS
# =========================

@dp.message(F.text == "📊 استثماراتي")
async def investments(message: Message):
    await ensure_user(message)

    await message.answer(
        "📊 استثماراتي\n\n"
        "لا توجد استثمارات مسجلة حاليًا على هذا الحساب."
    )


# =========================
# STATUS / LANGUAGE / INFO
# =========================

@dp.message(F.text == "🤖 حالة النظام")
async def status(message: Message):
    await message.answer(
        "🤖 حالة النظام\n\n"
        "🟢 البوت يعمل ويستقبل الطلبات."
    )


@dp.message(F.text == "🌐 اللغة")
async def language(message: Message):
    await message.answer(
        "🌐 اللغة\n\n"
        "🇸🇦 العربية\n"
        "🇬🇧 English\n\n"
        "واجهة English الكاملة نضيفها بعد استقرار النسخة العربية."
    )


@dp.message(F.text == "ℹ️ معلومات")
async def about(message: Message):
    await message.answer(
        "🚀 Quantum Grow\n\n"
        "إدارة حسابات وطلبات إيداع وسحب واستثمار.\n\n"
        "⚠️ لا توجد أرباح مضمونة، وأي عملية مالية "
        "تخضع للمراجعة وشروط الخدمة."
    )


# =========================
# MAIN
# =========================

async def main():
    print("Quantum Grow bot is starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
