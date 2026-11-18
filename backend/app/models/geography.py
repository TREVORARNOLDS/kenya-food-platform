from geoalchemy2 import Geometry

from app.extensions import db


class County(db.Model):
    __tablename__ = "counties"
    __table_args__ = (db.Index("ix_counties_geom", "geom", postgresql_using="gist"),)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    code = db.Column(db.String(10), unique=True)
    geom = db.Column(Geometry("MULTIPOLYGON", srid=4326, spatial_index=False))

    markets = db.relationship("Market", back_populates="county")
