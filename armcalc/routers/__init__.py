"""Router modules for Armcalc bot."""

from aiogram import Router

from .start import router as start_router
from .help import router as help_router
from .calc import router as calc_router
from .inline import router as inline_router
from .tools_convert import router as convert_router
from .debug import router as debug_router


def get_all_routers() -> list[Router]:
    """Get all routers for registration."""
    return [
        start_router,
        help_router,
        calc_router,
        inline_router,
        convert_router,
        debug_router,
    ]


__all__ = [
    "get_all_routers",
    "start_router",
    "help_router",
    "calc_router",
    "inline_router",
    "convert_router",
    "debug_router",
]
