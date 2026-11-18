from flask.views import MethodView
from flask_smorest import Blueprint

from app.schemas.prices import PaginatedPriceSchema, PriceQuerySchema
from app.services import price_service

blp = Blueprint("prices", __name__, url_prefix="/api/v1/prices", description="Price observations")


@blp.route("/")
class PriceList(MethodView):
    @blp.arguments(PriceQuerySchema, location="query")
    @blp.response(200, PaginatedPriceSchema)
    def get(self, args):
        """List price observations with filtering, date range, sorting and pagination."""
        return price_service.list_prices(**args)
