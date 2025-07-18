from aiogram import Router

from src.dialogs.organizer import organizer_dialog
from src.dialogs.profile import profile_dialog
from src.dialogs.registration import registration_dialog

dialogs_router = Router()
dialogs_router.include_router(registration_dialog)
dialogs_router.include_router(organizer_dialog)
dialogs_router.include_router(profile_dialog)
