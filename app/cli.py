import click
from app import db
from app.models import TrackedTicker
from flask.cli import with_appcontext


@click.command(name='get-stock-data')
@with_appcontext
def get_stock_data_command():
    pass



@click.command(name='seed-tickers')
@with_appcontext
def seed_tickers_command():
    """Seeds the TrackedTicker table with an initial batch of popular stocks."""

    initial_tickers = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOG']

    added_count = 0

    for ticker_symbol in initial_tickers:
        # 1. Check if the ticker is already in the database
        # Using SQLAlchemy 2.0 syntax
        existing_ticker = db.session.scalar(
            db.select(TrackedTicker).where(TrackedTicker.ticker == ticker_symbol)
        )

        # 2. Only add it if it doesn't exist
        if not existing_ticker:
            new_ticker = TrackedTicker(ticker=ticker_symbol, is_active=True)
            db.session.add(new_ticker)
            added_count += 1
            print(f"Queued {ticker_symbol} for insertion.")

    # 3. Commit the batch
    if added_count > 0:
        db.session.commit()
        print(f"Success! Seeded {added_count} new tickers into the database.")
    else:
        print("All tickers are already present in the database. No changes made.")

# NOTE: If you put this in a separate file, make sure to register it in your app factory:
# app.cli.add_command(seed_tickers)