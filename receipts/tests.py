from datetime import datetime, timezone
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from .forms import ReceiptForm
from .models import Receipt

User = get_user_model()


def _valid_data(**overrides):
    defaults = {
        "fn": "1234567890123456",
        "fd": "12345",
        "fp": "123456789",
        "purchase_date": "2024-02-15T12:00",
        "amount": "1500.00",
    }
    defaults.update(overrides)
    return defaults


class ReceiptFormTest(TestCase):
    def setUp(self):
        settings.PROMO_START_DATE = "2024-01-01"
        settings.PROMO_END_DATE = "2024-03-31"
        self.user = User.objects.create_user("tester", password="pass")

    # --- валидный чек ---

    def test_valid_receipt(self):
        form = ReceiptForm(data=_valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    # --- сумма ---

    def test_amount_below_minimum(self):
        form = ReceiptForm(data=_valid_data(amount="999.99"))
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_amount_exactly_minimum(self):
        form = ReceiptForm(data=_valid_data(amount="1000.00"))
        self.assertTrue(form.is_valid(), form.errors)

    # --- дата: границы акции ---

    def test_date_before_promo(self):
        form = ReceiptForm(data=_valid_data(purchase_date="2023-12-31T23:59"))
        self.assertFalse(form.is_valid())
        self.assertIn("purchase_date", form.errors)

    def test_date_after_promo(self):
        form = ReceiptForm(data=_valid_data(purchase_date="2024-04-01T00:01"))
        self.assertFalse(form.is_valid())
        self.assertIn("purchase_date", form.errors)

    def test_date_on_start_boundary(self):
        form = ReceiptForm(data=_valid_data(purchase_date="2024-01-01T00:00"))
        self.assertTrue(form.is_valid(), form.errors)

    def test_date_on_end_boundary(self):
        form = ReceiptForm(data=_valid_data(purchase_date="2024-03-31T23:59"))
        self.assertTrue(form.is_valid(), form.errors)

    # --- ФН / ФД / ФП ---

    def test_fn_too_short(self):
        form = ReceiptForm(data=_valid_data(fn="123"))
        self.assertFalse(form.is_valid())
        self.assertIn("fn", form.errors)

    def test_fn_non_digits(self):
        form = ReceiptForm(data=_valid_data(fn="12345678901234AB"))
        self.assertFalse(form.is_valid())
        self.assertIn("fn", form.errors)

    def test_fd_non_digits(self):
        form = ReceiptForm(data=_valid_data(fd="1A3"))
        self.assertFalse(form.is_valid())
        self.assertIn("fd", form.errors)

    # --- уникальность ---

    def test_duplicate_receipt(self):
        Receipt.objects.create(
            user=self.user,
            fn="1234567890123456", fd="12345", fp="123456789",
            purchase_date=datetime(2024, 2, 15, 12, 0, tzinfo=timezone.utc),
            amount=Decimal("1500.00"),
        )
        form = ReceiptForm(data=_valid_data())
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_rejected_receipt_cannot_be_resubmitted(self):
        """Отклонённый чек нельзя подать повторно — уникальность ФН+ФД+ФП."""
        Receipt.objects.create(
            user=self.user,
            fn="1234567890123456", fd="12345", fp="123456789",
            purchase_date=datetime(2024, 2, 15, 12, 0, tzinfo=timezone.utc),
            amount=Decimal("1500.00"),
            status=Receipt.STATUS_REJECTED,
            rejection_reason="Тест",
        )
        form = ReceiptForm(data=_valid_data())
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
