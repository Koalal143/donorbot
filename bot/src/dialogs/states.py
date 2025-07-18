from aiogram.fsm.state import State, StatesGroup


class RegistrationSG(StatesGroup):
    phone_input = State()
    name_confirmation = State()
    name_input = State()
    patronymic_confirmation = State()
    donor_type_selection = State()
    student_group_input = State()
    privacy_consent = State()
    account_access = State()


class OrganizerSG(StatesGroup):
    organizer_flow = State()


class ProfileSG(StatesGroup):
    profile_view = State()
