from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.RegisterUserView.as_view()),
    path("login/", views.LoginUserView.as_view()),
    path("users/me/", views.UserMeView.as_view()),
    path("users/<str:address>/exists", views.IsUserExists.as_view()),
    path("pairs/", views.GetSearchPairs.as_view()),
    path("pairs/trending/", views.GetTrendingPairs.as_view()),
    path("pairs/<str:pool_address>/", views.GetPair.as_view()),
    path("pairs/<str:pool_address>/chart", views.GetPairsChart.as_view()),
    path("positions/", views.GetCreateUserPositions.as_view()),
    path("orders/", views.CreateGetOrders.as_view()),
    path("wallets/swap/", views.SwapView.as_view()),
    path("wallets/", views.GetWalletInfo.as_view()),
    path("wallets/<str:address>/", views.GetAddressInformation.as_view()),
    path(
        "wallets/<str:address>/jettons/<str:jetton_address>/",
        views.GetJettonBalance.as_view(),
    ),
    # path("wallets/", views.RegisterGetUserView.as_view()),
]
