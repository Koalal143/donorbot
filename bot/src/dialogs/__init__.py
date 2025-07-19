from aiogram import Router

from src.dialogs.donor_day_menu import donor_day_menu_dialog
from src.dialogs.donor_day_registration import donor_day_registration_dialog
from src.dialogs.organizer import organizer_dialog
from src.dialogs.profile import profile_dialog
from src.dialogs.registration import registration_dialog

dialogs_router = Router()
dialogs_router.include_router(registration_dialog)
dialogs_router.include_router(organizer_dialog)
dialogs_router.include_router(profile_dialog)
dialogs_router.include_router(donor_day_registration_dialog)
dialogs_router.include_router(donor_day_menu_dialog)
