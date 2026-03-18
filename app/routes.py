from __future__ import annotations

from flask import Blueprint

from app.page_routes import register_routes
from app.route_utils import _to_verdict

bp = Blueprint("pages", __name__)
register_routes(bp)

__all__ = ["bp", "_to_verdict"]
