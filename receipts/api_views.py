from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import Receipt


@login_required
def receipts_list(request):
    qs = Receipt.objects.filter(user=request.user).values(
        "id", "fn", "fd", "fp", "purchase_date",
        "amount", "status", "rejection_reason", "registered_at",
    )
    data = []
    for r in qs:
        data.append({
            **r,
            "amount": str(r["amount"]),
            "purchase_date": r["purchase_date"].isoformat() if r["purchase_date"] else None,
            "registered_at": r["registered_at"].isoformat() if r["registered_at"] else None,
        })
    return JsonResponse({"receipts": data})
