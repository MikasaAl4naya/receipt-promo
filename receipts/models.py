from django.db import models
from django.conf import settings


class Receipt(models.Model):
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "На проверке"),
        (STATUS_ACCEPTED, "Принят"),
        (STATUS_REJECTED, "Отклонён"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="receipts",
        verbose_name="Пользователь",
    )
    fn = models.CharField("ФН", max_length=16)
    fd = models.CharField("ФД", max_length=10)
    fp = models.CharField("ФП", max_length=10)
    purchase_date = models.DateTimeField("Дата и время покупки")
    amount = models.DecimalField("Сумма (₽)", max_digits=12, decimal_places=2)
    status = models.CharField(
        "Статус", max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    rejection_reason = models.TextField("Причина отказа", blank=True)
    photo = models.ImageField(
        "Фото чека", upload_to="receipts/%Y/%m/", blank=True, null=True
    )
    registered_at = models.DateTimeField("Дата регистрации", auto_now_add=True)

    class Meta:
        unique_together = [["fn", "fd", "fp"]]
        ordering = ["-registered_at"]
        verbose_name = "Чек"
        verbose_name_plural = "Чеки"

    def __str__(self):
        return f"Чек {self.fn}/{self.fd}/{self.fp} ({self.get_status_display()})"

    @property
    def status_css(self):
        return {
            self.STATUS_PENDING: "pending",
            self.STATUS_ACCEPTED: "accepted",
            self.STATUS_REJECTED: "rejected",
        }.get(self.status, "pending")
