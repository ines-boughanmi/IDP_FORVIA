from fastapi import Request
from typing import Any
from ..services.data_loader import DataLoaderService


def get_data_loader(request: Request) -> DataLoaderService:
    """Dependency to retrieve the DataLoaderService from app state."""
    return request.app.state.data_loader
