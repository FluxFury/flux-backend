from datetime import datetime, timezone
import uuid
def utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def model_to_dict(row):
    """Convert SQLAlchemy model to JSON-serializable dictionary."""
    row_dict = {}
    for c in row.__table__.columns:
        value = getattr(row, c.name)
        # Convert UUID to string
        if isinstance(value, uuid.UUID):
            row_dict[c.name] = str(value)
        # Convert datetime to ISO format string
        elif isinstance(value, datetime):
            row_dict[c.name] = value.isoformat()
        else:
            row_dict[c.name] = value
    return row_dict