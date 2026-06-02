from sqlalchemy import String, Date, Float, BigInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression
from app.extensions import db
from decimal import Decimal
from datetime import date
import datetime


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


    def to_dict(self):

        data = {}
        excluded_cols = ['id']

        for column in self.__table__.columns:

            value = getattr(self, column.name)

            if column.name in excluded_cols:
                continue

            # Dates and Datetimes => ISO 8601 strings
            if isinstance(value, (datetime.date, datetime.datetime)):
                data[column.name] = value.isoformat() if value else None

            # Decimals => floats
            elif isinstance(value, Decimal):
                data[column.name] = float(value) if value is not None else None

            else:
                data[column.name] = value

        return data


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