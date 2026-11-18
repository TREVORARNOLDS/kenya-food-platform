from flask.views import MethodView
from flask_smorest import Blueprint

from app.schemas.analytics import TrendQuerySchema, TrendSchema, VolatilitySchema
from app.schemas.prices import PaginatedPriceSchema, PriceQuerySchema
from app.services import analytics_service, price_service

blp = Blueprint("prices", __name__, url_prefix="/api/v1/prices", description="Price observations")


@blp.route("/")
class PriceList(MethodView):
    @blp.arguments(PriceQuerySchema, location="query")
    @blp.response(200, PaginatedPriceSchema)
    def get(self, args):
        """List price observations with filtering, date range, sorting and pagination."""
        return price_service.list_prices(**args)


@blp.route("/trends/")
class PriceTrends(MethodView):
    @blp.arguments(TrendQuerySchema, location="query")
    @blp.response(200, TrendSchema)
    def get(self, args):
        """Monthly average, min and max price for one commodity in one unit."""
        return analytics_service.monthly_trend(**args)


@blp.route("/volatility/")
class PriceVolatility(MethodView):
    @blp.arguments(TrendQuerySchema, location="query")
    @blp.response(200, VolatilitySchema)
    def get(self, args):
        """Volatility measures for one commodity's monthly average price."""
        return analytics_service.price_volatility(**args)
