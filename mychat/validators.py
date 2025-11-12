from django.core.exceptions import ValidationError

def validate_file_size(value):
    max_size = 50 * 1024 * 1024  # 50 МБ
    if value.size > max_size:
        raise ValidationError("Файл не может быть больше 50 МБ")
