"""CNKI Space literature metadata search (no full-text download)."""

from .client import build_listresult_payload
from .models import Record, SearchResponse
from .parse import parse_list_html
from .service import get_record, search_cnki

__version__ = "0.1.0"
__all__ = [
    "Record",
    "SearchResponse",
    "get_record",
    "build_listresult_payload",
    "parse_list_html",
    "search_cnki",
]
