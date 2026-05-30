from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert
from app.extensions import db
from app.models import Stock, TrackedTicker

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class MktDataSvc:

    @classmethod
    def _active_mktdata_query(cls):

        return db.select(Stock)

    @classmethod
    def _prepare_data_dict(cls, df: pd.DataFrame) -> dict:
        """
        Converts the latest DataFrame row into a clean dictionary,
        handling Pandas/NumPy types and matching database columns.

        Args:
            df: a pd.DataFrame containing the stock data to be converted
            to a dictionary

        Returns:
            dict: the resulting dictionary object converted from pd.DataFrame
        """
        if df.empty:
            raise ValueError("DataFrame is empty.")

        cleaned_df = df.replace({np.nan: None, pd.NA: None})

        # Get a list of valid column names from the database model
        valid_columns = Stock.__table__.columns.keys()
        entry_dict = {}

        for column_name, value in cleaned_df.iloc[-1].items():

            # 1. Ignore columns that don't exist in database
            if column_name not in valid_columns:
                continue

            # 2. Handle missing data
            if value is None:
                entry_dict[column_name] = None
                continue

            # 3. Convert Pandas Timestamp to native Python Date
            if column_name == 'trade_date':
                value = value.date()

            # 4. Convert NumPy numeric types to standard Python types
            elif hasattr(value, 'item'):
                value = value.item()

            entry_dict[column_name] = value

        return entry_dict

    @classmethod
    def load_data(cls, df: pd.DataFrame):
        """
        Loads the latest market data entry to the database.

        Args:
            df: a pd.Dataframe containing the latest stock data
        """

        entry_dict = cls._prepare_data_dict(df)

        # Create the base Postgres Insert statement
        stmt = insert(Stock).values(entry_dict)

        # The Upsert Logic
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=['ticker', 'trade_date'],
            set_={
                col: getattr(stmt.excluded, col)
                for col in entry_dict.keys()
                if col not in ['ticker', 'trade_date']
            }
        )

        try:
            # Execute and Commit
            db.session.execute(upsert_stmt)
            db.session.commit()

        except SQLAlchemyError as e:

            logger.error(f"Database transaction failed for {entry_dict.get('ticker')}: {e}")
            db.session.rollback()
            raise ValueError(f"Failed to load data for {entry_dict.get('ticker')}")


class TickerSvc:

    @classmethod
    def get_active_tickers(cls) -> list[TrackedTicker]:
        """
        Get a list of all active stock tickers from the db

        Returns:
            list[TrackedTicker]: A list of TrackedTicker objects
        """
        query = db.select(TrackedTicker).where(TrackedTicker.is_active == True)

        return db.session.scalars(query).all()

    @classmethod
    def get_ticker_by_name(cls, ticker_symbol: str) -> TrackedTicker | None:
        """
        Get the TrackedTicker based on the ticker string.

        Args:
            ticker_symbol: The stock ticker that needs to be pulled

        Returns:
           TrackedTicker: The matching TrackedTicker
        """
        query = db.select(TrackedTicker).where(TrackedTicker.ticker == ticker_symbol)

        return db.session.execute(query).scalar_one_or_none()

    @classmethod
    def add_new_ticker(cls, ticker_symbol: str, auto_commit: bool = True) -> bool:
        """
        Attempts to add a new ticker using Postgres ON CONFLICT DO NOTHING.

        Args:
            ticker_symbol: The stock ticker that needs to be added
            auto_commit: Default `false`. Automatically commits new session additions
                to the database if `true`.

        Returns:
            bool: True if inserted, False if it was ignored (already exists).
        """
        insert_stmt = insert(TrackedTicker).values(
            ticker=ticker_symbol,
            is_active=True
        )

        stmt_w_ignore = insert_stmt.on_conflict_do_nothing(
            index_elements=['ticker']
        ).returning(TrackedTicker.id)

        try:
            result = db.session.execute(stmt_w_ignore)
            if auto_commit:
                db.session.commit()

        except SQLAlchemyError as e:
            db.session.rollback()

            logger.error(f"Database error while adding ticker {ticker_symbol}. Error: {e}")
            raise ValueError(f"Failed to add ticker{ticker_symbol}")

        inserted_id = result.scalar()

        return inserted_id is not None

    @classmethod
    def save_changes(cls) -> tuple[bool, str | None]:
        """
        Commits any pending session changes to the database safely.

        Returns:
            tuple[bool, str | None]: Boolean value and error string
            if failed or None if successful
        """
        try:
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            return False, str(e)

        return True, None