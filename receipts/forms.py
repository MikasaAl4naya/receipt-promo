import re
from datetime import date

from django import forms
from django.conf import settings

from .models import Receipt


def _promo_dates():
    return (
        date.fromisoformat(settings.PROMO_START_DATE),
        date.fromisoformat(settings.PROMO_END_DATE),
    )


class ReceiptForm(forms.ModelForm):
    class Meta:
        model = Receipt
        fields = ["fn", "fd", "fp", "purchase_date", "amount", "photo"]
        widgets = {
            "fn": forms.TextInput(attrs={"placeholder": "16 цифр"}),
            "fd": forms.TextInput(attrs={"placeholder": "До 10 цифр"}),
            "fp": forms.TextInput(attrs={"placeholder": "До 10 цифр"}),
            "purchase_date": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "amount": forms.NumberInput(
                attrs={"placeholder": "Минимум 1000", "step": "0.01"}
            ),
            "photo": forms.FileInput(
                attrs={"accept": "image/jpeg,image/png,image/webp"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["purchase_date"].input_formats = [
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M",
        ]

    def clean_fn(self):
        fn = self.cleaned_data.get("fn", "").strip()
        if not re.fullmatch(r"\d{16}", fn):
            raise forms.ValidationError("ФН должен содержать ровно 16 цифр")
        return fn

    def clean_fd(self):
        fd = self.cleaned_data.get("fd", "").strip()
        if not re.fullmatch(r"\d{1,10}", fd):
            raise forms.ValidationError("ФД: от 1 до 10 цифр")
        return fd

    def clean_fp(self):
        fp = self.cleaned_data.get("fp", "").strip()
        if not re.fullmatch(r"\d{1,10}", fp):
            raise forms.ValidationError("ФП: от 1 до 10 цифр")
        return fp

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount < 1000:
            raise forms.ValidationError("Сумма должна быть не менее 1 000 ₽")
        return amount

    def clean_purchase_date(self):
        purchase_date = self.cleaned_data.get("purchase_date")
        if purchase_date is None:
            return purchase_date
        promo_start, promo_end = _promo_dates()
        # Сравниваем только дату, игнорируя время и часовой пояс пользователя.
        # Если на чеке написано "31 марта" — чек принимается вне зависимости
        # от того, в каком часовом поясе живёт покупатель.
        purchase_day = purchase_date.date() if hasattr(purchase_date, "date") else purchase_date
        if purchase_day < promo_start:
            raise forms.ValidationError(
                f"Дата покупки раньше начала акции ({promo_start:%d.%m.%Y})"
            )
        if purchase_day > promo_end:
            raise forms.ValidationError(
                f"Дата покупки позже окончания акции ({promo_end:%d.%m.%Y})"
            )
        return purchase_date

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if not photo:
            return photo
        max_bytes = settings.RECEIPT_PHOTO_MAX_MB * 1024 * 1024
        if photo.size > max_bytes:
            raise forms.ValidationError(
                f"Файл слишком большой (максимум {settings.RECEIPT_PHOTO_MAX_MB} МБ)"
            )
        if photo.content_type not in settings.RECEIPT_PHOTO_ALLOWED_TYPES:
            raise forms.ValidationError("Допустимые форматы: JPEG, PNG, WebP")
        return photo

    def clean(self):
        cleaned = super().clean()
        fn = cleaned.get("fn")
        fd = cleaned.get("fd")
        fp = cleaned.get("fp")
        if fn and fd and fp:
            qs = Receipt.objects.filter(fn=fn, fd=fd, fp=fp)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                existing = qs.first()
                raise forms.ValidationError(
                    f"Чек с такими реквизитами уже зарегистрирован "
                    f"(статус: {existing.get_status_display()}). "
                    f"Повторная регистрация невозможна."
                )
        return cleaned
