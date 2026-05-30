from flask.cli import with_appcontext
from app.services import TickerSvc
from app.constants import TickerSets
import click

@click.command(name='get-stock-data')
@with_appcontext
def get_stock_data_command():
    pass


@click.command(name='seed-tickers')
@with_appcontext
def seed_tickers_command():
    """
    Seeds the TrackedTicker table with an initial batch of popular stocks.
    """

    initial_tickers = TickerSets.SET_B
    added_count = 0

    # 1. Loop through the list of initial tickers and add them to session
    for ticker_symbol in initial_tickers:
        was_added = TickerSvc.add_new_ticker(ticker_symbol, auto_commit=False)

        if was_added:
            added_count += 1
            click.echo(f"Queued {ticker_symbol} for insertion.")

    # 2. Commit session tickers to the database if there's any
    if added_count > 0:
        success, error_msg = TickerSvc.save_changes()

        if success:
            click.echo(f"Success! Seeded {added_count} new tickers into the database.")
        else:
            click.echo(f"Database error during commit: {error_msg}",
                       err=True)
    else:
        click.echo("All tickers are already present in the database. No changes made.")
