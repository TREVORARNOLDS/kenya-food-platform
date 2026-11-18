from flask.views import MethodView
from flask_smorest import Blueprint

from app.schemas.markets import MarketQuerySchema, PaginatedMarketSchema
from app.services import market_service

blp = Blueprint("markets", __name__, url_prefix="/api/v1/markets", description="Markets")


@blp.route("/")
class MarketList(MethodView):
    @blp.arguments(MarketQuerySchema, location="query")
    @blp.response(200, PaginatedMarketSchema)
    def get(self, args):
        """List markets, optionally filtered by county or name."""
        return market_service.list_markets(**args)
