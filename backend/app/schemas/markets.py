from marshmallow import Schema, fields

from .common import PaginationQuerySchema, paginated


class MarketSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    county_id = fields.Int(allow_none=True)
    county_name = fields.Str(attribute="county.name")
    latitude = fields.Float(allow_none=True)
    longitude = fields.Float(allow_none=True)


class MarketQuerySchema(PaginationQuerySchema):
    county_id = fields.Int()
    search = fields.Str()


PaginatedMarketSchema = paginated(MarketSchema)
