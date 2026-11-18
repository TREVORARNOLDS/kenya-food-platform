from marshmallow import Schema, fields

from .common import PaginationQuerySchema, paginated


class CommoditySchema(Schema):
    id = fields.Int()
    name = fields.Str()
    category = fields.Str(allow_none=True)


class CommodityQuerySchema(PaginationQuerySchema):
    category = fields.Str()
    search = fields.Str()


PaginatedCommoditySchema = paginated(CommoditySchema)
