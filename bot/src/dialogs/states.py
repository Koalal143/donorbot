from aiogram.fsm.state import State, StatesGroup


class RegistrationSG(StatesGroup):
    phone_input_method = State()
    phone_input = State()
    name_confirmation = State()
    name_input = State()
    patronymic_confirmation = State()
    donor_type_selection = State()
    student_group_input = State()
    bone_marrow_donor_selection = State()
    privacy_consent = State()
    telegram_id_conflict = State()


class OrganizerSG(StatesGroup):
    organizer_selection = State()
    organizer_registration = State()
    organizer_menu = State()
    events_management = State()
    content_management = State()
    donor_days_management = State()
    donor_day_creation = State()
    donor_day_datetime_input = State()
    donor_days_list = State()
    donor_day_cancel_confirmation = State()
    donor_data_management = State()
    donor_search_input = State()
    donor_selection = State()
    donor_edit_template = State()
    donor_edit_help = State()
    donor_add_input = State()
    donor_add_help = State()
    statistics_management = State()
    communication_management = State()
    mailing_category_selection = State()
    mailing_message_input = State()
    mailing_confirmation = State()
    excel_generation_processing = State()
    excel_generation_result = State()

    donors_excel_generation_processing = State()
    donors_excel_generation_result = State()

    # Редактирование прошедших ДД
    past_donor_days_list = State()
    donor_day_participants = State()
    add_participant = State()
    participant_phone_input = State()
    participant_confirmation = State()
    edit_participant_status = State()

    # Управление контентом (организатор) - дополнительные состояния
    content_list = State()
    content_add_title = State()
    content_add_description = State()
    content_confirm = State()
    content_view = State()
    content_delete_confirm = State()


class ProfileSG(StatesGroup):
    profile_view = State()
    my_registrations = State()
    cancel_registration = State()
    donation_history = State()

    # Просмотр информационного контента
    content_list = State()
    content_view = State()


class DonorDayMenuSG(StatesGroup):
    menu = State()


class DonorDayRegistrationSG(StatesGroup):
    donor_days_list = State()
    donor_day_selection = State()
    registration_confirmation = State()
