from app.extensions import db


def paginate_select(stmt, page: int, page_size: int) -> dict:
    result = db.paginate(stmt, page=page, per_page=page_size, max_per_page=200, error_out=False)
    return {
        "items": result.items,
        "page": result.page,
        "page_size": result.per_page,
        "total": result.total,
        "pages": result.pages,
    }
