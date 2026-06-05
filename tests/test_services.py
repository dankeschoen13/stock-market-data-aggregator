from mock_data import get_mock_aapl_dataframe
from app.services import MktDataSvc
from app.models import Stock
from app.extensions import db

class TestMktDataSvc:

    def test_load_data(self, app):

        # Arrange
        df = get_mock_aapl_dataframe(single_row=True)

        # Service Execution
        MktDataSvc.load_data(df)

        # Assertions
        saved_data = db.session.scalars(
            db.select(Stock).where(Stock.ticker == "AAPL")
        ).all()
        assert len(saved_data) == 1
        assert saved_data is not None

        first_record = saved_data[0]
        assert first_record.ticker == "AAPL"
        assert first_record.close_price == df["close_price"].iloc[0]
        assert first_record.rsi_14 == df["rsi_14"].iloc[0]


    