from datetime import date

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings

from .forms import ReceiptForm
from .models import Receipt


def _promo_ctx():
    start = date.fromisoformat(settings.PROMO_START_DATE)
    end = date.fromisoformat(settings.PROMO_END_DATE)
    return {"promo_start": f"{start:%d.%m.%Y}", "promo_end": f"{end:%d.%m.%Y}"}


@login_required
def register_receipt(request):
    ctx = _promo_ctx()
    if request.method == "POST":
        form = ReceiptForm(request.POST, request.FILES)
        if form.is_valid():
            receipt = form.save(commit=False)
            receipt.user = request.user
            receipt.status = Receipt.STATUS_PENDING
            receipt.save()
            return JsonResponse(
                {"success": True, "message": "Чек успешно зарегистрирован!"}
            )
        errors = {
            field: [str(e) for e in errs]
            for field, errs in form.errors.items()
        }
        return JsonResponse({"success": False, "errors": errors}, status=400)

    form = ReceiptForm()
    return render(request, "receipts/register.html", {"form": form, **ctx})


@login_required
def cabinet(request):
    qs = Receipt.objects.filter(user=request.user).order_by("-registered_at")
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    return render(
        request,
        "receipts/cabinet.html",
        {"page_obj": page_obj, **_promo_ctx()},
    )


@login_required
def receipt_status(request, pk):
    try:
        r = Receipt.objects.get(pk=pk, user=request.user)
    except Receipt.DoesNotExist:
        return JsonResponse({"error": "not found"}, status=404)
    return JsonResponse(
        {
            "status": r.status,
            "status_display": r.get_status_display(),
            "rejection_reason": r.rejection_reason,
        }
    )
