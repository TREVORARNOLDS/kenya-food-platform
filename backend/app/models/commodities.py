from app.extensions import db


class Commodity(db.Model):
    __tablename__ = "commodities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    category = db.Column(db.String(100))

    prices = db.relationship("PriceObservation", back_populates="commodity")
