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


class OrganizerSG(StatesGroup):
    organizer_selection = State()
    organizer_registration = State()
    organizer_menu = State()
    events_management = State()
    content_management = State()
    donor_days_management = State()
    donor_data_management = State()
    statistics_management = State()
    communication_management = State()


class ProfileSG(StatesGroup):
    profile_view = State()
