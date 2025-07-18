from aiogram import Router

from src.dialogs import dialogs_router

from . import start

main_router = Router()
main_router.include_router(start.router)
main_router.include_router(dialogs_router)
