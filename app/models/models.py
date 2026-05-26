from datetime import date
from sqlalchemy import String, Date, Float, BigInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression
from app.extensions import db


class Stock(db.Model):
    __tablename__ = 'stocks'

    # Prevents duplicate rows and allows for "Upsert" logic
    __table_args__ = (
        UniqueConstraint('ticker', 'trade_date', name='uq_ticker_trade_date'),
    )

    # Required columns
    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(15), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    close_price: Mapped[float] = mapped_column(Float, nullable=False)

    # Non Required
    open_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    high_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    low_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Computed
    rsi_14: Mapped[float | None] = mapped_column(Float, nullable=True)
    macd_line: Mapped[float | None] = mapped_column(Float, nullable=True)
    ema_50: Mapped[float | None] = mapped_column(Float, nullable=True)

class TrackedTicker(db.Model):
    __tablename__ = 'tracked_tickers'
    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(
        String(15),
        unique=True,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        server_default=expression.true(),
        nullable=False
    )