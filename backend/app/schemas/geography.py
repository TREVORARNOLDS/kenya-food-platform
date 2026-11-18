from marshmallow import Schema, fields

from .common import paginated


class CountySchema(Schema):
    id = fields.Int()
    name = fields.Str()
    code = fields.Str(allow_none=True)


PaginatedCountySchema = paginated(CountySchema)
