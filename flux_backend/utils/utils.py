from fastapi import Query
from sqlalchemy.dialects.postgresql import array
from sqlalchemy import desc, asc, true


def common_pagination_params(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
):
    # helper для dependency injection
    return {"page": page, "page_size": page_size}


from sqlalchemy.dialects.postgresql import array


def has_any(jsonb_col, values: list[str]):
    if not values:  # пустой список → без фильтра
        return true()
    return jsonb_col.op("?|")(array(values))


ORDER_MAP = {
    "timestamp": "news_creation_time",
    "title": "header",
}


def order_clause(model, order: str, default: str = "-timestamp"):
    order = order or default
    raw_field = order.lstrip("-")
    field = ORDER_MAP.get(raw_field, raw_field)
    col = getattr(model, field)
    return desc(col) if order.startswith("-") else asc(col)
