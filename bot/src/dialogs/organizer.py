from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const

from .states import OrganizerSG

organizer_dialog = Dialog(
    Window(
        Const("Добро пожаловать в панель организатора!"),
        state=OrganizerSG.organizer_flow,
    ),
)
