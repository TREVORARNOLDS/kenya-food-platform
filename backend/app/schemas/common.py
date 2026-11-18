from marshmallow import Schema, fields, validate


class PaginationQuerySchema(Schema):
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    page_size = fields.Int(load_default=50, validate=validate.Range(min=1, max=200))


def paginated(item_schema):
    """Build a response envelope: {items, page, page_size, total, pages}."""
    return type(
        f"Paginated{item_schema.__name__}",
        (Schema,),
        {
            "items": fields.List(fields.Nested(item_schema)),
            "page": fields.Int(),
            "page_size": fields.Int(),
            "total": fields.Int(),
            "pages": fields.Int(),
        },
    )
