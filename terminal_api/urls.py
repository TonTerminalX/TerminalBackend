from django.urls import path
from . import views

urlpatterns = [
    path("wallets/", views.GetAddressInformation.as_view()),
    path("pairs/", views.GetPairsList.as_view()),
    path("pairs/<str:pair_address>", views.GetPair.as_view()),
    path("pairs/new/", views.GetNewPairs.as_view()),
    # path("wallets/", views.RegisterGetUserView.as_view()),
]
