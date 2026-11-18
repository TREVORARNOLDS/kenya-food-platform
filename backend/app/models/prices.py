from app.extensions import db


class PriceObservation(db.Model):
    __tablename__ = "price_observations"
    __table_args__ = (
        # Prevents duplicate rows when an ingestion is re-run
        db.UniqueConstraint(
            "market_id", "commodity_id", "observed_on", "unit", "price_type",
            "data_source_id", name="uq_price_observation",
        ),
        db.Index("ix_price_market_commodity_date", "market_id", "commodity_id", "observed_on"),
    )

    id = db.Column(db.Integer, primary_key=True)
    market_id = db.Column(db.Integer, db.ForeignKey("markets.id"), nullable=False)
    commodity_id = db.Column(db.Integer, db.ForeignKey("commodities.id"), nullable=False)
    data_source_id = db.Column(db.Integer, db.ForeignKey("data_sources.id"), nullable=False)
    ingestion_run_id = db.Column(db.Integer, db.ForeignKey("ingestion_runs.id"))
    observed_on = db.Column(db.Date, nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    price_type = db.Column(db.String(20), nullable=False, default="retail")
    currency = db.Column(db.String(10), default="KES")
    price = db.Column(db.Numeric(14, 4), nullable=False)
    price_usd = db.Column(db.Numeric(14, 4))

    market = db.relationship("Market", back_populates="prices")
    commodity = db.relationship("Commodity", back_populates="prices")
