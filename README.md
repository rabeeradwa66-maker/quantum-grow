# Quantum Grow

Starter MVP for a bilingual (Arabic/English) Telegram trading/investment interface.

## Stack
- Python 3.12
- FastAPI
- aiogram 3
- SQLAlchemy + SQLite for local development (switch to PostgreSQL with DATABASE_URL)
- Telegram Web App-ready frontend

## Run
1. Copy `.env.example` to `.env`.
2. Set `TELEGRAM_BOT_TOKEN`.
3. Install: `pip install -r requirements.txt`
4. Start API: `uvicorn app.main:app --reload`
5. Start bot: `python -m app.bot`

The first version intentionally does not custody funds, promise returns, or implement real-money withdrawals. Payment/broker adapters are placeholders to be connected only after selecting compliant providers.
