import asyncio
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, Message, CallbackQuery
from sqlalchemy import select

from .config import settings
from .db import Base, SessionLocal, engine
from .models import DemoBalance, DepositRequest, Investment, InvestmentPlan, User, WithdrawalRequest

Base.metadata.create_all(bind=engine)
bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher(storage=MemoryStorage())

PLANS = [
    (1, "Starter", 10, 7, .18), (2, "Basic", 25, 7, .18),
    (3, "Bronze", 50, 7, .18), (4, "Silver", 100, 7, .18),
    (5, "Gold", 250, 7, .18), (6, "Platinum", 500, 7, .18),
    (7, "Pro", 1000, 7, .18), (8, "Advanced", 2500, 7, .18),
    (9, "Premium", 5000, 7, .18), (10, "Elite", 10000, 7, .18),
    (11, "VIP", 15000, 7, .18), (12, "Quantum", 20000, 7, .18),
]

def seed_plans():
    with SessionLocal() as db:
        for pid, name, amount, days, rate in PLANS:
            p = db.scalar(select(InvestmentPlan).where(InvestmentPlan.id == pid))
            if not p:
                db.add(InvestmentPlan(id=pid, name=name, amount=amount,
                    duration_days=days, target_rate=rate, is_active=True))
            else:
                p.name, p.amount, p.duration_days, p.target_rate, p.is_active = name, amount, days, rate, True
        db.commit()
seed_plans()

# ---------------------------------------------------------------------
# TEXT
# ---------------------------------------------------------------------
T = {
"ar": {
"welcome": "🚀 مرحبًا بك في Quantum Grow\n\nمنصة رقمية لإدارة الحسابات والإيداعات والسحوبات والاستثمارات.\n\nاختر من القائمة:",
"plans":"💰 خطط الاستثمار","deposit":"➕ الإيداع","withdraw":"➖ السحب","balance":"💼 رصيدي","investments":"📊 استثماراتي","status":"🤖 حالة النظام","language":"🌐 اللغة","info":"ℹ️ معلومات","admin":"👨‍💼 لوحة المسؤول",
"choose_language":"🌐 اختيار اللغة\n\nاختر اللغة التي تريد استخدامها:","arabic_selected":"🇸🇦 تم اختيار اللغة العربية.","english_selected":"🇬🇧 تم اختيار اللغة الإنجليزية.",
"choose_plan":"💰 خطط الاستثمار\n\nاختر الخطة التي تريد الاطلاع على تفاصيلها:","investment_duration":"⏱ المدة","target_return":"📈 العائد المستهدف","target_total":"🎯 القيمة المستهدفة","investment_amount":"💵 الاستثمار",
"risk":"العائد المستهدف ليس ضمانًا للربح. النتيجة الفعلية تعتمد على أداء النظام وظروف السوق وشروط الخدمة.",
"plan_details":"📋 تفاصيل الخطة","plan":"🔹 الخطة","amount":"💵 المبلغ","target_profit":"📈 العائد المستهدف","buy_plan":"🛒 تفعيل الخطة من الرصيد","back_plans":"🔙 العودة للخطط","locked":"🔒 يتم حجز المبلغ المستثمر حتى نهاية دورة الاستثمار.","plan_not_found":"❌ الخطة غير موجودة.",
"insufficient":"❌ لا يمكن تفعيل الخطة.\n\n💰 سعر الخطة: {amount:,.2f} USDT\n💼 رصيدك المتاح: {balance:,.2f} USDT\n📥 المبلغ المطلوب إضافته: {required:,.2f} USDT",
"purchase":"✅ تم تفعيل الخطة بنجاح\n\n🆔 رقم الاستثمار: #{id}\n🔹 الخطة: {plan}\n💵 المبلغ المستثمر: {amount:,.2f} USDT\n⏱ المدة: {days} أيام\n📅 البداية: {start} UTC\n📅 النهاية: {end} UTC\n\n📈 العائد المستهدف: {profit:,.2f} USDT\n🎯 القيمة المستهدفة: {total:,.2f} USDT\n\n🔒 تم حجز مبلغ الاستثمار حتى انتهاء الدورة.\n💼 رصيدك المتاح الآن: {balance:,.2f} USDT",
"deposit_choose":"➕ الإيداع\n\nاختر طريقة الإيداع:","usdt":"🟢 USDT","usdc":"🔵 USDC","btc":"🟠 BTC","eth":"🔷 ETH","sham":"🇸🇾 شام كاش",
"deposit_amount":"💳 {asset}\n\nأدخل المبلغ الذي تريد إيداعه بالدولار.\n\n💵 الحد الأدنى للإيداع: $10\n\nأرسل المبلغ الآن:",
"invalid_amount":"❌ المبلغ غير صحيح.\n\nأدخل مبلغًا رقميًا، والحد الأدنى للإيداع هو $10.",
"not_configured":"⚠️ لم يتم إعداد {asset} بعد.\nيرجى التواصل مع الإدارة.",
"crypto_details":"💳 {asset}\n\n💵 المبلغ: ${amount:,.2f}\n🌐 الشبكة: {network}\n📍 عنوان الإيداع:\n{address}\n\nبعد إتمام التحويل اضغط «تم التحويل».",
"sham_details":"🇸🇾 شام كاش\n\n💵 المبلغ: ${amount:,.2f}\n🆔 معرّف الاستلام:\n{address}\n\nبعد إتمام التحويل اضغط «تم التحويل».",
"sent":"✅ تم التحويل","reference":"🔖 رمز العملية\n\nأرسل الآن Transaction Hash / TXID الخاص بالتحويل.","sham_reference":"🔖 رمز العملية\n\nأرسل الآن رقم/رمز العملية الظاهر في Sham Cash.",
"deposit_created":"✅ تم تسجيل طلب الإيداع #{id}.\n\n💰 المبلغ: ${amount:,.2f}\n💳 الطريقة: {asset}\n⏳ الحالة: قيد مراجعة الإدارة.",
"admin_deposit":"📥 طلب إيداع جديد\n\n🆔 الطلب: #{id}\n👤 المستخدم: @{username}\nTelegram ID: {user_id}\n💳 الطريقة: {asset}\n🌐 الشبكة: {network}\n💰 المبلغ: ${amount:,.2f}\n🧾 المرجع / TX Hash:\n{reference}\n\nاختر الإجراء:",
"approve_deposit":"✅ قبول الإيداع","reject":"❌ رفض","deposit_approved":"✅ تمت الموافقة على الإيداع\n\n🆔 الطلب: #{id}\n💳 الطريقة: {asset}\n💰 المبلغ: ${amount:,.2f}\n\nتم تحديث رصيد حسابك.","deposit_rejected":"❌ تم رفض طلب الإيداع #{id}.",
"balance_title":"💼 رصيد الحساب\n\n💵 الرصيد المتاح: {balance:,.2f} USDT\n🔒 المبلغ المستثمر والمحجوز: {locked:,.2f} USDT\n\n📊 الاستثمارات النشطة: {count}",
"withdraw_help":"➖ السحب\n\nلإنشاء طلب سحب استخدم:\n\n/withdraw USDT TRC20 100 YOUR_WALLET_ADDRESS\n\n🔒 الأموال الموجودة في استثمارات نشطة غير متاحة للسحب.",
"withdraw_syntax":"❌ الصيغة الصحيحة:\n/withdraw USDT TRC20 100 YOUR_WALLET_ADDRESS","unsupported":"❌ العملة غير مدعومة.","withdraw_insufficient":"❌ الرصيد المتاح غير كافٍ.\n\n💼 المتاح: {available:,.2f} USDT\n💸 المطلوب: {amount:,.2f} USDT","withdraw_created":"✅ تم إنشاء طلب السحب #{id}.\n\n⏳ الطلب بانتظار مراجعة الإدارة.",
"admin_withdraw":"💸 طلب سحب جديد\n\n🆔 الطلب: #{id}\n👤 المستخدم: @{username}\nTelegram ID: {user_id}\n💳 العملة: {asset}\n🌐 الشبكة: {network}\n💰 المبلغ: {amount:,.2f}\n📍 محفظة المستلم:\n{wallet}\n\nاختر الإجراء:","approve_withdraw":"✅ قبول السحب","withdraw_approved":"✅ تمت الموافقة على طلب السحب\n\n🆔 الطلب: #{id}\n💳 العملة: {asset}\n💰 المبلغ: {amount:,.2f}\n\nسيتم تنفيذ التحويل ومشاركة TX Hash بعد إتمام العملية.","withdraw_rejected":"❌ تم رفض طلب السحب #{id}.\n\nلم يتم خصم أي مبلغ من رصيدك.",
"admin_panel":"👨‍💼 لوحة المسؤول\n\n/pending_deposits\n/pending_withdrawals\n/user_balance TELEGRAM_ID\n/system","no_pending_deposits":"📥 لا توجد طلبات إيداع معلقة.","no_pending_withdrawals":"💸 لا توجد طلبات سحب معلقة.","unauthorized":"⛔ غير مصرح لك.","not_found":"❌ الطلب غير موجود.","processed":"⚠️ تمت معالجة هذا الطلب مسبقًا.","admin_insufficient":"❌ الرصيد غير كافٍ.",
"admin_balance":"💰 رصيد المستخدم\n\nTelegram ID: {id}\n💵 الرصيد المتاح: {balance:,.2f} USDT\n🔒 المبلغ المستثمر: {locked:,.2f} USDT\n📊 الاستثمارات النشطة: {count}",
"system":"📊 حالة النظام\n\n🟢 البوت يعمل\n👥 المستخدمون: {users}\n📥 إيداعات معلقة: {deposits}\n💸 سحوبات معلقة: {withdrawals}\n📊 استثمارات نشطة: {investments}",
"no_investments":"📊 استثماراتي\n\nلا توجد استثمارات مسجلة حاليًا.","active":"🟢 #{id} — {plan}\n💰 المبلغ: {amount:,.2f} USDT\n🔒 الحالة: نشط ومحجوز\n⏳ المتبقي تقريبًا: {days} يوم و{hours} ساعة\n📅 الانتهاء: {end} UTC\n━━━━━━━━━━━━━━\n","waiting":"🟡 #{id} — {plan}\n⏳ بانتظار التسوية...\n━━━━━━━━━━━━━━\n","completed":"✅ #{id} — {plan}\n💰 الأصل: {amount:,.2f} USDT\n📈 العائد المستهدف: {profit:,.2f} USDT\n💵 الإجمالي المسوى: {total:,.2f} USDT\n🔓 أصبحت الأموال متاحة.\n━━━━━━━━━━━━━━\n",
"status_text":"🤖 حالة النظام\n\n🟢 البوت يعمل ويستقبل الطلبات.\n🟢 تتم مراقبة الاستثمارات المنتهية وتسويتها تلقائيًا.","about":"🚀 Quantum Grow\n\nمنصة رقمية لإدارة الحسابات والإيداعات والسحوبات والاستثمارات.\n\n🏢 الخلفية التقنية\nTrade Ideas LLC تأسست عام 2003 في الولايات المتحدة، ويظهر عنوانها في Encinitas, California.\n\n🤖 نركز على التكنولوجيا وتحليل البيانات وأدوات الذكاء الاصطناعي وتجربة رقمية منظمة.\n\nQuantum Grow\nTechnology • Intelligence • Transparency",
"completed_notice":"🎉 انتهت دورة الاستثمار\n\n🆔 الاستثمار: #{id}\n💰 أصل الاستثمار: {principal:,.2f} USDT\n📈 العائد المستهدف: {profit:,.2f} USDT\n💵 الإجمالي المسوى: {total:,.2f} USDT\n\n✅ أصبح المبلغ متاحًا في رصيدك."
},
"en": {}
}
# Use the Arabic catalog as a base for any admin fallback, then override English UI text.
T["en"] = {
"k": "v"
}
# Complete English dictionary by mapping the actual keys used above.
EN = {
"welcome":"🚀 Welcome to Quantum Grow\n\nA digital platform for managing accounts, deposits, withdrawals and investments.\n\nChoose from the menu:",
"plans":"💰 Investment Plans","deposit":"➕ Deposit","withdraw":"➖ Withdraw","balance":"💼 My Balance","investments":"📊 My Investments","status":"🤖 System Status","language":"🌐 Language","info":"ℹ️ Information","admin":"👨‍💼 Admin Panel",
"choose_language":"🌐 Language Selection\n\nChoose your preferred language:","arabic_selected":"🇸🇦 Arabic language selected.","english_selected":"🇬🇧 English language selected.","choose_plan":"💰 Investment Plans\n\nChoose a plan to view its details:","investment_duration":"⏱ Duration","target_return":"📈 Target Return","target_total":"🎯 Target Value","investment_amount":"💵 Investment","risk":"The target return is not a guarantee of profit. Actual results depend on system performance, market conditions and applicable terms.",
"plan_details":"📋 Plan Details","plan":"🔹 Plan","amount":"💵 Amount","target_profit":"📈 Target Return","buy_plan":"🛒 Activate Plan from Balance","back_plans":"🔙 Back to Plans","locked":"🔒 The invested amount is locked until the investment cycle ends.","plan_not_found":"❌ Plan not found.",
"insufficient":"❌ The plan cannot be activated.\n\n💰 Plan price: {amount:,.2f} USDT\n💼 Available balance: {balance:,.2f} USDT\n📥 Additional amount required: {required:,.2f} USDT",
"purchase":"✅ Plan activated successfully\n\n🆔 Investment ID: #{id}\n🔹 Plan: {plan}\n💵 Invested amount: {amount:,.2f} USDT\n⏱ Duration: {days} days\n📅 Start: {start} UTC\n📅 End: {end} UTC\n\n📈 Target return: {profit:,.2f} USDT\n🎯 Target value: {total:,.2f} USDT\n\n🔒 The investment amount is locked until the cycle ends.\n💼 Available balance: {balance:,.2f} USDT",
"deposit_choose":"➕ Deposit\n\nChoose a deposit method:","usdt":"🟢 USDT","usdc":"🔵 USDC","btc":"🟠 BTC","eth":"🔷 ETH","sham":"🇸🇾 Sham Cash","deposit_amount":"💳 {asset}\n\nEnter the amount you want to deposit in USD.\n\n💵 Minimum deposit: $10\n\nSend the amount now:",
"invalid_amount":"❌ Invalid amount.\n\nEnter a numeric amount. The minimum deposit is $10.","not_configured":"⚠️ {asset} has not been configured yet.\nPlease contact administration.","crypto_details":"💳 {asset}\n\n💵 Amount: ${amount:,.2f}\n🌐 Network: {network}\n📍 Deposit address:\n{address}\n\nAfter completing the transfer, press “Transfer Sent”.","sham_details":"🇸🇾 Sham Cash\n\n💵 Amount: ${amount:,.2f}\n🆔 Receiving ID:\n{address}\n\nAfter completing the transfer, press “Transfer Sent”.","sent":"✅ Transfer Sent","reference":"🔖 Transaction Reference\n\nSend the Transaction Hash / TXID for your transfer.","sham_reference":"🔖 Transaction Reference\n\nSend the transaction/reference number shown by Sham Cash.",
"deposit_created":"✅ Deposit request #{id} has been recorded.\n\n💰 Amount: ${amount:,.2f}\n💳 Method: {asset}\n⏳ Status: Pending administrative review.","admin_deposit":"📥 New Deposit Request\n\n🆔 Request: #{id}\n👤 User: @{username}\nTelegram ID: {user_id}\n💳 Method: {asset}\n🌐 Network: {network}\n💰 Amount: ${amount:,.2f}\n🧾 Reference / TX Hash:\n{reference}\n\nChoose an action:","approve_deposit":"✅ Approve Deposit","reject":"❌ Reject","deposit_approved":"✅ Deposit approved\n\n🆔 Request: #{id}\n💳 Method: {asset}\n💰 Amount: ${amount:,.2f}\n\nYour account balance has been updated.","deposit_rejected":"❌ Deposit request #{id} was rejected.",
"balance_title":"💼 Account Balance\n\n💵 Available balance: {balance:,.2f} USDT\n🔒 Locked investment amount: {locked:,.2f} USDT\n\n📊 Active investments: {count}","withdraw_help":"➖ Withdraw\n\nTo create a withdrawal request use:\n\n/withdraw USDT TRC20 100 YOUR_WALLET_ADDRESS\n\n🔒 Funds in active investments are not available for withdrawal.","withdraw_syntax":"❌ Correct format:\n/withdraw USDT TRC20 100 YOUR_WALLET_ADDRESS","unsupported":"❌ Unsupported currency.","withdraw_insufficient":"❌ Available balance is insufficient.\n\n💼 Available: {available:,.2f} USDT\n💸 Required: {amount:,.2f} USDT","withdraw_created":"✅ Withdrawal request #{id} has been created.\n\n⏳ The request is waiting for administrative review.","admin_withdraw":"💸 New Withdrawal Request\n\n🆔 Request: #{id}\n👤 User: @{username}\nTelegram ID: {user_id}\n💳 Asset: {asset}\n🌐 Network: {network}\n💰 Amount: {amount:,.2f}\n📍 Destination wallet:\n{wallet}\n\nChoose an action:","approve_withdraw":"✅ Approve Withdrawal","withdraw_approved":"✅ Withdrawal request approved\n\n🆔 Request: #{id}\n💳 Asset: {asset}\n💰 Amount: {amount:,.2f}\n\nThe transfer will be processed and the TX Hash shared after completion.","withdraw_rejected":"❌ Withdrawal request #{id} was rejected.\n\nNo amount was deducted from your balance.",
"admin_panel":"👨‍💼 Admin Panel\n\n/pending_deposits\n/pending_withdrawals\n/user_balance TELEGRAM_ID\n/system","no_pending_deposits":"📥 No pending deposit requests.","no_pending_withdrawals":"💸 No pending withdrawal requests.","unauthorized":"⛔ You are not authorized.","not_found":"❌ Request not found.","processed":"⚠️ This request has already been processed.","admin_insufficient":"❌ Insufficient balance.","admin_balance":"💰 User Balance\n\nTelegram ID: {id}\n💵 Available balance: {balance:,.2f} USDT\n🔒 Invested amount: {locked:,.2f} USDT\n📊 Active investments: {count}","system":"📊 System Status\n\n🟢 Bot is running\n👥 Users: {users}\n📥 Pending deposits: {deposits}\n💸 Pending withdrawals: {withdrawals}\n📊 Active investments: {investments}","no_investments":"📊 My Investments\n\nThere are currently no registered investments.","active":"🟢 #{id} — {plan}\n💰 Amount: {amount:,.2f} USDT\n🔒 Status: Active and locked\n⏳ Approximately remaining: {days} days and {hours} hours\n📅 End: {end} UTC\n━━━━━━━━━━━━━━\n","waiting":"🟡 #{id} — {plan}\n⏳ Waiting for settlement...\n━━━━━━━━━━━━━━\n","completed":"✅ #{id} — {plan}\n💰 Principal: {amount:,.2f} USDT\n📈 Target return: {profit:,.2f} USDT\n💵 Settled total: {total:,.2f} USDT\n🔓 Funds are now available.\n━━━━━━━━━━━━━━\n","status_text":"🤖 System Status\n\n🟢 The bot is running and accepting requests.\n🟢 Finished investments are monitored and settled automatically.","about":"🚀 Quantum Grow\n\nA digital platform for account, deposit, withdrawal and investment management.\n\n🏢 Technical background\nTrade Ideas LLC was founded in 2003 in the United States, with its listed address in Encinitas, California.\n\n🤖 We focus on technology, data analysis, AI-related tools and a structured digital experience.\n\nQuantum Grow\nTechnology • Intelligence • Transparency","completed_notice":"🎉 Investment cycle completed\n\n🆔 Investment: #{id}\n💰 Principal: {principal:,.2f} USDT\n📈 Target return: {profit:,.2f} USDT\n💵 Settled total: {total:,.2f} USDT\n\n✅ The amount is now available in your balance."
}
T["en"] = EN

def tr(lang, key, **kw):
    lang = lang if lang in T else "ar"
    s = T[lang].get(key, T["ar"].get(key, key))
    try:
        return s.format(**kw)
    except (KeyError, ValueError):
        return s

async def ensure_user(message):
    uid = message.from_user.id
    with SessionLocal() as db:
        u = db.scalar(select(User).where(User.telegram_id == uid))
        if not u:
            db.add(User(telegram_id=uid, username=message.from_user.username, language="ar"))
        else:
            u.username = message.from_user.username
        b = db.scalar(select(DemoBalance).where(DemoBalance.telegram_id == uid))
        if not b:
            db.add(DemoBalance(telegram_id=uid, balance=0.0))
        db.commit()

def get_language(uid):
    with SessionLocal() as db:
        u = db.scalar(select(User).where(User.telegram_id == uid))
        return u.language if u and u.language in ("ar","en") else "ar"

def set_language(uid, lang):
    with SessionLocal() as db:
        u = db.scalar(select(User).where(User.telegram_id == uid))
        if u:
            u.language = lang
            db.commit()

def main_keyboard(lang):
    rows = [
        [KeyboardButton(text=tr(lang,"plans")), KeyboardButton(text=tr(lang,"deposit"))],
        [KeyboardButton(text=tr(lang,"withdraw")), KeyboardButton(text=tr(lang,"balance"))],
        [KeyboardButton(text=tr(lang,"investments")), KeyboardButton(text=tr(lang,"status"))],
        [KeyboardButton(text=tr(lang,"language")), KeyboardButton(text=tr(lang,"info"))],
    ]
    if settings.admin_telegram_id:
        rows.append([KeyboardButton(text=tr(lang,"admin"))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇸🇦 العربية", callback_data="lang:ar"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")
    ]])

def payment_keyboard(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr(lang,"usdt"), callback_data="depmethod:USDT")],
        [InlineKeyboardButton(text=tr(lang,"usdc"), callback_data="depmethod:USDC")],
        [InlineKeyboardButton(text=tr(lang,"btc"), callback_data="depmethod:BTC")],
        [InlineKeyboardButton(text=tr(lang,"eth"), callback_data="depmethod:ETH")],
        [InlineKeyboardButton(text=tr(lang,"sham"), callback_data="depmethod:SHAM_CASH")],
    ])

def payment_details(asset):
    return {
        "USDT": (settings.usdt_network, settings.usdt_address),
        "USDC": (settings.usdc_network, settings.usdc_address),
        "BTC": (settings.btc_network, settings.btc_address),
        "ETH": (settings.eth_network, settings.eth_address),
        "SHAM_CASH": ("Sham Cash", settings.sham_cash_id),
    }.get(asset, ("",""))

def is_admin(uid):
    return settings.admin_telegram_id != 0 and uid == settings.admin_telegram_id

async def send_admin(text, markup=None):
    if settings.admin_telegram_id:
        await bot.send_message(settings.admin_telegram_id, text, reply_markup=markup)

class DepositState(StatesGroup):
    amount = State()
    reference = State()

@dp.message(CommandStart())
async def start(message: Message):
    await ensure_user(message)
    lang = get_language(message.from_user.id)
    await message.answer(tr(lang,"welcome"), reply_markup=main_keyboard(lang))

@dp.message(F.text.in_(["🌐 اللغة","🌐 Language"]))
async def language(message: Message):
    lang = get_language(message.from_user.id)
    await message.answer(tr(lang,"choose_language"), reply_markup=language_keyboard())

@dp.callback_query(F.data.startswith("lang:"))
async def language_callback(callback: CallbackQuery):
    lang = callback.data.split(":",1)[1]
    if lang not in ("ar","en"):
        await callback.answer()
        return
    await ensure_user(callback.message)
    set_language(callback.from_user.id, lang)
    await callback.message.answer(tr(lang, "arabic_selected" if lang=="ar" else "english_selected"),
                                  reply_markup=main_keyboard(lang))
    await callback.answer()

def plan_keyboard(rows):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💰 {p.name} — {p.amount:,.0f} USDT", callback_data=f"plan:{p.id}")]
        for p in rows
    ])

@dp.message(F.text.in_(["💰 خطط الاستثمار","💰 Investment Plans"]))
async def plans(message: Message):
    await ensure_user(message)
    lang = get_language(message.from_user.id)
    with SessionLocal() as db:
        rows = db.scalars(select(InvestmentPlan).where(InvestmentPlan.is_active == True).order_by(InvestmentPlan.amount)).all()
    text = tr(lang,"choose_plan") + "\n\n"
    for p in rows:
        profit = p.amount*p.target_rate
        text += f"🔹 {p.name}\n{tr(lang,'investment_amount')}: {p.amount:,.2f} USDT\n{tr(lang,'investment_duration')}: {p.duration_days} days\n{tr(lang,'target_return')}: {p.target_rate*100:.0f}%\n{tr(lang,'target_total')}: {p.amount+profit:,.2f} USDT\n━━━━━━━━━━━━━━\n"
    await message.answer(text + "\n" + tr(lang,"risk"), reply_markup=plan_keyboard(rows))

@dp.callback_query(F.data.startswith("plan:"))
async def plan_details(callback: CallbackQuery):
    pid = int(callback.data.split(":")[1]); lang = get_language(callback.from_user.id)
    with SessionLocal() as db:
        p = db.scalar(select(InvestmentPlan).where(InvestmentPlan.id==pid, InvestmentPlan.is_active==True))
    if not p:
        await callback.answer(tr(lang,"plan_not_found"), show_alert=True); return
    profit=p.amount*p.target_rate; total=p.amount+profit
    markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr(lang,"buy_plan"), callback_data=f"buyplan:{p.id}")],
        [InlineKeyboardButton(text=tr(lang,"back_plans"), callback_data="backplans")]
    ])
    text=f"{tr(lang,'plan_details')}\n\n{tr(lang,'plan')}: {p.name}\n{tr(lang,'amount')}: {p.amount:,.2f} USDT\n{tr(lang,'investment_duration')}: {p.duration_days} days\n{tr(lang,'target_return')}: {p.target_rate*100:.0f}%\n{tr(lang,'target_profit')}: {profit:,.2f} USDT\n{tr(lang,'target_total')}: {total:,.2f} USDT\n\n{tr(lang,'locked')}\n\n{tr(lang,'risk')}"
    await callback.message.answer(text, reply_markup=markup); await callback.answer()

@dp.callback_query(F.data=="backplans")
async def backplans(callback: CallbackQuery):
    lang=get_language(callback.from_user.id)
    with SessionLocal() as db:
        rows=db.scalars(select(InvestmentPlan).where(InvestmentPlan.is_active==True).order_by(InvestmentPlan.amount)).all()
    await callback.message.answer(tr(lang,"choose_plan"), reply_markup=plan_keyboard(rows)); await callback.answer()

@dp.callback_query(F.data.startswith("buyplan:"))
async def buyplan(callback: CallbackQuery):
    pid=int(callback.data.split(":")[1]); uid=callback.from_user.id; lang=get_language(uid)
    with SessionLocal() as db:
        p=db.scalar(select(InvestmentPlan).where(InvestmentPlan.id==pid, InvestmentPlan.is_active==True))
        if not p:
            await callback.answer(tr(lang,"plan_not_found"),show_alert=True); return
        b=db.scalar(select(DemoBalance).where(DemoBalance.telegram_id==uid))
        if not b:
            b=DemoBalance(telegram_id=uid,balance=0.0); db.add(b); db.commit()
        if b.balance < p.amount:
            await callback.message.answer(tr(lang,"insufficient",amount=p.amount,balance=b.balance,required=p.amount-b.balance))
            await callback.answer("Insufficient balance." if lang=="en" else "الرصيد غير كافٍ.",show_alert=True); return
        now=datetime.utcnow(); end=now+timedelta(days=p.duration_days); profit=p.amount*p.target_rate
        b.balance-=p.amount
        inv=Investment(telegram_id=uid,plan_id=p.id,amount=p.amount,target_profit=profit,status="active",started_at=now,ends_at=end)
        db.add(inv); db.commit()
        iid=inv.id; remaining=b.balance
    await callback.message.answer(tr(lang,"purchase",id=iid,plan=p.name,amount=p.amount,days=p.duration_days,start=now.strftime("%Y-%m-%d %H:%M"),end=end.strftime("%Y-%m-%d %H:%M"),profit=profit,total=p.amount+profit,balance=remaining))
    await callback.answer("Plan activated." if lang=="en" else "تم تفعيل الخطة.")

# ---------------------------------------------------------------------
# NEW DEPOSIT FLOW: currency -> amount -> address -> transaction reference
# ---------------------------------------------------------------------

@dp.message(F.text.in_(["➕ الإيداع","➕ Deposit"]))
async def deposit(message: Message, state: FSMContext):
    await ensure_user(message); await state.clear()
    lang=get_language(message.from_user.id)
    await message.answer(tr(lang,"deposit_choose"), reply_markup=payment_keyboard(lang))

@dp.callback_query(F.data.startswith("depmethod:"))
async def deposit_currency(callback: CallbackQuery, state: FSMContext):
    asset=callback.data.split(":",1)[1]; lang=get_language(callback.from_user.id)
    network,address=payment_details(asset)
    if not address:
        await callback.message.answer(tr(lang,"not_configured",asset=asset)); await callback.answer(); return
    await state.clear()
    await state.update_data(asset=asset,network=network,address=address)
    await state.set_state(DepositState.amount)
    name="Sham Cash" if asset=="SHAM_CASH" else asset
    await callback.message.answer(tr(lang,"deposit_amount",asset=name))
    await callback.answer()

@dp.message(DepositState.amount)
async def deposit_amount(message: Message, state: FSMContext):
    lang=get_language(message.from_user.id)
    try:
        amount=float((message.text or "").replace(",","").strip())
        if amount < 10: raise ValueError
    except (ValueError,TypeError):
        await message.answer(tr(lang,"invalid_amount")); return
    data=await state.get_data()
    asset,network,address=data.get("asset"),data.get("network"),data.get("address")
    if not asset or not address:
        await state.clear(); await message.answer(tr(lang,"not_configured",asset=asset or "Payment")); return
    await state.update_data(amount=amount)
    await state.set_state(DepositState.reference)
    if asset=="SHAM_CASH":
        text=tr(lang,"sham_details",amount=amount,address=address)
    else:
        text=tr(lang,"crypto_details",asset=asset,amount=amount,network=network,address=address)
    markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=tr(lang,"sent"),callback_data="depsent")]])
    await message.answer(text,reply_markup=markup)

@dp.callback_query(F.data=="depsent")
async def deposit_sent(callback: CallbackQuery, state: FSMContext):
    lang=get_language(callback.from_user.id); data=await state.get_data()
    if not data.get("asset") or not data.get("amount"):
        await state.clear(); await callback.answer(tr(lang,"deposit_choose"),show_alert=True); return
    await callback.message.answer(tr(lang,"sham_reference" if data["asset"]=="SHAM_CASH" else "reference"))
    await callback.answer()

@dp.message(DepositState.reference)
async def deposit_reference(message: Message, state: FSMContext):
    lang=get_language(message.from_user.id); reference=(message.text or "").strip()
    if not reference:
        await message.answer(tr(lang,"reference")); return
    data=await state.get_data()
    asset,network,amount=data.get("asset"),data.get("network"),data.get("amount")
    if not asset or not network or not amount:
        await state.clear(); await message.answer(tr(lang,"deposit_choose")); return
    await ensure_user(message)
    with SessionLocal() as db:
        req=DepositRequest(telegram_id=message.from_user.id,asset=asset,network=network,amount=amount,tx_hash=reference,status="pending")
        db.add(req); db.commit(); rid=req.id
    markup=InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr("ar","approve_deposit"),callback_data=f"depapprove:{rid}"),
        InlineKeyboardButton(text=tr("ar","reject"),callback_data=f"depreject:{rid}")
    ]])
    username=message.from_user.username or "no_username"
    await send_admin(tr("ar","admin_deposit",id=rid,username=username,user_id=message.from_user.id,asset="Sham Cash" if asset=="SHAM_CASH" else asset,network=network,amount=amount,reference=reference),markup)
    await message.answer(tr(lang,"deposit_created",id=rid,amount=amount,asset="Sham Cash" if asset=="SHAM_CASH" else asset),reply_markup=main_keyboard(lang))
    await state.clear()

@dp.message(Command("deposit"))
async def deposit_command(message: Message):
    lang = get_language(message.from_user.id)
    await message.answer(tr(lang,"deposit_choose"), reply_markup=payment_keyboard(lang))

@dp.callback_query(F.data.startswith("depapprove:"))
async def approve_deposit(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer(tr("ar","unauthorized"),show_alert=True); return
    rid=int(callback.data.split(":")[1])
    with SessionLocal() as db:
        req=db.scalar(select(DepositRequest).where(DepositRequest.id==rid))
        if not req: await callback.answer(tr("ar","not_found"),show_alert=True); return
        if req.status!="pending": await callback.answer(tr("ar","processed"),show_alert=True); return
        bal=db.scalar(select(DemoBalance).where(DemoBalance.telegram_id==req.telegram_id))
        if not bal: bal=DemoBalance(telegram_id=req.telegram_id,balance=0.0); db.add(bal)
        bal.balance+=req.amount; req.status="approved"; db.commit()
        uid,amount,asset=req.telegram_id,req.amount,req.asset
    await bot.send_message(uid,tr(get_language(uid),"deposit_approved",id=rid,asset="Sham Cash" if asset=="SHAM_CASH" else asset,amount=amount))
    await callback.message.edit_text(callback.message.text+"\n\n✅ تمت الموافقة وتحديث الرصيد."); await callback.answer("Deposit approved.")

@dp.callback_query(F.data.startswith("depreject:"))
async def reject_deposit(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer(tr("ar","unauthorized"),show_alert=True); return
    rid=int(callback.data.split(":")[1])
    with SessionLocal() as db:
        req=db.scalar(select(DepositRequest).where(DepositRequest.id==rid))
        if not req: await callback.answer(tr("ar","not_found"),show_alert=True); return
        if req.status!="pending": await callback.answer(tr("ar","processed"),show_alert=True); return
        req.status="rejected"; db.commit(); uid=req.telegram_id
    await bot.send_message(uid,tr(get_language(uid),"deposit_rejected",id=rid))
    await callback.message.edit_text(callback.message.text+"\n\n❌ تم رفض الطلب."); await callback.answer("Deposit rejected.")

@dp.message(F.text.in_(["💼 رصيدي","💼 My Balance"]))
async def balance(message: Message):
    await ensure_user(message); lang=get_language(message.from_user.id)
    with SessionLocal() as db:
        b=db.scalar(select(DemoBalance).where(DemoBalance.telegram_id==message.from_user.id))
        invs=db.scalars(select(Investment).where(Investment.telegram_id==message.from_user.id,Investment.status=="active")).all()
    await message.answer(tr(lang,"balance_title",balance=b.balance if b else 0,locked=sum(i.amount for i in invs),count=len(invs)))

@dp.message(F.text.in_(["➖ السحب","➖ Withdraw"]))
async def withdrawal(message: Message):
    await ensure_user(message); await message.answer(tr(get_language(message.from_user.id),"withdraw_help"))

@dp.message(Command("withdraw"))
async def withdraw(message: Message):
    lang=get_language(message.from_user.id); parts=message.text.split(maxsplit=4)
    if len(parts)!=5: await message.answer(tr(lang,"withdraw_syntax")); return
    _,asset,network,amount_s,wallet=parts; asset=asset.upper(); network=network.upper()
    if asset not in ["USDT","USDC","BTC","ETH","SHAM_CASH"]: await message.answer(tr(lang,"unsupported")); return
    try: amount=float(amount_s); assert amount>0
    except: await message.answer(tr(lang,"invalid_amount")); return
    await ensure_user(message)
    with SessionLocal() as db:
        b=db.scalar(select(DemoBalance).where(DemoBalance.telegram_id==message.from_user.id))
        if not b or b.balance<amount:
            await message.answer(tr(lang,"withdraw_insufficient",available=b.balance if b else 0,amount=amount)); return
        req=WithdrawalRequest(telegram_id=message.from_user.id,asset=asset,network=network,amount=amount,wallet_address=wallet,status="pending")
        db.add(req); db.commit(); rid=req.id
    markup=InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr("ar","approve_withdraw"),callback_data=f"withapprove:{rid}"),
        InlineKeyboardButton(text=tr("ar","reject"),callback_data=f"withreject:{rid}")
    ]])
    await send_admin(tr("ar","admin_withdraw",id=rid,username=message.from_user.username or "no_username",user_id=message.from_user.id,asset=asset,network=network,amount=amount,wallet=wallet),markup)
    await message.answer(tr(lang,"withdraw_created",id=rid))

@dp.callback_query(F.data.startswith("withapprove:"))
async def approve_withdraw(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): await callback.answer(tr("ar","unauthorized"),show_alert=True); return
    rid=int(callback.data.split(":")[1])
    with SessionLocal() as db:
        req=db.scalar(select(WithdrawalRequest).where(WithdrawalRequest.id==rid))
        if not req: await callback.answer(tr("ar","not_found"),show_alert=True); return
        if req.status!="pending": await callback.answer(tr("ar","processed"),show_alert=True); return
        b=db.scalar(select(DemoBalance).where(DemoBalance.telegram_id==req.telegram_id))
        if not b or b.balance<req.amount: await callback.answer(tr("ar","admin_insufficient"),show_alert=True); return
        b.balance-=req.amount; req.status="approved"; db.commit(); uid,amount,asset=req.telegram_id,req.amount,req.asset
    await bot.send_message(uid,tr(get_language(uid),"withdraw_approved",id=rid,asset=asset,amount=amount))
    await callback.message.edit_text(callback.message.text+"\n\n✅ تمت الموافقة وخصم المبلغ من الرصيد."); await callback.answer("Withdrawal approved.")

@dp.callback_query(F.data.startswith("withreject:"))
async def reject_withdraw(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): await callback.answer(tr("ar","unauthorized"),show_alert=True); return
    rid=int(callback.data.split(":")[1])
    with SessionLocal() as db:
        req=db.scalar(select(WithdrawalRequest).where(WithdrawalRequest.id==rid))
        if not req: await callback.answer(tr("ar","not_found"),show_alert=True); return
        if req.status!="pending": await callback.answer(tr("ar","processed"),show_alert=True); return
        req.status="rejected"; db.commit(); uid=req.telegram_id
    await bot.send_message(uid,tr(get_language(uid),"withdraw_rejected",id=rid))
    await callback.message.edit_text(callback.message.text+"\n\n❌ تم رفض طلب السحب."); await callback.answer("Withdrawal rejected.")

@dp.message(F.text.in_(["📊 استثماراتي","📊 My Investments"]))
async def investments(message: Message):
    await ensure_user(message); lang=get_language(message.from_user.id); await settle_finished()
    with SessionLocal() as db:
        rows=db.scalars(select(Investment).where(Investment.telegram_id==message.from_user.id).order_by(Investment.id.desc())).all()
        pm={p.id:p for p in db.scalars(select(InvestmentPlan)).all()}
    if not rows: await message.answer(tr(lang,"no_investments")); return
    text=tr(lang,"investments")+"\n\n"; now=datetime.utcnow()
    for i in rows:
        p=pm.get(i.plan_id); name=p.name if p else f"Plan #{i.plan_id}"
        if i.status=="active":
            r=i.ends_at-now
            if r.total_seconds()>0: text+=tr(lang,"active",id=i.id,plan=name,amount=i.amount,days=r.days,hours=r.seconds//3600,end=i.ends_at.strftime("%Y-%m-%d %H:%M"))
            else: text+=tr(lang,"waiting",id=i.id,plan=name)
        else: text+=tr(lang,"completed",id=i.id,plan=name,amount=i.amount,profit=i.target_profit,total=i.amount+i.target_profit)
    await message.answer(text)

async def settle_finished():
    now=datetime.utcnow(); done=[]
    with SessionLocal() as db:
        rows=db.scalars(select(Investment).where(Investment.status=="active",Investment.ends_at<=now)).all()
        for i in rows:
            b=db.scalar(select(DemoBalance).where(DemoBalance.telegram_id==i.telegram_id))
            if not b: b=DemoBalance(telegram_id=i.telegram_id,balance=0.0); db.add(b)
            total=i.amount+i.target_profit; b.balance+=total; i.status="completed"; i.completed_at=now
            done.append((i.telegram_id,i.id,i.amount,i.target_profit,total))
        db.commit()
    for uid,iid,p,profit,total in done:
        try: await bot.send_message(uid,tr(get_language(uid),"completed_notice",id=iid,principal=p,profit=profit,total=total))
        except: pass

async def settlement_loop():
    while True:
        try: await settle_finished()
        except Exception as e: print("Settlement error:",e)
        await asyncio.sleep(60)

@dp.message(F.text.in_(["🤖 حالة النظام","🤖 System Status"]))
async def status(message: Message):
    await message.answer(tr(get_language(message.from_user.id),"status_text"))

@dp.message(F.text.in_(["ℹ️ معلومات","ℹ️ Information"]))
async def about(message: Message):
    await message.answer(tr(get_language(message.from_user.id),"about"))

@dp.message(F.text.in_(["👨‍💼 لوحة المسؤول","👨‍💼 Admin Panel"]))
async def admin_button(message: Message):
    if not is_admin(message.from_user.id): await message.answer(tr(get_language(message.from_user.id),"unauthorized")); return
    await message.answer(tr("ar","admin_panel"))

@dp.message(Command("admin"))
async def admin(message: Message):
    if is_admin(message.from_user.id): await message.answer(tr("ar","admin_panel"))
    else: await message.answer(tr(get_language(message.from_user.id),"unauthorized"))

@dp.message(Command("pending_deposits"))
async def pending_deposits(message: Message):
    if not is_admin(message.from_user.id): await message.answer(tr("ar","unauthorized")); return
    with SessionLocal() as db: rows=db.scalars(select(DepositRequest).where(DepositRequest.status=="pending").order_by(DepositRequest.id.desc())).all()
    if not rows: await message.answer(tr("ar","no_pending_deposits")); return
    text="📥 طلبات الإيداع المعلقة\n\n"
    for r in rows: text+=f"#{r.id} | {r.asset} | ${r.amount:,.2f}\n👤 {r.telegram_id}\n🌐 {r.network}\n🧾 {r.tx_hash}\n━━━━━━━━━━━━━━\n"
    await message.answer(text)

@dp.message(Command("pending_withdrawals"))
async def pending_withdrawals(message: Message):
    if not is_admin(message.from_user.id): await message.answer(tr("ar","unauthorized")); return
    with SessionLocal() as db: rows=db.scalars(select(WithdrawalRequest).where(WithdrawalRequest.status=="pending").order_by(WithdrawalRequest.id.desc())).all()
    if not rows: await message.answer(tr("ar","no_pending_withdrawals")); return
    text="💸 طلبات السحب المعلقة\n\n"
    for r in rows: text+=f"#{r.id} | {r.asset} | {r.amount:,.2f}\n👤 {r.telegram_id}\n🌐 {r.network}\n📍 {r.wallet_address}\n━━━━━━━━━━━━━━\n"
    await message.answer(text)

@dp.message(Command("user_balance"))
async def user_balance(message: Message):
    if not is_admin(message.from_user.id): await message.answer(tr("ar","unauthorized")); return
    parts=message.text.split()
    if len(parts)!=2: await message.answer("الصيغة: /user_balance TELEGRAM_ID"); return
    try: uid=int(parts[1])
    except: await message.answer("❌ Telegram ID غير صحيح."); return
    with SessionLocal() as db:
        b=db.scalar(select(DemoBalance).where(DemoBalance.telegram_id==uid))
        invs=db.scalars(select(Investment).where(Investment.telegram_id==uid,Investment.status=="active")).all()
    await message.answer(tr("ar","admin_balance",id=uid,balance=b.balance if b else 0,locked=sum(i.amount for i in invs),count=len(invs)))

@dp.message(Command("system"))
async def system(message: Message):
    if not is_admin(message.from_user.id): await message.answer(tr("ar","unauthorized")); return
    with SessionLocal() as db:
        users=db.scalars(select(User)).all()
        deps=db.scalars(select(DepositRequest).where(DepositRequest.status=="pending")).all()
        withs=db.scalars(select(WithdrawalRequest).where(WithdrawalRequest.status=="pending")).all()
        invs=db.scalars(select(Investment).where(Investment.status=="active")).all()
    await message.answer(tr("ar","system",users=len(users),deposits=len(deps),withdrawals=len(withs),investments=len(invs)))

async def main():
    print("Quantum Grow bot is starting...")
    task=asyncio.create_task(settlement_loop())
    try: await dp.start_polling(bot)
    finally:
        task.cancel()
        try: await task
        except asyncio.CancelledError: pass

if __name__ == "__main__":
    asyncio.run(main())
