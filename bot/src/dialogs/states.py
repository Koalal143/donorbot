from aiogram.fsm.state import State, StatesGroup


class RegistrationSG(StatesGroup):
    phone_input_method = State()
    phone_input = State()
    name_confirmation = State()
    name_input = State()
    patronymic_confirmation = State()
    donor_type_selection = State()
    student_group_input = State()
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
    statistics_management = State()
    communication_management = State()


class ProfileSG(StatesGroup):
    profile_view = State()
    my_registrations = State()
    cancel_registration = State()
    donation_history = State()


class DonorDayMenuSG(StatesGroup):
    menu = State()


class DonorDayRegistrationSG(StatesGroup):
    donor_days_list = State()
    donor_day_selection = State()
    registration_confirmation = State()
