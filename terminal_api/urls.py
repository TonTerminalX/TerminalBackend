from django.urls import path
from . import views

urlpatterns = [
    path("wallets/<str:address>/", views.GetAddressInformation.as_view()),
    path("signup/", views.RegisterUserView.as_view()),
    path("login/", views.LoginUserView.as_view()),
    path("users/me/", views.UserMeView.as_view()),
    path("pairs/", views.GetSearchPairs.as_view()),
    path("pairs/trending/", views.GetTrendingPairs.as_view()),
    path("pairs/<str:pool_address>/", views.GetPair.as_view()),
    path("pairs/<str:pool_address>/chart", views.GetPairsChart.as_view()),
    path("positions/", views.GetCreateUserPositions.as_view()),
    path("wallets/swap/", views.SwapView.as_view()),
    # path("wallets/", views.RegisterGetUserView.as_view()),
]
