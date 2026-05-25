from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert
from app.extensions import db
from app.models import Stock
from app.services import fetch_latest_stock_data

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class StockSvc:

    @classmethod
    def _active_messages_query(cls):

        return db.select(Stock)

    @classmethod
    def _prepare_data_dict(cls, df: pd.DataFrame) -> dict:
        """
        Converts the latest DataFrame row into a clean dictionary,
        handling Pandas/NumPy types and matching database columns.
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

        entry_dict = cls._prepare_data_dict(df)

        try:
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

            # Execute and Commit
            db.session.execute(upsert_stmt)
            db.session.commit()

        except SQLAlchemyError as e:

            logger.error(f"Database transaction failed for {entry_dict.get('ticker')}: {e}")
            db.session.rollback()
            raise ValueError(f"Failed to load data for {entry_dict.get('ticker')}")