from geoalchemy2 import Geometry

from app.extensions import db


class Market(db.Model):
    __tablename__ = "markets"
    __table_args__ = (
        db.UniqueConstraint("name", "county_id", name="uq_market_name_county"),
        db.Index("ix_markets_location", "location", postgresql_using="gist"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    county_id = db.Column(db.Integer, db.ForeignKey("counties.id"))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    location = db.Column(Geometry("POINT", srid=4326, spatial_index=False))

    county = db.relationship("County", back_populates="markets")
    prices = db.relationship("PriceObservation", back_populates="market")
