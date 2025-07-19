from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram_dialog import DialogManager, StartMode

from src.dialogs.states import RegistrationSG

router = Router(name="start")


@router.message(CommandStart())
async def start_handler(message: types.Message, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(RegistrationSG.phone_input, mode=StartMode.RESET_STACK)


@router.message(Command("reset"))
async def reset_state_handler(message: types.Message, dialog_manager: DialogManager) -> None:
    await message.answer("Состояние сброшено. Начинаем заново.")
    await dialog_manager.start(RegistrationSG.phone_input, mode=StartMode.RESET_STACK)
