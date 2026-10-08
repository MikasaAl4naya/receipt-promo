from django.urls import path
from . import api_views

urlpatterns = [
    path("receipts/", api_views.receipts_list, name="api_receipts"),
]
