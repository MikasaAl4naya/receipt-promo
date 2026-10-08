import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import Receipt


@admin.action(description="Выгрузить принятые чеки в CSV")
def export_accepted_csv(modeladmin, request, queryset):
    accepted = queryset.filter(status=Receipt.STATUS_ACCEPTED)
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = 'attachment; filename="accepted_receipts.csv"'
    w = csv.writer(response)
    w.writerow(["ID", "Пользователь", "ФН", "ФД", "ФП", "Дата покупки", "Сумма", "Дата регистрации"])
    for r in accepted:
        w.writerow([
            r.pk,
            r.user.username,
            r.fn, r.fd, r.fp,
            r.purchase_date.strftime("%d.%m.%Y %H:%M"),
            r.amount,
            r.registered_at.strftime("%d.%m.%Y %H:%M"),
        ])
    return response


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "fn", "fd", "fp", "purchase_date", "amount", "status", "registered_at"]
    list_filter = ["status", "registered_at"]
    search_fields = ["fn", "fd", "fp", "user__username"]
    readonly_fields = ["fn", "fd", "fp", "purchase_date", "amount", "user", "registered_at", "photo"]
    fields = ["user", "fn", "fd", "fp", "purchase_date", "amount", "photo", "status", "rejection_reason", "registered_at"]
    actions = [export_accepted_csv]
