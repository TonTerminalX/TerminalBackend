from django.urls import path
from . import views

urlpatterns = [
    path("wallets/<str:address>/", views.GetAddressInformation),
    path("pairs/<str:address>/", views.GetPairsList)
]
