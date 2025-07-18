import re
from typing import NamedTuple


class ValidationResult(NamedTuple):
    is_valid: bool
    error_message: str = ""


def validate_phone(phone: str) -> ValidationResult:
    phone = phone.strip()
    errors = []

    if not phone:
        errors.append("Номер телефона не может быть пустым.")
    elif len(phone) > 25:
        errors.append("Номер телефона слишком длинный (максимум 25 символов).")
    else:
        digits = re.sub(r"\D", "", phone)

        if not digits:
            errors.append("Номер телефона должен содержать цифры.")
        else:
            if len(digits) < 10:
                errors.append("Номер телефона слишком короткий (минимум 10 цифр).")

            if len(digits) > 11:
                errors.append("Номер телефона слишком длинный (максимум 11 цифр).")

            if not digits.startswith(("7", "8")):
                errors.append("Российский номер должен начинаться с 7 или 8.")

    is_valid = len(errors) == 0
    errors_text = "\n".join(f"• {error}" for error in errors)
    error_message = f"Произошли ошибки при валидации номера телефона:\n\n{errors_text}" if not is_valid else ""
    return ValidationResult(is_valid=is_valid, error_message=error_message)


def validate_full_name(name: str) -> ValidationResult:
    name = name.strip()
    errors = []

    if not name:
        errors.append("ФИО не может быть пустым.")
    else:
        if len(name) < 2:
            errors.append("ФИО слишком короткое (минимум 2 символа).")

        if len(name) > 100:
            errors.append("ФИО слишком длинное (максимум 100 символов).")

        parts = name.split()
        if len(parts) < 2:
            errors.append("Введите минимум фамилию и имя.")

        if len(parts) > 4:
            errors.append("Слишком много слов в ФИО (максимум 4).")

        for part in parts:
            if not part.isalpha():
                errors.append("ФИО должно содержать только буквы.")
                break

            if len(part) < 2:
                errors.append(f"Слово '{part}' слишком короткое (минимум 2 буквы).")

            if len(part) > 30:
                errors.append(f"Слово '{part}' слишком длинное (максимум 30 букв).")

    is_valid = len(errors) == 0
    errors_text = "\n".join(f"• {error}" for error in errors)
    error_message = f"Произошли ошибки при валидации ФИО:\n\n{errors_text}" if not is_valid else ""

    return ValidationResult(is_valid=is_valid, error_message=error_message)


def validate_student_group(group: str) -> ValidationResult:
    group = group.strip()
    errors = []

    if not group:
        errors.append("Номер группы не может быть пустым.")
    else:
        if len(group) < 2:
            errors.append("Номер группы слишком короткий (минимум 2 символа).")

        if len(group) > 20:
            errors.append("Номер группы слишком длинный (максимум 20 символов).")

        if not re.match(r"^[А-Яа-яA-Za-z0-9\-\.]+$", group):
            errors.append("Номер группы может содержать только буквы, цифры, дефисы и точки.")

    is_valid = len(errors) == 0
    errors_text = "\n".join(f"• {error}" for error in errors)
    error_message = f"Произошли ошибки при валидации номера группы:\n\n{errors_text}" if not is_valid else ""

    return ValidationResult(is_valid=is_valid, error_message=error_message)


def normalize_phone(phone: str) -> str:
    if not phone:
        return phone

    digits = re.sub(r"\D", "", phone)

    if not digits:
        return phone

    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    elif digits.startswith("9") and len(digits) == 10:
        digits = "7" + digits
    elif digits.startswith("7") and len(digits) == 11:
        pass
    elif len(digits) == 10 and not digits.startswith(("7", "8", "9")):
        digits = "7" + digits

    if digits.startswith("7") and len(digits) == 11:
        return "+" + digits

    return phone


def normalize_full_name(name: str) -> str:
    name = name.strip()
    parts = name.split()
    normalized_parts = [part.capitalize() for part in parts]
    return " ".join(normalized_parts)


def normalize_student_group(group: str) -> str:
    return group.strip().upper()
