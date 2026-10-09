from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register_receipt, name="register_receipt"),
    path("cabinet/", views.cabinet, name="cabinet"),
    path("rules/", views.rules, name="rules"),
    path("profile/", views.profile, name="profile"),
    path("status/<int:pk>/", views.receipt_status, name="receipt_status"),
]
