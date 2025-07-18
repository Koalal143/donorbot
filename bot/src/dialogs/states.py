from aiogram.fsm.state import State, StatesGroup


class RegistrationSG(StatesGroup):
    phone_input = State()
    name_confirmation = State()
    name_input = State()
    patronymic_confirmation = State()
    donor_type_selection = State()
    student_group_input = State()
    privacy_consent = State()
    registration_complete = State()


class OrganizerSG(StatesGroup):
    organizer_selection = State()
    organizer_registration = State()


class ProfileSG(StatesGroup):
    profile_view = State()
