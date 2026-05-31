from app.services import MktDataSvc, TickerSvc, fetch_latest_stock_data
from app.constants import TickerSets
from flask.cli import with_appcontext
from flask import current_app
import pandas as pd
import click


@click.command(name='get-stock-data')
@with_appcontext
def get_stock_data_command():
    """
    Fetches daily data for all active tickers and loads it into the database.
    """

    # 1.A | DATA PREP: Get the api key.
    api_key = current_app.config.get('FMP_KEY')
    if not api_key:
        click.secho(
            "Critical Error: FMP_KEY is missing from app configuration.",
            fg="red", err=True
        )
        return

    # 1.B | DATA PREP: Get the list of tracked tickers.
    tickers = TickerSvc.get_active_tickers()
    if not tickers:
        click.echo("No active tickers found in the database to update.")
        return


    # 2. | MAIN PROCESS: Loop through the ticker list, fetch data and save to db.
    click.echo(f"Starting market data update for {len(tickers)} tickers...")

    for symbol in tickers:
        click.echo(f"Fetching data for {symbol.ticker}...")

        try:
            # a. Extract
            stock_data = fetch_latest_stock_data(symbol.ticker, api_key)

            # b. Validate
            if isinstance(stock_data, pd.DataFrame):

            # c. Load
                MktDataSvc.load_data(stock_data)
                click.secho(
                    f"  ✔ Success! {symbol.ticker} data updated.",
                    fg="green"
                )
            else:
                click.secho(
                    f"  ✖ Failed to extract valid data for {symbol.ticker}.",
                    fg="yellow"
                )

        except Exception as e:
            # d. Catch unexpected extraction network errors or database SQLAlchemyErrors
            click.secho(
                f"  ! Critical error processing {symbol.ticker}: {e}",
                fg="red", err=True
            )

    click.echo("Market data update complete!")


@click.command(name='seed-tickers')
@with_appcontext
def seed_tickers_command():
    """
    Seeds the TrackedTicker table with an initial batch of popular stocks.
    """

    initial_tickers = TickerSets.SET_C
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
            click.echo(
                f"Success! Seeded {added_count} new tickers into the database."
            )
        else:
            click.echo(
                f"Database error during commit: {error_msg}",
                err=True
            )
    else:
        click.echo(
            "All tickers are already present in the database. No changes made."
        )

def register_cli_commands(app):
    """
    Registers all background CLI tasks to the Flask app.
    """
    app.cli.add_command(get_stock_data_command)
    app.cli.add_command(seed_tickers_command)