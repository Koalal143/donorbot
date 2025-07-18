from typing import Any

from aiogram import F
from aiogram.types import CallbackQuery, Contact, KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput, TextInput
from aiogram_dialog.widgets.kbd import Button, Group, Row, Select
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.dialogs.states import OrganizerSG, ProfileSG, RegistrationSG
from src.dialogs.validators import normalize_phone, validate_full_name, validate_phone, validate_student_group
from src.enums.donor_type import DonorType
from src.models.donor import Donor
from src.repositories.donor import DonorRepository
from src.services.notification_service import NotificationService


async def phone_input_method_selected(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    button_id = button.widget_id
    if button_id == "share_contact":
        dialog_manager.dialog_data["input_method"] = "contact"
        await dialog_manager.switch_to(RegistrationSG.phone_input)
    elif button_id == "manual_input":
        dialog_manager.dialog_data["input_method"] = "manual"
        await dialog_manager.switch_to(RegistrationSG.phone_input)


@inject
async def contact_shared(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
    donor_repository: FromDishka[DonorRepository],
) -> None:
    if not message.contact:
        await message.answer("Пожалуйста, поделитесь контактом.")
        return

    contact: Contact = message.contact
    phone = contact.phone_number

    if not phone:
        await message.answer("Не удалось получить номер телефона из контакта.")
        return

    if phone.strip() == "admin":
        await dialog_manager.start(OrganizerSG.organizer_selection)
        return

    validation_result = validate_phone(phone)
    if not validation_result.is_valid:
        dialog_manager.dialog_data["phone_retry"] = True
        await message.answer(validation_result.error_message)
        return

    phone = normalize_phone(phone)
    dialog_manager.dialog_data["phone"] = phone
    dialog_manager.dialog_data.pop("phone_retry", None)

    await message.answer("✅ Контакт получен!", reply_markup=ReplyKeyboardRemove())

    existing_donor = await donor_repository.get_by_phone_number(phone)
    if existing_donor:
        current_telegram_id = message.from_user.id
        if existing_donor.telegram_id and existing_donor.telegram_id != current_telegram_id:
            dialog_manager.dialog_data["existing_user"] = {
                "full_name": existing_donor.full_name,
                "donor_id": existing_donor.id,
                "old_telegram_id": existing_donor.telegram_id,
                "new_telegram_id": current_telegram_id,
            }
            await dialog_manager.switch_to(RegistrationSG.telegram_id_conflict)
        else:
            dialog_manager.dialog_data["existing_user"] = {"full_name": existing_donor.full_name}
            await dialog_manager.switch_to(RegistrationSG.name_confirmation)
    else:
        await dialog_manager.switch_to(RegistrationSG.name_input)


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

    await message.answer("✅ Номер телефона получен!", reply_markup=ReplyKeyboardRemove())

    existing_donor = await donor_repository.get_by_phone_number(phone)
    if existing_donor:
        current_telegram_id = message.from_user.id
        if existing_donor.telegram_id and existing_donor.telegram_id != current_telegram_id:
            dialog_manager.dialog_data["existing_user"] = {
                "full_name": existing_donor.full_name,
                "donor_id": existing_donor.id,
                "old_telegram_id": existing_donor.telegram_id,
                "new_telegram_id": current_telegram_id,
            }
            await dialog_manager.switch_to(RegistrationSG.telegram_id_conflict)
        else:
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
    await dialog_manager.start(ProfileSG.profile_view, data={"phone": phone})


async def name_confirmation_no(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data.pop("phone", None)
    dialog_manager.dialog_data.pop("existing_user", None)
    dialog_manager.dialog_data["phone_retry"] = True
    await dialog_manager.switch_to(RegistrationSG.phone_input_method)


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
        await dialog_manager.switch_to(RegistrationSG.bone_marrow_donor_selection)


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
    await dialog_manager.switch_to(RegistrationSG.bone_marrow_donor_selection)


async def bone_marrow_donor_yes(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data["is_bone_marrow_donor"] = True
    await dialog_manager.switch_to(RegistrationSG.privacy_consent)


async def bone_marrow_donor_no(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data["is_bone_marrow_donor"] = False
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
    is_bone_marrow_donor = dialog_manager.dialog_data.get("is_bone_marrow_donor", False)

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
        telegram_id = callback.from_user.id if callback.from_user else None

        new_donor = Donor(
            full_name=full_name,
            phone_number=phone,
            donor_type=donor_type,
            student_group=student_group if donor_type == DonorType.STUDENT else None,
            telegram_id=telegram_id,
            is_bone_marrow_donor=is_bone_marrow_donor,
        )
        await donor_repository.create(new_donor)
    elif not existing_donor.telegram_id:
        telegram_id = callback.from_user.id if callback.from_user else None
        if telegram_id:
            await donor_repository.update_telegram_id(existing_donor.id, telegram_id)

    await callback.answer("✅ Регистрация завершена! Добро пожаловать в систему.")
    await dialog_manager.start(ProfileSG.profile_view, data={"phone": phone})


async def get_name_confirmation_data(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    existing_user = dialog_manager.dialog_data.get("existing_user", {})
    return {"full_name": existing_user.get("full_name", "")}


def create_contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поделиться контактом", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


async def get_phone_input_data(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    is_retry = dialog_manager.dialog_data.get("phone_retry", False)
    if is_retry:
        return {"welcome_text": "Пожалуйста, введите корректный номер телефона:"}
    return {"welcome_text": "Введите ваш номер телефона:"}


async def get_donor_types(**kwargs: Any) -> dict[str, Any]:
    return {
        "donor_types": [
            (DonorType.STUDENT, "Студент"),
            (DonorType.EMPLOYEE, "Сотрудник"),
            (DonorType.EXTERNAL, "Внешний донор"),
        ]
    }


async def get_telegram_id_conflict_data(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    existing_user = dialog_manager.dialog_data.get("existing_user", {})
    return {
        "full_name": existing_user.get("full_name", ""),
        "old_telegram_id": existing_user.get("old_telegram_id", ""),
        "new_telegram_id": existing_user.get("new_telegram_id", ""),
    }


@inject
async def confirm_telegram_id_change(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    donor_repository: FromDishka[DonorRepository],
) -> None:
    existing_user = dialog_manager.dialog_data.get("existing_user", {})
    donor_id = existing_user.get("donor_id")
    new_telegram_id = existing_user.get("new_telegram_id")
    old_telegram_id = existing_user.get("old_telegram_id")
    full_name = existing_user.get("full_name")

    if not donor_id or not new_telegram_id:
        await callback.answer("Ошибка: не удалось получить данные донора")
        return
    bot = dialog_manager.middleware_data.get("bot")
    if bot and old_telegram_id:
        notification_service = NotificationService(bot)
        await notification_service.send_account_change_notification(old_telegram_id, full_name, new_telegram_id)

    await callback.answer("✅ Запрос на смену аккаунта отправлен! Ожидайте подтверждения.")
    await dialog_manager.switch_to(RegistrationSG.phone_input_method)


async def cancel_telegram_id_change(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(RegistrationSG.phone_input_method)


async def show_contact_keyboard(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    if callback.message:
        await callback.message.answer(
            "Нажмите кнопку ниже, чтобы поделиться контактом:", reply_markup=create_contact_keyboard()
        )


registration_dialog = Dialog(
    Window(
        Const("Добро пожаловать! Выберите способ ввода номера телефона:"),
        Group(
            Row(
                Button(
                    Const("📱 Поделиться контактом"),
                    id="share_contact",
                    on_click=phone_input_method_selected,
                ),
            ),
            Row(
                Button(
                    Const("⌨️ Ввести вручную"),
                    id="manual_input",
                    on_click=phone_input_method_selected,
                ),
            ),
        ),
        state=RegistrationSG.phone_input_method,
    ),
    Window(
        Format("📱 Поделитесь своим контактом или введите номер вручную:\n\n{welcome_text}"),
        Group(
            Row(
                Button(
                    Const("📱 Показать клавиатуру для контакта"),
                    id="show_contact_keyboard",
                    on_click=show_contact_keyboard,
                ),
            ),
        ),
        MessageInput(contact_shared, filter=F.contact),
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
        Const("🩸 Состоите ли вы в регистре доноров костного мозга (ДКМ)?"),
        Group(
            Row(
                Button(
                    Const("Да"),
                    id="bone_marrow_yes",
                    on_click=bone_marrow_donor_yes,
                ),
                Button(
                    Const("Нет"),
                    id="bone_marrow_no",
                    on_click=bone_marrow_donor_no,
                ),
            ),
        ),
        state=RegistrationSG.bone_marrow_donor_selection,
    ),
    Window(
        Const("Даете ли вы согласие на обработку персональных данных? (https://drive.google.com/file/d/1UE8YN_i7ani9KgL8MMJz-MRrSn1SDaIv/view?usp=drive_link)"),
        Button(
            Const("Даю согласие"),
            id="privacy_consent",
            on_click=privacy_consent_handler,
        ),
        state=RegistrationSG.privacy_consent,
    ),
    Window(
        Format(
            "⚠️ Обнаружен другой аккаунт\n\n"
            "Пользователь с фамилиейё {full_name} уже зарегистрирован в системе.\n\n"
            "Старый Telegram ID: `{old_telegram_id}`\n"
            "Новый Telegram ID: `{new_telegram_id}`\n\n"
            "Хотите ли вы обновить привязку к новому аккаунту?"
        ),
        Group(
            Row(
                Button(
                    Const("✅ Да, обновить"),
                    id="confirm_telegram_change",
                    on_click=confirm_telegram_id_change,
                ),
                Button(
                    Const("❌ Нет, отменить"),
                    id="cancel_telegram_change",
                    on_click=cancel_telegram_id_change,
                ),
            ),
        ),
        state=RegistrationSG.telegram_id_conflict,
        getter=get_telegram_id_conflict_data,
    ),
)
