import uuid
from fastapi import HTTPException


def validate_uuid(value: str, field_name: str = "id") -> str:
    """Checks whether the string is a valid UUID. It throws 422 if not."""
    try:
        uuid.UUID(value)
        return value
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid {field_name} format — must be a valid UUID",
        )