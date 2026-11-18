from marshmallow import Schema, ValidationError, fields, validate, validates_schema


class TrendQuerySchema(Schema):
    commodity_id = fields.Int(required=True)
    unit = fields.Str()
    price_type = fields.Str(load_default="retail", validate=validate.OneOf(["retail", "wholesale"]))
    county_id = fields.Int()
    market_id = fields.Int()
    date_from = fields.Date()
    date_to = fields.Date()

    @validates_schema
    def check_date_range(self, data, **kwargs):
        start, end = data.get("date_from"), data.get("date_to")
        if start and end and start > end:
            raise ValidationError("date_from must not be after date_to", "date_from")


class TrendPointSchema(Schema):
    month = fields.Date()
    avg_price = fields.Float()
    min_price = fields.Float()
    max_price = fields.Float()
    observations = fields.Int()


class TrendSchema(Schema):
    commodity_id = fields.Int()
    unit = fields.Str(allow_none=True)
    price_type = fields.Str()
    available_units = fields.List(fields.Str())
    points = fields.List(fields.Nested(TrendPointSchema))


class VolatilityStatsSchema(Schema):
    months = fields.Int()
    mean_price = fields.Float(allow_none=True)
    coefficient_of_variation_pct = fields.Float(allow_none=True)
    mean_abs_monthly_change_pct = fields.Float(allow_none=True)
    monthly_change_std_pct = fields.Float(allow_none=True)


class VolatilitySchema(Schema):
    commodity_id = fields.Int()
    unit = fields.Str(allow_none=True)
    price_type = fields.Str()
    stats = fields.Nested(VolatilityStatsSchema)


class CompareQuerySchema(Schema):
    commodity_id = fields.Int(required=True)
    unit = fields.Str()
    price_type = fields.Str(load_default="retail", validate=validate.OneOf(["retail", "wholesale"]))
    group_by = fields.Str(load_default="county", validate=validate.OneOf(["county", "market"]))
    date_from = fields.Date()
    date_to = fields.Date()
    limit = fields.Int(load_default=50, validate=validate.Range(min=1, max=200))

    @validates_schema
    def check_date_range(self, data, **kwargs):
        start, end = data.get("date_from"), data.get("date_to")
        if start and end and start > end:
            raise ValidationError("date_from must not be after date_to", "date_from")


class CompareItemSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    county_name = fields.Str(allow_none=True)
    avg_price = fields.Float()
    min_price = fields.Float()
    max_price = fields.Float()
    observations = fields.Int()


class CompareSchema(Schema):
    commodity_id = fields.Int()
    unit = fields.Str(allow_none=True)
    price_type = fields.Str()
    group_by = fields.Str()
    available_units = fields.List(fields.Str())
    date_from = fields.Date(allow_none=True)
    date_to = fields.Date(allow_none=True)
    overall_avg_price = fields.Float(allow_none=True)
    items = fields.List(fields.Nested(CompareItemSchema))
