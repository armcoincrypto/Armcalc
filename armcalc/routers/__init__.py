"""Router modules for Armcalc bot."""

from aiogram import Router

from .start import router as start_router
from .help import router as help_router
from .calc import router as calc_router
from .inline import router as inline_router
from .tools_convert import router as convert_router
from .debug import router as debug_router


def get_all_routers() -> list[Router]:
    """Get all routers for registration.

    ORDER MATTERS: Command routers (convert, debug) must come BEFORE
    calc_router which has a catch-all text handler.
    """
    return [
        start_router,
        help_router,
        convert_router,  # Commands: /convert, /price, /pairs, /rates
        debug_router,    # Commands: /debug
        calc_router,     # Commands + catch-all text handler (MUST be last)
        inline_router,   # Inline queries
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
