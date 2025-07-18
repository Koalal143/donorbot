from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import ManagedTextInput, TextInput
from aiogram_dialog.widgets.kbd import Button, Group, Row, Select
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.dialogs.states import OrganizerSG, ProfileSG, RegistrationSG
from src.dialogs.validators import normalize_phone, validate_full_name, validate_phone, validate_student_group
from src.enums.donor_type import DonorType
from src.models.donor import Donor
from src.repositories.donor import DonorRepository


@inject
async def phone_input_handler(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
    donor_repository: FromDishka[DonorRepository],
) -> None:
    if data.strip() == "admin":
        await dialog_manager.start(OrganizerSG.organizer_selection)
        return

    validation_result = validate_phone(data)
    if not validation_result.is_valid:
        dialog_manager.dialog_data["phone_retry"] = True
        await message.answer(validation_result.error_message)
        return

    phone = normalize_phone(data)
    dialog_manager.dialog_data["phone"] = phone
    dialog_manager.dialog_data.pop("phone_retry", None)

    existing_donor = await donor_repository.get_by_phone_number(phone)
    if existing_donor:
        dialog_manager.dialog_data["existing_user"] = {"full_name": existing_donor.full_name}
        await dialog_manager.switch_to(RegistrationSG.name_confirmation)
    else:
        await dialog_manager.switch_to(RegistrationSG.name_input)


async def name_confirmation_yes(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    phone = dialog_manager.dialog_data.get("phone")

    await callback.answer("✅ Регистрация завершена! Добро пожаловать в систему.")
    await dialog_manager.start(ProfileSG.profile_view, data={"phone": phone, "just_registered": False})


async def name_confirmation_no(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data.pop("phone", None)
    dialog_manager.dialog_data.pop("existing_user", None)
    dialog_manager.dialog_data["phone_retry"] = True
    await dialog_manager.switch_to(RegistrationSG.phone_input)


async def name_input_handler(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
) -> None:
    validation_result = validate_full_name(data)
    if not validation_result.is_valid:
        await message.answer(validation_result.error_message)
        return

    name_parts = data.strip().split()
    if len(name_parts) == 2:
        dialog_manager.dialog_data["temp_name"] = data
        await dialog_manager.switch_to(RegistrationSG.patronymic_confirmation)
    else:
        dialog_manager.dialog_data["full_name"] = data
        await dialog_manager.switch_to(RegistrationSG.donor_type_selection)


async def patronymic_yes(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(RegistrationSG.name_input)


async def patronymic_no(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    full_name = dialog_manager.dialog_data.get("temp_name", "")
    dialog_manager.dialog_data["full_name"] = full_name
    dialog_manager.dialog_data.pop("temp_name", None)
    await dialog_manager.switch_to(RegistrationSG.donor_type_selection)


async def donor_type_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["donor_type"] = item_id

    if item_id == DonorType.STUDENT:
        await dialog_manager.switch_to(RegistrationSG.student_group_input)
    else:
        await dialog_manager.switch_to(RegistrationSG.privacy_consent)


async def student_group_input_handler(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
) -> None:
    validation_result = validate_student_group(data)
    if not validation_result.is_valid:
        await message.answer(validation_result.error_message)
        return

    dialog_manager.dialog_data["student_group"] = data.strip().upper()
    await dialog_manager.switch_to(RegistrationSG.privacy_consent)


@inject
async def privacy_consent_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    donor_repository: FromDishka[DonorRepository],
) -> None:
    phone = dialog_manager.dialog_data.get("phone")
    full_name = dialog_manager.dialog_data.get("full_name")
    donor_type_str = dialog_manager.dialog_data.get("donor_type")
    student_group = dialog_manager.dialog_data.get("student_group")

    if not phone or not full_name or not donor_type_str:
        if callback.message:
            await callback.message.answer("Ошибка: не все данные заполнены. Начните регистрацию заново.")
        return

    donor_type = DonorType(donor_type_str)

    if donor_type == DonorType.STUDENT and not student_group:
        if callback.message:
            await callback.message.answer(
                "Ошибка: для студентов обязательно указание группы. Начните регистрацию заново."
            )
        return

    existing_donor = await donor_repository.get_by_phone_number(phone)
    if not existing_donor:
        new_donor = Donor(
            full_name=full_name,
            phone_number=phone,
            donor_type=donor_type,
            student_group=student_group if donor_type == DonorType.STUDENT else None,
        )
        await donor_repository.create(new_donor)

    await callback.answer("✅ Регистрация завершена! Добро пожаловать в систему.")
    await dialog_manager.start(ProfileSG.profile_view, data={"phone": phone, "just_registered": False})


async def get_name_confirmation_data(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    existing_user = dialog_manager.dialog_data.get("existing_user", {})
    return {"full_name": existing_user.get("full_name", "")}


async def get_phone_input_data(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    is_retry = dialog_manager.dialog_data.get("phone_retry", False)
    if is_retry:
        return {"welcome_text": "Введите корректный номер телефона:"}
    return {"welcome_text": "Добро пожаловать! Введите ваш номер телефона:"}


async def get_donor_types(**kwargs: Any) -> dict[str, Any]:
    return {
        "donor_types": [
            (DonorType.STUDENT, "Студент"),
            (DonorType.EMPLOYEE, "Сотрудник"),
            (DonorType.EXTERNAL, "Внешний донор"),
        ]
    }


registration_dialog = Dialog(
    Window(
        Format("{welcome_text}"),
        TextInput(
            id="phone_input",
            on_success=phone_input_handler,
        ),
        state=RegistrationSG.phone_input,
        getter=get_phone_input_data,
    ),
    Window(
        Format("Ваша фамилия - {full_name}?"),
        Group(
            Row(
                Button(
                    Const("Да"),
                    id="name_yes",
                    on_click=name_confirmation_yes,
                ),
                Button(
                    Const("Нет"),
                    id="name_no",
                    on_click=name_confirmation_no,
                ),
            ),
        ),
        state=RegistrationSG.name_confirmation,
        getter=get_name_confirmation_data,
    ),
    Window(
        Const("💳 Введите ваши фамилию, имя и отчество (при наличии):"),
        TextInput(
            id="name_input",
            on_success=name_input_handler,
        ),
        state=RegistrationSG.name_input,
    ),
    Window(
        Const("Подтвердите, нет ли у вас отчества?"),
        Group(
            Row(
                Button(
                    Const("Да, отчества нет"),
                    id="patronymic_no",
                    on_click=patronymic_no,
                ),
                Button(
                    Const("Нет, есть отчество"),
                    id="patronymic_yes",
                    on_click=patronymic_yes,
                ),
            ),
        ),
        state=RegistrationSG.patronymic_confirmation,
    ),
    Window(
        Const("Выберите ваш тип:"),
        Select(
            Format("{item[1]}"),
            items="donor_types",
            item_id_getter=lambda item: item[0],
            id="donor_type_select",
            on_click=donor_type_selected,
        ),
        state=RegistrationSG.donor_type_selection,
        getter=get_donor_types,
    ),
    Window(
        Const("🎓 Введите номер вашей группы:"),
        TextInput(
            id="student_group_input",
            on_success=student_group_input_handler,
        ),
        state=RegistrationSG.student_group_input,
    ),
    Window(
        Const("Даете ли вы согласие на обработку персональных данных?"),
        Button(
            Const("Даю согласие"),
            id="privacy_consent",
            on_click=privacy_consent_handler,
        ),
        state=RegistrationSG.privacy_consent,
    ),
)
