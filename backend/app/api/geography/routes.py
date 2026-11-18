from flask.views import MethodView
from flask_smorest import Blueprint

from app.schemas.common import PaginationQuerySchema
from app.schemas.geography import PaginatedCountySchema
from app.services import market_service

blp = Blueprint("counties", __name__, url_prefix="/api/v1/counties", description="Counties")


@blp.route("/")
class CountyList(MethodView):
    @blp.arguments(PaginationQuerySchema, location="query")
    @blp.response(200, PaginatedCountySchema)
    def get(self, args):
        """List counties."""
        return market_service.list_counties(**args)
