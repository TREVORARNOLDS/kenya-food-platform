from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from .common import PaginationQuerySchema, paginated


class PriceSchema(Schema):
    id = fields.Int()
    observed_on = fields.Date()
    market_id = fields.Int()
    market_name = fields.Str(attribute="market.name")
    county_name = fields.Str(attribute="market.county.name")
    commodity_id = fields.Int()
    commodity_name = fields.Str(attribute="commodity.name")
    unit = fields.Str()
    price_type = fields.Str()
    currency = fields.Str()
    price = fields.Float()
    price_usd = fields.Float(allow_none=True)


class PriceQuerySchema(PaginationQuerySchema):
    market_id = fields.Int()
    commodity_id = fields.Int()
    county_id = fields.Int()
    price_type = fields.Str(validate=validate.OneOf(["retail", "wholesale"]))
    date_from = fields.Date()
    date_to = fields.Date()
    sort = fields.Str(load_default="observed_on", validate=validate.OneOf(["observed_on", "price"]))
    order = fields.Str(load_default="desc", validate=validate.OneOf(["asc", "desc"]))

    @validates_schema
    def check_date_range(self, data, **kwargs):
        start, end = data.get("date_from"), data.get("date_to")
        if start and end and start > end:
            raise ValidationError("date_from must not be after date_to", "date_from")


PaginatedPriceSchema = paginated(PriceSchema)
