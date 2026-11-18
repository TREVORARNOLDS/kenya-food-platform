from flask.views import MethodView
from flask_smorest import Blueprint

from app.schemas.commodities import CommodityQuerySchema, PaginatedCommoditySchema
from app.services import price_service

blp = Blueprint(
    "commodities", __name__, url_prefix="/api/v1/commodities", description="Commodities"
)


@blp.route("/")
class CommodityList(MethodView):
    @blp.arguments(CommodityQuerySchema, location="query")
    @blp.response(200, PaginatedCommoditySchema)
    def get(self, args):
        """List commodities, optionally filtered by category or name."""
        return price_service.list_commodities(**args)
