from django.urls import path
from . import views

urlpatterns = [
    path("wallets/<str:address>/", views.GetAddressInformation.as_view()),
    path("pairs/", views.GetPairsList.as_view()),
    path("pairs/<str:address>/", views.GetPairsList.as_view()),
    path("wallets/", views.RegisterGetUserView.as_view()),
]
