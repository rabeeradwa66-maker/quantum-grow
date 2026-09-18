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


# =========================================================
# INVESTMENT PLANS
# =========================================================

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
                plan.name = name
                plan.amount = amount
                plan.duration_days = days
                plan.target_rate = rate
                plan.is_active = True

        db.commit()


seed_plans()


# =========================================================
# TRANSLATIONS
# =========================================================

TEXTS = {
    "ar": {
        "welcome": (
            "🚀 مرحبًا بك في Quantum Grow\n\n"
            "منصة لإدارة الحسابات والإيداعات "
            "والسحوبات والاستثمارات.\n\n"
            "⚠️ الاستثمارات تنطوي على مخاطر، "
            "والعائد المعروض هو عائد مستهدف وفق إعدادات الخطة "
            "وليس ضمانًا لنتيجة السوق.\n\n"
            "اختر من القائمة:"
        ),

        "plans": "💰 خطط الاستثمار",
        "deposit": "➕ الإيداع",
        "withdraw": "➖ السحب",
        "balance": "💼 رصيدي",
        "investments": "📊 استثماراتي",
        "status": "🤖 حالة النظام",
        "language": "🌐 اللغة",
        "info": "ℹ️ معلومات",
        "admin": "👨‍💼 لوحة المسؤول",

        "choose_language": (
            "🌐 اختيار اللغة\n\n"
            "اختر اللغة التي تريد استخدامها:"
        ),

        "arabic_selected": "🇸🇦 تم اختيار اللغة العربية.",
        "english_selected": "🇬🇧 English language selected.",

        "choose_plan": (
            "💰 خطط الاستثمار\n\n"
            "اختر الخطة التي تريد الاطلاع عليها:"
        ),

        "investment_duration": "⏱ المدة",
        "target_return": "📈 العائد المستهدف",
        "target_total": "🎯 الإجمالي المستهدف",
        "investment_amount": "💵 الاستثمار",

        "risk_plan": (
            "\n⚠️ العائد المستهدف ليس ضمانًا للربح. "
            "النتيجة الفعلية تعتمد على أداء النظام "
            "وظروف السوق وشروط الخدمة."
        ),

        "plan_details": "📋 تفاصيل الخطة",
        "plan": "🔹 الخطة",
        "amount": "💵 المبلغ",
        "target_profit": "💰 العائد المستهدف",
        "buy_plan": "🛒 شراء الخطة من الرصيد",
        "back_plans": "🔙 العودة للخطط",

        "locked_message": (
            "🔒 بعد شراء الخطة يصبح المبلغ المستثمر "
            "محجوزًا حتى نهاية الدورة."
        ),

        "plan_not_found": "❌ الخطة غير موجودة.",

        "insufficient": (
            "❌ لا يمكن شراء الخطة.\n\n"
            "💰 سعر الخطة: {amount:,.2f} USDT\n"
            "💼 رصيدك المتاح: {balance:,.2f} USDT\n"
            "📥 المبلغ المطلوب: {required:,.2f} USDT\n\n"
            "يمكنك إيداع المبلغ المطلوب ثم شراء الخطة."
        ),

        "purchase_success": (
            "✅ تم شراء الخطة بنجاح\n\n"
            "🆔 رقم الاستثمار: #{id}\n"
            "🔹 الخطة: {plan}\n"
            "💵 المبلغ المستثمر: {amount:,.2f} USDT\n"
            "⏱ المدة: {days} أيام\n"
            "📅 تاريخ البداية: {start} UTC\n"
            "📅 تاريخ الانتهاء: {end} UTC\n\n"
            "📈 العائد المستهدف: {profit:,.2f} USDT\n\n"
            "🔒 تم حجز مبلغ الاستثمار حتى انتهاء الدورة.\n"
            "💼 رصيدك المتاح الآن: {balance:,.2f} USDT\n\n"
            "⚠️ العائد المستهدف ليس ضمانًا لنتيجة السوق."
        ),

        "purchase_button": "تم شراء الخطة.",

        "deposit_choose": (
            "➕ الإيداع\n\n"
            "اختر طريقة الدفع:"
        ),

        "usdt": "🟢 USDT",
        "usdc": "🔵 USDC",
        "btc": "🟠 BTC",
        "eth": "🔷 ETH",
        "sham": "🇸🇾 شام كاش",

        "deposit_not_configured": (
            "⚠️ لم يتم إعداد {asset} بعد.\n"
            "تواصل مع الإدارة."
        ),

        "sham_deposit": (
            "🇸🇾 إيداع عبر شام كاش\n\n"
            "🆔 معرّف الاستلام:\n{address}\n\n"
            "بعد إرسال المبلغ، استخدم الأمر التالي "
            "لتسجيل العملية:\n\n"
            "/deposit SHAM_CASH SHAM_CASH المبلغ رقم_المرجع"
        ),

        "crypto_deposit": (
            "➕ إيداع {asset}\n\n"
            "🌐 الشبكة: {network}\n"
            "📍 العنوان:\n{address}\n\n"
            "بعد التحويل استخدم الأمر التالي:\n\n"
            "/deposit {asset} {network} المبلغ TX_HASH\n\n"
            "مثال:\n"
            "/deposit {asset} {network} 100 TX123456"
        ),

        "deposit_syntax": (
            "❌ الصيغة غير صحيحة.\n\n"
            "للعملات الرقمية:\n"
            "/deposit USDT TRC20 100 TX_HASH\n\n"
            "لشام كاش:\n"
            "/deposit SHAM_CASH SHAM_CASH 100 REFERENCE"
        ),

        "unsupported_payment": "❌ طريقة الدفع غير مدعومة.",
        "invalid_amount": "❌ المبلغ غير صحيح.",

        "deposit_created": (
            "✅ تم تسجيل طلب الإيداع #{id}.\n\n"
            "⏳ الطلب بانتظار مراجعة الإدارة."
        ),

        "admin_deposit": (
            "📥 طلب إيداع جديد\n\n"
            "🆔 الطلب: #{id}\n"
            "👤 المستخدم: @{username}\n"
            "Telegram ID: {user_id}\n"
            "💳 الطريقة: {asset}\n"
            "🌐 الشبكة: {network}\n"
            "💰 المبلغ: {amount:,.2f}\n"
            "🧾 المرجع / TX Hash:\n{reference}\n\n"
            "اختر الإجراء:"
        ),

        "approve_deposit": "✅ قبول الإيداع",
        "reject": "❌ رفض",

        "deposit_approved": (
            "✅ تم قبول الإيداع\n\n"
            "🆔 الطلب: #{id}\n"
            "💳 العملة: {asset}\n"
            "💰 المبلغ: {amount:,.2f}\n\n"
            "تم تحديث رصيد حسابك."
        ),

        "deposit_rejected": (
            "❌ تم رفض طلب الإيداع #{id}.\n\n"
            "يرجى التواصل مع الإدارة إذا كنت تعتقد أن هناك خطأ."
        ),

        "balance_title": (
            "💼 رصيد الحساب\n\n"
            "💵 الرصيد المتاح: {balance:,.2f} USDT\n"
            "🔒 المبلغ المستثمر والمحجوز: {locked:,.2f} USDT\n\n"
            "📊 الاستثمارات النشطة: {count}"
        ),

        "withdraw_help": (
            "➖ السحب\n\n"
            "لإنشاء طلب سحب أرسل:\n\n"
            "/withdraw USDT TRC20 100 YOUR_WALLET_ADDRESS\n\n"
            "⚠️ لا يمكن سحب الأموال المحجوزة داخل "
            "استثمار نشط."
        ),

        "withdraw_syntax": (
            "❌ الصيغة الصحيحة:\n"
            "/withdraw USDT TRC20 100 YOUR_WALLET_ADDRESS"
        ),

        "unsupported_withdraw": "❌ عملة السحب غير مدعومة.",

        "withdraw_insufficient": (
            "❌ الرصيد المتاح غير كافٍ.\n\n"
            "💼 المتاح: {available:,.2f} USDT\n"
            "💸 المطلوب: {amount:,.2f} USDT\n\n"
            "الأموال الموجودة داخل الاستثمارات "
            "النشطة غير قابلة للسحب."
        ),

        "withdraw_created": (
            "✅ تم إنشاء طلب السحب #{id}.\n\n"
            "⏳ الطلب بانتظار مراجعة الإدارة."
        ),

        "admin_withdraw": (
            "💸 طلب سحب جديد\n\n"
            "🆔 الطلب: #{id}\n"
            "👤 المستخدم: @{username}\n"
            "Telegram ID: {user_id}\n"
            "💳 العملة: {asset}\n"
            "🌐 الشبكة: {network}\n"
            "💰 المبلغ: {amount:,.2f}\n"
            "📍 محفظة المستلم:\n{wallet}\n\n"
            "اختر الإجراء:"
        ),

        "approve_withdraw": "✅ قبول السحب",

        "withdraw_approved": (
            "✅ تمت الموافقة على طلب السحب\n\n"
            "🆔 الطلب: #{id}\n"
            "💳 العملة: {asset}\n"
            "💰 المبلغ: {amount:,.2f}\n\n"
            "سيتم تنفيذ التحويل ومشاركة TX Hash "
            "بعد إتمام العملية."
        ),

        "withdraw_rejected": (
            "❌ تم رفض طلب السحب #{id}.\n\n"
            "لم يتم خصم أي مبلغ من رصيدك."
        ),

        "admin_panel": (
            "👨‍💼 لوحة المسؤول\n\n"
            "📥 /pending_deposits\n"
            "💸 /pending_withdrawals\n"
            "💰 /user_balance TELEGRAM_ID\n"
            "📊 /system"
        ),

        "no_pending_deposits": "📥 لا توجد طلبات إيداع معلقة.",
        "no_pending_withdrawals": "💸 لا توجد طلبات سحب معلقة.",

        "user_balance_syntax": (
            "الصيغة:\n/user_balance TELEGRAM_ID"
        ),

        "invalid_id": "❌ Telegram ID غير صحيح.",

        "admin_balance": (
            "💰 رصيد المستخدم\n\n"
            "Telegram ID: {id}\n"
            "💵 الرصيد المتاح: {balance:,.2f} USDT\n"
            "🔒 المبلغ المستثمر: {locked:,.2f} USDT\n"
            "📊 الاستثمارات النشطة: {count}"
        ),

        "system": (
            "📊 حالة النظام\n\n"
            "🟢 البوت يعمل\n"
            "👥 المستخدمون: {users}\n"
            "📥 إيداعات معلقة: {deposits}\n"
            "💸 سحوبات معلقة: {withdrawals}\n"
            "📊 استثمارات نشطة: {investments}"
        ),

        "no_investments": (
            "📊 استثماراتي\n\n"
            "لا توجد استثمارات مسجلة حاليًا."
        ),

        "my_investments": "📊 استثماراتي",

        "active_investment": (
            "🟢 #{id} — {plan}\n"
            "💰 المبلغ: {amount:,.2f} USDT\n"
            "🔒 الحالة: نشط ومحجوز\n"
            "⏳ المتبقي تقريبًا: {days} يوم و {hours} ساعة\n"
            "📅 الانتهاء: {end} UTC\n"
            "━━━━━━━━━━━━━━\n"
        ),

        "waiting_settlement": (
            "🟡 #{id} — {plan}\n"
            "⏳ بانتظار التسوية...\n"
            "━━━━━━━━━━━━━━\n"
        ),

        "completed_investment": (
            "✅ #{id} — {plan}\n"
            "💰 الأصل: {amount:,.2f} USDT\n"
            "📈 العائد المستهدف: {profit:,.2f} USDT\n"
            "💵 الإجمالي المسوى: {total:,.2f} USDT\n"
            "🔓 أصبحت الأموال متاحة.\n"
            "━━━━━━━━━━━━━━\n"
        ),

        "investment_footer": (
            "\n⚠️ العائد المذكور هو عائد مستهدف "
            "وليس ضمانًا للربح."
        ),

        "status_text": (
            "🤖 حالة النظام\n\n"
            "🟢 البوت يعمل ويستقبل الطلبات.\n"
            "🟢 تتم مراقبة الاستثمارات المنتهية "
            "وتسويتها تلقائيًا."
        ),

        "about": (
            "🚀 Quantum Grow\n\n"
            "إدارة الحسابات والإيداعات والسحوبات "
            "والاستثمارات.\n\n"
            "📅 مدة الدورة: 7 أيام\n"
            "📈 العائد المستهدف حسب إعدادات الخطة.\n\n"
            "⚠️ لا توجد أرباح مضمونة، والنتيجة الفعلية "
            "تعتمد على أداء النظام وظروف السوق "
            "وشروط الخدمة."
        ),

        "investment_completed": (
            "🎉 انتهت دورة الاستثمار\n\n"
            "🆔 الاستثمار: #{id}\n"
            "💰 أصل الاستثمار: {principal:,.2f} USDT\n"
            "📈 العائد المستهدف: {profit:,.2f} USDT\n"
            "💵 المبلغ المعاد للرصد: {total:,.2f} USDT\n\n"
            "✅ أصبح المبلغ متاحًا في رصيدك."
        ),

        "unauthorized": "⛔ غير مصرح لك.",
        "not_found": "❌ الطلب غير موجود.",
        "already_processed": "⚠️ تمت معالجة هذا الطلب مسبقًا.",
        "insufficient_admin": "❌ الرصيد غير كافٍ.",
    },

    "en": {
        "welcome": (
            "🚀 Welcome to Quantum Grow\n\n"
            "A platform for managing accounts, deposits, "
            "withdrawals and investments.\n\n"
            "⚠️ Investments involve risk. Any displayed return "
            "is a target based on the plan settings and is not "
            "a guarantee of market results.\n\n"
            "Choose from the menu:"
        ),

        "plans": "💰 Investment Plans",
        "deposit": "➕ Deposit",
        "withdraw": "➖ Withdraw",
        "balance": "💼 My Balance",
        "investments": "📊 My Investments",
        "status": "🤖 System Status",
        "language": "🌐 Language",
        "info": "ℹ️ Information",
        "admin": "👨‍💼 Admin Panel",

        "choose_language": (
            "🌐 Language Selection\n\n"
            "Choose your preferred language:"
        ),

        "arabic_selected": "🇸🇦 Arabic language selected.",
        "english_selected": "🇬🇧 English language selected.",

        "choose_plan": (
            "💰 Investment Plans\n\n"
            "Choose a plan to view its details:"
        ),

        "investment_duration": "⏱ Duration",
        "target_return": "📈 Target Return",
        "target_total": "🎯 Target Total",
        "investment_amount": "💵 Investment",

        "risk_plan": (
            "\n⚠️ The target return is not a guarantee of profit. "
            "Actual results depend on system performance, "
            "market conditions and the applicable terms."
        ),

        "plan_details": "📋 Plan Details",
        "plan": "🔹 Plan",
        "amount": "💵 Amount",
        "target_profit": "💰 Target Return",
        "buy_plan": "🛒 Buy Plan from Balance",
        "back_plans": "🔙 Back to Plans",

        "locked_message": (
            "🔒 After purchasing the plan, the invested amount "
            "is locked until the end of the cycle."
        ),

        "plan_not_found": "❌ Plan not found.",

        "insufficient": (
            "❌ The plan cannot be purchased.\n\n"
            "💰 Plan price: {amount:,.2f} USDT\n"
            "💼 Available balance: {balance:,.2f} USDT\n"
            "📥 Required amount: {required:,.2f} USDT\n\n"
            "Deposit the required amount and try again."
        ),

        "purchase_success": (
            "✅ Plan purchased successfully\n\n"
            "🆔 Investment ID: #{id}\n"
            "🔹 Plan: {plan}\n"
            "💵 Invested amount: {amount:,.2f} USDT\n"
            "⏱ Duration: {days} days\n"
            "📅 Start: {start} UTC\n"
            "📅 End: {end} UTC\n\n"
            "📈 Target return: {profit:,.2f} USDT\n\n"
            "🔒 The investment amount is locked until the cycle ends.\n"
            "💼 Available balance: {balance:,.2f} USDT\n\n"
            "⚠️ The target return is not a guarantee of market results."
        ),

        "purchase_button": "Plan purchased.",

        "deposit_choose": (
            "➕ Deposit\n\n"
            "Choose a payment method:"
        ),

        "usdt": "🟢 USDT",
        "usdc": "🔵 USDC",
        "btc": "🟠 BTC",
        "eth": "🔷 ETH",
        "sham": "🇸🇾 Sham Cash",

        "deposit_not_configured": (
            "⚠️ {asset} has not been configured yet.\n"
            "Please contact administration."
        ),

        "sham_deposit": (
            "🇸🇾 Sham Cash Deposit\n\n"
            "🆔 Receiving ID:\n{address}\n\n"
            "After sending the amount, use:\n\n"
            "/deposit SHAM_CASH SHAM_CASH AMOUNT REFERENCE"
        ),

        "crypto_deposit": (
            "➕ {asset} Deposit\n\n"
            "🌐 Network: {network}\n"
            "📍 Address:\n{address}\n\n"
            "After the transfer, use:\n\n"
            "/deposit {asset} {network} AMOUNT TX_HASH\n\n"
            "Example:\n"
            "/deposit {asset} {network} 100 TX123456"
        ),

        "deposit_syntax": (
            "❌ Invalid format.\n\n"
            "For crypto:\n"
            "/deposit USDT TRC20 100 TX_HASH\n\n"
            "For Sham Cash:\n"
            "/deposit SHAM_CASH SHAM_CASH 100 REFERENCE"
        ),

        "unsupported_payment": "❌ Payment method is not supported.",
        "invalid_amount": "❌ Invalid amount.",

        "deposit_created": (
            "✅ Deposit request #{id} has been created.\n\n"
            "⏳ The request is waiting for administrative review."
        ),

        "admin_deposit": (
            "📥 New Deposit Request\n\n"
            "🆔 Request: #{id}\n"
            "👤 User: @{username}\n"
            "Telegram ID: {user_id}\n"
            "💳 Asset: {asset}\n"
            "🌐 Network: {network}\n"
            "💰 Amount: {amount:,.2f}\n"
            "🧾 Reference / TX Hash:\n{reference}\n\n"
            "Choose an action:"
        ),

        "approve_deposit": "✅ Approve Deposit",
        "reject": "❌ Reject",

        "deposit_approved": (
            "✅ Deposit approved\n\n"
            "🆔 Request: #{id}\n"
            "💳 Asset: {asset}\n"
            "💰 Amount: {amount:,.2f}\n\n"
            "Your account balance has been updated."
        ),

        "deposit_rejected": (
            "❌ Deposit request #{id} was rejected.\n\n"
            "Contact administration if you believe this was an error."
        ),

        "balance_title": (
            "💼 Account Balance\n\n"
            "💵 Available balance: {balance:,.2f} USDT\n"
            "🔒 Locked investment amount: {locked:,.2f} USDT\n\n"
            "📊 Active investments: {count}"
        ),

        "withdraw_help": (
            "➖ Withdraw\n\n"
            "To create a withdrawal request send:\n\n"
            "/withdraw USDT TRC20 100 YOUR_WALLET_ADDRESS\n\n"
            "⚠️ Funds locked in an active investment cannot be withdrawn."
        ),

        "withdraw_syntax": (
            "❌ Correct format:\n"
            "/withdraw USDT TRC20 100 YOUR_WALLET_ADDRESS"
        ),

        "unsupported_withdraw": "❌ Withdrawal asset is not supported.",

        "withdraw_insufficient": (
            "❌ Available balance is insufficient.\n\n"
            "💼 Available: {available:,.2f} USDT\n"
            "💸 Required: {amount:,.2f} USDT\n\n"
            "Funds locked in active investments cannot be withdrawn."
        ),

        "withdraw_created": (
            "✅ Withdrawal request #{id} has been created.\n\n"
            "⏳ The request is waiting for administrative review."
        ),

        "admin_withdraw": (
            "💸 New Withdrawal Request\n\n"
            "🆔 Request: #{id}\n"
            "👤 User: @{username}\n"
            "Telegram ID: {user_id}\n"
            "💳 Asset: {asset}\n"
            "🌐 Network: {network}\n"
            "💰 Amount: {amount:,.2f}\n"
            "📍 Destination wallet:\n{wallet}\n\n"
            "Choose an action:"
        ),

        "approve_withdraw": "✅ Approve Withdrawal",

        "withdraw_approved": (
            "✅ Withdrawal request approved\n\n"
            "🆔 Request: #{id}\n"
            "💳 Asset: {asset}\n"
            "💰 Amount: {amount:,.2f}\n\n"
            "The transfer will be processed and the TX Hash "
            "shared after completion."
        ),

        "withdraw_rejected": (
            "❌ Withdrawal request #{id} was rejected.\n\n"
            "No amount was deducted from your balance."
        ),

        "admin_panel": (
            "👨‍💼 Admin Panel\n\n"
            "📥 /pending_deposits\n"
            "💸 /pending_withdrawals\n"
            "💰 /user_balance TELEGRAM_ID\n"
            "📊 /system"
        ),

        "no_pending_deposits": "📥 No pending deposit requests.",
        "no_pending_withdrawals": "💸 No pending withdrawal requests.",

        "user_balance_syntax": (
            "Format:\n/user_balance TELEGRAM_ID"
        ),

        "invalid_id": "❌ Invalid Telegram ID.",

        "admin_balance": (
            "💰 User Balance\n\n"
            "Telegram ID: {id}\n"
            "💵 Available balance: {balance:,.2f} USDT\n"
            "🔒 Invested amount: {locked:,.2f} USDT\n"
            "📊 Active investments: {count}"
        ),

        "system": (
            "📊 System Status\n\n"
            "🟢 Bot is running\n"
            "👥 Users: {users}\n"
            "📥 Pending deposits: {deposits}\n"
            "💸 Pending withdrawals: {withdrawals}\n"
            "📊 Active investments: {investments}"
        ),

        "no_investments": (
            "📊 My Investments\n\n"
            "There are currently no registered investments."
        ),

        "my_investments": "📊 My Investments",

        "active_investment": (
            "🟢 #{id} — {plan}\n"
            "💰 Amount: {amount:,.2f} USDT\n"
            "🔒 Status: Active and locked\n"
            "⏳ Approximately remaining: {days} days and {hours} hours\n"
            "📅 End: {end} UTC\n"
            "━━━━━━━━━━━━━━\n"
        ),

        "waiting_settlement": (
            "🟡 #{id} — {plan}\n"
            "⏳ Waiting for settlement...\n"
            "━━━━━━━━━━━━━━\n"
        ),

        "completed_investment": (
            "✅ #{id} — {plan}\n"
            "💰 Principal: {amount:,.2f} USDT\n"
            "📈 Target return: {profit:,.2f} USDT\n"
            "💵 Settled total: {total:,.2f} USDT\n"
            "🔓 Funds are now available.\n"
            "━━━━━━━━━━━━━━\n"
        ),

        "investment_footer": (
            "\n⚠️ The displayed return is a target and "
            "not a guarantee of profit."
        ),

        "status_text": (
            "🤖 System Status\n\n"
            "🟢 The bot is running and accepting requests.\n"
            "🟢 Finished investments are monitored and settled automatically."
        ),

        "about": (
            "🚀 Quantum Grow\n\n"
            "Account, deposit, withdrawal and investment management.\n\n"
            "📅 Cycle duration: 7 days\n"
            "📈 Target return according to plan settings.\n\n"
            "⚠️ No profits are guaranteed. Actual results depend "
            "on system performance, market conditions and the applicable terms."
        ),

        "investment_completed": (
            "🎉 Investment cycle completed\n\n"
            "🆔 Investment: #{id}\n"
            "💰 Principal: {principal:,.2f} USDT\n"
            "📈 Target return: {profit:,.2f} USDT\n"
            "💵 Amount returned to balance: {total:,.2f} USDT\n\n"
            "✅ The amount is now available in your balance."
        ),

        "unauthorized": "⛔ You are not authorized.",
        "not_found": "❌ Request not found.",
        "already_processed": "⚠️ This request has already been processed.",
        "insufficient_admin": "❌ Insufficient balance.",
    },
}


def tr(lang: str, key: str, **kwargs):
    lang = lang if lang in TEXTS else "ar"
    text = TEXTS[lang].get(key, TEXTS["ar"].get(key, key))

    try:
        return text.format(**kwargs)
    except (KeyError, ValueError):
        return text


# =========================================================
# USER / LANGUAGE
# =========================================================

async def ensure_user(message: Message):
    uid = message.from_user.id
    username = message.from_user.username

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.telegram_id == uid)
        )

        if not user:
            user = User(
                telegram_id=uid,
                username=username,
                language="ar",
            )
            db.add(user)
        else:
            user.username = username

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


def get_language(user_id: int) -> str:
    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.telegram_id == user_id
            )
        )

        if user and user.language in ("ar", "en"):
            return user.language

    return "ar"


def set_language(user_id: int, language: str):
    if language not in ("ar", "en"):
        return

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.telegram_id == user_id
            )
        )

        if user:
            user.language = language
            db.commit()


def language_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🇸🇦 العربية",
                    callback_data="lang:ar",
                ),
                InlineKeyboardButton(
                    text="🇬🇧 English",
                    callback_data="lang:en",
                ),
            ]
        ]
    )


# =========================================================
# MAIN KEYBOARD
# =========================================================

def keyboard(lang: str = "ar"):
    buttons = [
        [
            KeyboardButton(text=tr(lang, "plans")),
            KeyboardButton(text=tr(lang, "deposit")),
        ],
        [
            KeyboardButton(text=tr(lang, "withdraw")),
            KeyboardButton(text=tr(lang, "balance")),
        ],
        [
            KeyboardButton(text=tr(lang, "investments")),
            KeyboardButton(text=tr(lang, "status")),
        ],
        [
            KeyboardButton(text=tr(lang, "language")),
            KeyboardButton(text=tr(lang, "info")),
        ],
    ]

    if settings.admin_telegram_id:
        buttons.append(
            [KeyboardButton(text=tr(lang, "admin"))]
        )

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
    )


# =========================================================
# PAYMENTS
# =========================================================

def payment_keyboard(prefix: str, lang: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=tr(lang, "usdt"),
                    callback_data=f"{prefix}:USDT",
                )
            ],
            [
                InlineKeyboardButton(
                    text=tr(lang, "usdc"),
                    callback_data=f"{prefix}:USDC",
                )
            ],
            [
                InlineKeyboardButton(
                    text=tr(lang, "btc"),
                    callback_data=f"{prefix}:BTC",
                )
            ],
            [
                InlineKeyboardButton(
                    text=tr(lang, "eth"),
                    callback_data=f"{prefix}:ETH",
                )
            ],
            [
                InlineKeyboardButton(
                    text=tr(lang, "sham"),
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


# =========================================================
# ADMIN
# =========================================================

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
                    DemoBalance.telegram_id
                    == investment.telegram_id
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

        lang = get_language(user_id)

        try:
            await bot.send_message(
                chat_id=user_id,
                text=tr(
                    lang,
                    "investment_completed",
                    id=investment_id,
                    principal=principal,
                    profit=profit,
                    total=total,
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

    lang = get_language(
        message.from_user.id
    )

    await message.answer(
        tr(lang, "welcome"),
        reply_markup=keyboard(lang),
    )


# =========================================================
# LANGUAGE
# =========================================================

@dp.message(
    F.text.in_(
        [
            "🌐 اللغة",
            "🌐 Language",
        ]
    )
)
async def language(message: Message):
    lang = get_language(
        message.from_user.id
    )

    await message.answer(
        tr(lang, "choose_language"),
        reply_markup=language_keyboard(),
    )


@dp.callback_query(F.data.startswith("lang:"))
async def language_callback(callback):
    language_code = callback.data.split(":", 1)[1]

    if language_code not in ("ar", "en"):
        await callback.answer()
        return

    await ensure_user(callback.message)

    set_language(
        callback.from_user.id,
        language_code,
    )

    await callback.message.answer(
        tr(
            language_code,
            "arabic_selected"
            if language_code == "ar"
            else "english_selected",
        ),
        reply_markup=keyboard(language_code),
    )

    await callback.answer()


# =========================================================
# INVESTMENT PLANS
# =========================================================

def plan_keyboard(plans, lang: str):
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


@dp.message(
    F.text.in_(
        [
            "💰 خطط الاستثمار",
            "💰 Investment Plans",
        ]
    )
)
async def plans(message: Message):
    await ensure_user(message)

    lang = get_language(
        message.from_user.id
    )

    with SessionLocal() as db:
        rows = db.scalars(
            select(InvestmentPlan)
            .where(
                InvestmentPlan.is_active == True
            )
            .order_by(InvestmentPlan.amount)
        ).all()

    text = tr(lang, "choose_plan") + "\n\n"

    for p in rows:
        target_profit = (
            p.amount * p.target_rate
        )

        total_target = (
            p.amount + target_profit
        )

        text += (
            f"🔹 {p.name}\n"
            f"{tr(lang, 'investment_amount')}: "
            f"{p.amount:,.2f} USDT\n"
            f"{tr(lang, 'investment_duration')}: "
            f"{p.duration_days} days\n"
            f"{tr(lang, 'target_return')}: "
            f"{p.target_rate * 100:.0f}%\n"
            f"{tr(lang, 'target_total')}: "
            f"{total_target:,.2f} USDT\n"
            "━━━━━━━━━━━━━━\n"
        )

    text += tr(lang, "risk_plan")

    await message.answer(
        text,
        reply_markup=plan_keyboard(
            rows,
            lang,
        ),
    )


# =========================================================
# PLAN DETAILS
# =========================================================

@dp.callback_query(F.data.startswith("plan:"))
async def plan_details_callback(callback):
    plan_id = int(
        callback.data.split(":")[1]
    )

    lang = get_language(
        callback.from_user.id
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
            tr(lang, "plan_not_found"),
            show_alert=True,
        )
        return

    target_profit = (
        plan.amount * plan.target_rate
    )

    total_target = (
        plan.amount + target_profit
    )

    buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=tr(lang, "buy_plan"),
                    callback_data=f"buyplan:{plan.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=tr(lang, "back_plans"),
                    callback_data="backplans",
                )
            ],
        ]
    )

    text = (
        f"{tr(lang, 'plan_details')}\n\n"
        f"{tr(lang, 'plan')}: {plan.name}\n"
        f"{tr(lang, 'amount')}: "
        f"{plan.amount:,.2f} USDT\n"
        f"{tr(lang, 'investment_duration')}: "
        f"{plan.duration_days} days\n"
        f"{tr(lang, 'target_return')}: "
        f"{plan.target_rate * 100:.0f}%\n"
        f"{tr(lang, 'target_profit')}: "
        f"{target_profit:,.2f} USDT\n"
        f"{tr(lang, 'target_total')}: "
        f"{total_target:,.2f} USDT\n\n"
        f"{tr(lang, 'locked_message')}\n\n"
        f"{tr(lang, 'risk_plan').strip()}"
    )

    await callback.message.answer(
        text,
        reply_markup=buttons,
    )

    await callback.answer()


@dp.callback_query(F.data == "backplans")
async def back_to_plans(callback):
    lang = get_language(
        callback.from_user.id
    )

    with SessionLocal() as db:
        rows = db.scalars(
            select(InvestmentPlan)
            .where(
                InvestmentPlan.is_active == True
            )
            .order_by(InvestmentPlan.amount)
        ).all()

    await callback.message.answer(
        tr(lang, "choose_plan"),
        reply_markup=plan_keyboard(
            rows,
            lang,
        ),
    )

    await callback.answer()


# =========================================================
# BUY PLAN
# =========================================================

@dp.callback_query(F.data.startswith("buyplan:"))
async def buy_plan(callback):
    plan_id = int(
        callback.data.split(":")[1]
    )

    user_id = callback.from_user.id
    lang = get_language(user_id)

    with SessionLocal() as db:
        plan = db.scalar(
            select(InvestmentPlan).where(
                InvestmentPlan.id == plan_id,
                InvestmentPlan.is_active == True,
            )
        )

        if not plan:
            await callback.answer(
                tr(lang, "plan_not_found"),
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
            required = (
                plan.amount - current
            )

            await callback.message.answer(
                tr(
                    lang,
                    "insufficient",
                    amount=plan.amount,
                    balance=current,
                    required=required,
                )
            )

            await callback.answer(
                "Insufficient balance."
                if lang == "en"
                else "الرصيد غير كافٍ.",
                show_alert=True,
            )
            return

        now = datetime.utcnow()

        ends_at = (
            now
            + timedelta(
                days=plan.duration_days
            )
        )

        target_profit = (
            plan.amount
            * plan.target_rate
        )

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
        tr(
            lang,
            "purchase_success",
            id=investment_id,
            plan=plan.name,
            amount=plan.amount,
            days=plan.duration_days,
            start=now.strftime(
                "%Y-%m-%d %H:%M"
            ),
            end=ends_at.strftime(
                "%Y-%m-%d %H:%M"
            ),
            profit=target_profit,
            balance=remaining_balance,
        )
    )

    await callback.answer(
        tr(lang, "purchase_button")
    )


# =========================================================
# DEPOSIT
# =========================================================

@dp.message(
    F.text.in_(
        [
            "➕ الإيداع",
            "➕ Deposit",
        ]
    )
)
async def deposit(message: Message):
    await ensure_user(message)

    lang = get_language(
        message.from_user.id
    )

    await message.answer(
        tr(lang, "deposit_choose"),
        reply_markup=payment_keyboard(
            "dep",
            lang,
        ),
    )


@dp.callback_query(F.data.startswith("dep:"))
async def deposit_currency(callback):
    asset = callback.data.split(
        ":",
        1,
    )[1]

    lang = get_language(
        callback.from_user.id
    )

    network, address = payment_details(
        asset
    )

    if not address:
        await callback.message.answer(
            tr(
                lang,
                "deposit_not_configured",
                asset=asset,
            )
        )

    elif asset == "SHAM_CASH":
        await callback.message.answer(
            tr(
                lang,
                "sham_deposit",
                address=address,
            )
        )

    else:
        await callback.message.answer(
            tr(
                lang,
                "crypto_deposit",
                asset=asset,
                network=network,
                address=address,
            )
        )

    await callback.answer()


@dp.message(Command("deposit"))
async def deposit_command(message: Message):
    lang = get_language(
        message.from_user.id
    )

    parts = message.text.split(
        maxsplit=4
    )

    if len(parts) != 5:
        await message.answer(
            tr(lang, "deposit_syntax")
        )
        return

    _, asset, network, amount_s, reference = parts

    asset = asset.upper()
    network = network.upper()

    allowed_assets = [
        "USDT",
        "USDC",
        "BTC",
        "ETH",
        "SHAM_CASH",
    ]

    if asset not in allowed_assets:
        await message.answer(
            tr(lang, "unsupported_payment")
        )
        return

    try:
        amount = float(amount_s)

        if amount <= 0:
            raise ValueError

    except ValueError:
        await message.answer(
            tr(lang, "invalid_amount")
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
                    text=tr(
                        "ar",
                        "approve_deposit",
                    ),
                    callback_data=(
                        f"depapprove:{request_id}"
                    ),
                ),
                InlineKeyboardButton(
                    text=tr(
                        "ar",
                        "reject",
                    ),
                    callback_data=(
                        f"depreject:{request_id}"
                    ),
                ),
            ]
        ]
    )

    username = (
        message.from_user.username
        or "no_username"
    )

    admin_text = tr(
        "ar",
        "admin_deposit",
        id=request_id,
        username=username,
        user_id=message.from_user.id,
        asset=asset,
        network=network,
        amount=amount,
        reference=reference,
    )

    await send_admin_message(
        admin_text,
        reply_markup=admin_keyboard,
    )

    await message.answer(
        tr(
            lang,
            "deposit_created",
            id=request_id,
        )
    )


# =========================================================
# ADMIN DEPOSIT
# =========================================================

@dp.callback_query(
    F.data.startswith("depapprove:")
)
async def approve_deposit(callback):
    if not is_admin(
        callback.from_user.id
    ):
        await callback.answer(
            tr("ar", "unauthorized"),
            show_alert=True,
        )
        return

    request_id = int(
        callback.data.split(":")[1]
    )

    with SessionLocal() as db:
        req = db.scalar(
            select(DepositRequest).where(
                DepositRequest.id
                == request_id
            )
        )

        if not req:
            await callback.answer(
                tr("ar", "not_found"),
                show_alert=True,
            )
            return

        if req.status != "pending":
            await callback.answer(
                tr("ar", "already_processed"),
                show_alert=True,
            )
            return

        bal = db.scalar(
            select(DemoBalance).where(
                DemoBalance.telegram_id
                == req.telegram_id
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

    user_lang = get_language(user_id)

    await bot.send_message(
        chat_id=user_id,
        text=tr(
            user_lang,
            "deposit_approved",
            id=request_id,
            asset=asset,
            amount=amount,
        ),
    )

    await callback.message.edit_text(
        callback.message.text
        + "\n\n✅ تم قبول الطلب وتحديث الرصيد."
    )

    await callback.answer(
        "Deposit approved."
    )


@dp.callback_query(
    F.data.startswith("depreject:")
)
async def reject_deposit(callback):
    if not is_admin(
        callback.from_user.id
    ):
        await callback.answer(
            tr("ar", "unauthorized"),
            show_alert=True,
        )
        return

    request_id = int(
        callback.data.split(":")[1]
    )

    with SessionLocal() as db:
        req = db.scalar(
            select(DepositRequest).where(
                DepositRequest.id
                == request_id
            )
        )

        if not req:
            await callback.answer(
                tr("ar", "not_found"),
                show_alert=True,
            )
            return

        if req.status != "pending":
            await callback.answer(
                tr("ar", "already_processed"),
                show_alert=True,
            )
            return

        req.status = "rejected"
        db.commit()

        user_id = req.telegram_id

    user_lang = get_language(user_id)

    await bot.send_message(
        chat_id=user_id,
        text=tr(
            user_lang,
            "deposit_rejected",
            id=request_id,
        ),
    )

    await callback.message.edit_text(
        callback.message.text
        + "\n\n❌ تم رفض الطلب."
    )

    await callback.answer(
        "Deposit rejected."
    )


# =========================================================
# BALANCE
# =========================================================

@dp.message(
    F.text.in_(
        [
            "💼 رصيدي",
            "💼 My Balance",
        ]
    )
)
async def balance(message: Message):
    await ensure_user(message)

    lang = get_language(
        message.from_user.id
    )

    with SessionLocal() as db:
        bal = db.scalar(
            select(DemoBalance).where(
                DemoBalance.telegram_id
                == message.from_user.id
            )
        )

        active_investments = db.scalars(
            select(Investment).where(
                Investment.telegram_id
                == message.from_user.id,
                Investment.status
                == "active",
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
        tr(
            lang,
            "balance_title",
            balance=current_balance,
            locked=locked,
            count=len(active_investments),
        )
    )


# =========================================================
# WITHDRAWAL
# =========================================================

@dp.message(
    F.text.in_(
        [
            "➖ السحب",
            "➖ Withdraw",
        ]
    )
)
async def withdrawal(message: Message):
    await ensure_user(message)

    lang = get_language(
        message.from_user.id
    )

    await message.answer(
        tr(lang, "withdraw_help")
    )


@dp.message(Command("withdraw"))
async def withdraw_command(message: Message):
    lang = get_language(
        message.from_user.id
    )

    parts = message.text.split(
        maxsplit=4
    )

    if len(parts) != 5:
        await message.answer(
            tr(lang, "withdraw_syntax")
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
            tr(
                lang,
                "unsupported_withdraw",
            )
        )
        return

    try:
        amount = float(amount_s)

        if amount <= 0:
            raise ValueError

    except ValueError:
        await message.answer(
            tr(lang, "invalid_amount")
        )
        return

    await ensure_user(message)

    with SessionLocal() as db:
        bal = db.scalar(
            select(DemoBalance).where(
                DemoBalance.telegram_id
                == message.from_user.id
            )
        )

        if not bal or bal.balance < amount:
            available = (
                bal.balance if bal else 0.0
            )

            await message.answer(
                tr(
                    lang,
                    "withdraw_insufficient",
                    available=available,
                    amount=amount,
                )
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
                    text=tr(
                        "ar",
                        "approve_withdraw",
                    ),
                    callback_data=(
                        f"withapprove:{request_id}"
                    ),
                ),
                InlineKeyboardButton(
                    text=tr(
                        "ar",
                        "reject",
                    ),
                    callback_data=(
                        f"withreject:{request_id}"
                    ),
                ),
            ]
        ]
    )

    username = (
        message.from_user.username
        or "no_username"
    )

    admin_text = tr(
        "ar",
        "admin_withdraw",
        id=request_id,
        username=username,
        user_id=message.from_user.id,
        asset=asset,
        network=network,
        amount=amount,
        wallet=wallet,
    )

    await send_admin_message(
        admin_text,
        reply_markup=admin_keyboard,
    )

    await message.answer(
        tr(
            lang,
            "withdraw_created",
            id=request_id,
        )
    )


# =========================================================
# ADMIN WITHDRAWAL
# =========================================================

@dp.callback_query(
    F.data.startswith("withapprove:")
)
async def approve_withdrawal(callback):
    if not is_admin(
        callback.from_user.id
    ):
        await callback.answer(
            tr("ar", "unauthorized"),
            show_alert=True,
        )
        return

    request_id = int(
        callback.data.split(":")[1]
    )

    with SessionLocal() as db:
        req = db.scalar(
            select(WithdrawalRequest).where(
                WithdrawalRequest.id
                == request_id
            )
        )

        if not req:
            await callback.answer(
                tr("ar", "not_found"),
                show_alert=True,
            )
            return

        if req.status != "pending":
            await callback.answer(
                tr("ar", "already_processed"),
                show_alert=True,
            )
            return

        bal = db.scalar(
            select(DemoBalance).where(
                DemoBalance.telegram_id
                == req.telegram_id
            )
        )

        if not bal or bal.balance < req.amount:
            await callback.answer(
                tr("ar", "insufficient_admin"),
                show_alert=True,
            )
            return

        bal.balance -= req.amount
        req.status = "approved"

        db.commit()

        user_id = req.telegram_id
        amount = req.amount
        asset = req.asset

    user_lang = get_language(user_id)

    await bot.send_message(
        chat_id=user_id,
        text=tr(
            user_lang,
            "withdraw_approved",
            id=request_id,
            asset=asset,
            amount=amount,
        ),
    )

    await callback.message.edit_text(
        callback.message.text
        + "\n\n✅ تمت الموافقة وخصم المبلغ من الرصيد."
    )

    await callback.answer(
        "Withdrawal approved."
    )


@dp.callback_query(
    F.data.startswith("withreject:")
)
async def reject_withdrawal(callback):
    if not is_admin(
        callback.from_user.id
    ):
        await callback.answer(
            tr("ar", "unauthorized"),
            show_alert=True,
        )
        return

    request_id = int(
        callback.data.split(":")[1]
    )

    with SessionLocal() as db:
        req = db.scalar(
            select(WithdrawalRequest).where(
                WithdrawalRequest.id
                == request_id
            )
        )

        if not req:
            await callback.answer(
                tr("ar", "not_found"),
                show_alert=True,
            )
            return

        if req.status != "pending":
            await callback.answer(
                tr("ar", "already_processed"),
                show_alert=True,
            )
            return

        req.status = "rejected"
        db.commit()

        user_id = req.telegram_id

    user_lang = get_language(user_id)

    await bot.send_message(
        chat_id=user_id,
        text=tr(
            user_lang,
            "withdraw_rejected",
            id=request_id,
        ),
    )

    await callback.message.edit_text(
        callback.message.text
        + "\n\n❌ تم رفض طلب السحب."
    )

    await callback.answer(
        "Withdrawal rejected."
    )


# =========================================================
# ADMIN PANEL
# =========================================================

@dp.message(Command("admin"))
async def admin_command(message: Message):
    if not is_admin(
        message.from_user.id
    ):
        await message.answer(
            tr(
                get_language(
                    message.from_user.id
                ),
                "unauthorized",
            )
        )
        return

    await message.answer(
        tr("ar", "admin_panel")
    )


@dp.message(
    F.text.in_(
        [
            "👨‍💼 لوحة المسؤول",
            "👨‍💼 Admin Panel",
        ]
    )
)
async def admin_button(message: Message):
    if not is_admin(
        message.from_user.id
    ):
        await message.answer(
            tr(
                get_language(
                    message.from_user.id
                ),
                "unauthorized",
            )
        )
        return

    await message.answer(
        tr("ar", "admin_panel")
    )


@dp.message(Command("pending_deposits"))
async def pending_deposits(message: Message):
    if not is_admin(
        message.from_user.id
    ):
        await message.answer(
            tr("ar", "unauthorized")
        )
        return

    with SessionLocal() as db:
        rows = db.scalars(
            select(DepositRequest)
            .where(
                DepositRequest.status
                == "pending"
            )
            .order_by(
                DepositRequest.id.desc()
            )
        ).all()

    if not rows:
        await message.answer(
            tr(
                get_language(
                    message.from_user.id
                ),
                "no_pending_deposits",
            )
        )
        return

    text = (
        "📥 طلبات الإيداع المعلقة\n\n"
    )

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
    if not is_admin(
        message.from_user.id
    ):
        await message.answer(
            tr("ar", "unauthorized")
        )
        return

    with SessionLocal() as db:
        rows = db.scalars(
            select(WithdrawalRequest)
            .where(
                WithdrawalRequest.status
                == "pending"
            )
            .order_by(
                WithdrawalRequest.id.desc()
            )
        ).all()

    if not rows:
        await message.answer(
            tr(
                get_language(
                    message.from_user.id
                ),
                "no_pending_withdrawals",
            )
        )
        return

    text = (
        "💸 طلبات السحب المعلقة\n\n"
    )

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
    if not is_admin(
        message.from_user.id
    ):
        await message.answer(
            tr("ar", "unauthorized")
        )
        return

    parts = message.text.split()

    if len(parts) != 2:
        await message.answer(
            tr(
                "ar",
                "user_balance_syntax",
            )
        )
        return

    try:
        telegram_id = int(parts[1])
    except ValueError:
        await message.answer(
            tr("ar", "invalid_id")
        )
        return

    with SessionLocal() as db:
        bal = db.scalar(
            select(DemoBalance).where(
                DemoBalance.telegram_id
                == telegram_id
            )
        )

        investments = db.scalars(
            select(Investment).where(
                Investment.telegram_id
                == telegram_id,
                Investment.status
                == "active",
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
        tr(
            "ar",
            "admin_balance",
            id=telegram_id,
            balance=amount,
            locked=locked,
            count=len(investments),
        )
    )


@dp.message(Command("system"))
async def admin_system(message: Message):
    if not is_admin(
        message.from_user.id
    ):
        await message.answer(
            tr("ar", "unauthorized")
        )
        return

    with SessionLocal() as db:
        deposits = db.scalars(
            select(DepositRequest).where(
                DepositRequest.status
                == "pending"
            )
        ).all()

        withdrawals = db.scalars(
            select(WithdrawalRequest).where(
                WithdrawalRequest.status
                == "pending"
            )
        ).all()

        users = db.scalars(
            select(User)
        ).all()

        active_investments = db.scalars(
            select(Investment).where(
                Investment.status
                == "active"
            )
        ).all()

    await message.answer(
        tr(
            "ar",
            "system",
            users=len(users),
            deposits=len(deposits),
            withdrawals=len(withdrawals),
            investments=len(active_investments),
        )
    )


# =========================================================
# USER INVESTMENTS
# =========================================================

@dp.message(
    F.text.in_(
        [
            "📊 استثماراتي",
            "📊 My Investments",
        ]
    )
)
async def investments(message: Message):
    await ensure_user(message)

    lang = get_language(
        message.from_user.id
    )

    await settle_finished_investments()

    with SessionLocal() as db:
        rows = db.scalars(
            select(Investment)
            .where(
                Investment.telegram_id
                == message.from_user.id
            )
            .order_by(
                Investment.id.desc()
            )
        ).all()

        plans_map = {
            p.id: p
            for p in db.scalars(
                select(InvestmentPlan)
            ).all()
        }

    if not rows:
        await message.answer(
            tr(lang, "no_investments")
        )
        return

    text = (
        tr(lang, "my_investments")
        + "\n\n"
    )

    now = datetime.utcnow()

    for inv in rows:
        plan = plans_map.get(
            inv.plan_id
        )

        plan_name = (
            plan.name
            if plan
            else f"Plan #{inv.plan_id}"
        )

        if inv.status == "active":
            remaining = (
                inv.ends_at - now
            )

            if remaining.total_seconds() > 0:
                days = remaining.days
                hours = (
                    remaining.seconds
                    // 3600
                )

                text += tr(
                    lang,
                    "active_investment",
                    id=inv.id,
                    plan=plan_name,
                    amount=inv.amount,
                    days=days,
                    hours=hours,
                    end=inv.ends_at.strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                )

            else:
                text += tr(
                    lang,
                    "waiting_settlement",
                    id=inv.id,
                    plan=plan_name,
                )

        elif inv.status == "completed":
            total = (
                inv.amount
                + inv.target_profit
            )

            text += tr(
                lang,
                "completed_investment",
                id=inv.id,
                plan=plan_name,
                amount=inv.amount,
                profit=inv.target_profit,
                total=total,
            )

    text += tr(
        lang,
        "investment_footer",
    )

    await message.answer(text)


# =========================================================
# STATUS / INFO
# =========================================================

@dp.message(
    F.text.in_(
        [
            "🤖 حالة النظام",
            "🤖 System Status",
        ]
    )
)
async def status(message: Message):
    lang = get_language(
        message.from_user.id
    )

    await message.answer(
        tr(lang, "status_text")
    )


@dp.message(
    F.text.in_(
        [
            "ℹ️ معلومات",
            "ℹ️ Information",
        ]
    )
)
async def about(message: Message):
    lang = get_language(
        message.from_user.id
    )

    await message.answer(
        tr(lang, "about")
    )


# =========================================================
# MAIN
# =========================================================

async def main():
    print(
        "Quantum Grow bot is starting..."
    )

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
