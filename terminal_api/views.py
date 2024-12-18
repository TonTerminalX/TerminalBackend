from concurrent.futures import ThreadPoolExecutor

from asgiref.sync import async_to_sync
from django.core.cache import cache
from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from core.authenticate import CookieJWTAuthentication
from terminal_api.models import Order, Position, User, UserWallets
from terminal_api.serializers import (
    GetUserSerializer,
    JettonBalanceSerializer,
    MakeSwapSerializer,
    OrderSerializer,
    PairSerializer,
    PositionSerializer,
    RegisterOrLoginUserSerializer,
    UserWalletsAddresses,
    WalletSerializer,
)
from terminal_api.utils.dexapi import DexScreenerApi
from terminal_api.utils.geckoapi import GeckoTerminalApi
from terminal_api.utils.tonapi import TonCenterApi
from terminal_api.utils.wallet import WalletUtils


class RegisterUserView(APIView):
    def post(self, request):
        body = request.data
        serializer = RegisterOrLoginUserSerializer(data=body)
        serializer.is_valid(raise_exception=True)

        data = serializer.data
        sign, address, message = data["signature"], data["address"], data["message"]
        address = WalletUtils.to_user_friendly_address(address)
        # public_key = WalletUtils.get_public_key_bytes(address)

        # is_verified_signature = WalletUtils.verify_sign(public_key, message, sign)
        # if not is_verified_signature:
        #     return Response({"detail": "Failed to verify signed message signature."}, status=status.HTTP_403_FORBIDDEN)

        # is_exists_wallet = User.objects.get(id=request.user.id).exists()
        # if is_exists_wallet:
        #     return Response({"detail": "Already registered"}, status=status.HTTP_409_CONFLICT)

        # mnemo, new_wallet = await WalletUtils.generate_wallet()

        is_user_exists = User.objects.filter(address=address).exists()
        if is_user_exists:
            return Response(
                {"detail": "Already registered"}, status=status.HTTP_409_CONFLICT
            )

        _, new_address, new_private_key, new_public_key, new_mnemonic = async_to_sync(
            WalletUtils.generate_wallet
        )()
        new_wallet = UserWallets(
            address=new_address,
            private_key=new_private_key,
            mnemonic=new_mnemonic,
            public_key=new_public_key,
        )
        new_wallet.save()

        user = User(address=address, wallet=new_wallet)
        user.save()
        refresh = RefreshToken.for_user(user)

        response = Response(
            data={
                "address": new_address,
                "mnemonic": new_mnemonic,
                "public_key": new_public_key,
            }
        )
        response.set_cookie(
            key="access_token",
            value=str(refresh.access_token),
            samesite="None",
            secure=True,
            httponly=False,
        )

        return response


class UserMeView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            GetUserSerializer(request.user, context={"request": request}).data
        )


class LoginUserView(APIView):
    def post(self, request):
        body = request.data
        serializer = RegisterOrLoginUserSerializer(data=body)
        serializer.is_valid(raise_exception=True)
        data = serializer.data

        sign, address, message = data["signature"], data["address"], data["message"]
        # public_key = WalletUtils.get_public_key_bytes(address)
        # is_verified_signature = verify_sign(public_key, message, sign)
        # if not is_verified_signature:
        #     return Response("Failed to verify signed message signature.", status=status.HTTP_400_BAD_REQUEST)
        # WalletUtils.generate_wallet()

        try:
            user = User.objects.get(address=address)
        except User.DoesNotExist:
            return Response(
                {"detail": "User with this credentials not found"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)

        wallet = WalletSerializer(user.wallet)
        response = Response(
            data={"ok": True, "wallet": wallet.data["address"]},
            status=status.HTTP_200_OK,
        )
        response.set_cookie(
            key="access_token",
            value=str(refresh.access_token),
            samesite="None",
            secure=True,
            httponly=False,
        )
        return response


class GetPairsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class GetSearchPairs(APIView):
    pagination_class = GetPairsPagination
    serializer_class = PairSerializer

    def get_queryset(self):
        search_param = self.request.query_params["search"]

        pairs = DexScreenerApi.search_for_pairs(search_param)
        return [
            pair
            for pair in pairs
            if pair["chainId"] == "ton" and pair["dexId"] == "dedust"
        ]

    def get(self, request, *args, **kwargs):
        if not request.query_params.get("search"):
            return Response(
                {"detail": "search param is not defined"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pagination = self.pagination_class()
        data = self.get_queryset()
        paginated_queryset = pagination.paginate_queryset(data, request)

        serializer = self.serializer_class(paginated_queryset, many=True)
        return pagination.get_paginated_response(serializer.data)


class GetPair(APIView):
    serializer_class = PairSerializer

    def get(self, request, pool_address):
        result = DexScreenerApi.get_pair(pool_address)
        if not result:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(result)
        print(result)
        return Response(serializer.data)


class GetPairsChart(APIView):
    def get(self, request, pool_address: str):
        result = GeckoTerminalApi.get_ohlcv_data(pool_address)
        return Response(result)


class GetTrendingPairs(APIView):
    def get(self, request):
        cached_pairs = cache.get("trending_pairs")
        if cached_pairs:
            return Response(data=cached_pairs)
        pair_addresses = GeckoTerminalApi.default_pairs

        # def filter_pair(pair: dict):
        #     return (pair["relationships"]["quote_token"]["data"]["id"] == WalletUtils.TON_TOKEN_ADDRESS and
        #             pair["relationships"]["dex"]["data"]["id"] == "dedust")

        # filtered_pairs = list(filter(filter_pair, pairs))
        with ThreadPoolExecutor(max_workers=10) as executor:
            pairs = list(executor.map(GeckoTerminalApi.get_pair, pair_addresses))

        with ThreadPoolExecutor(max_workers=10) as executor:
            dexscreener_pairs = list(
                executor.map(DexScreenerApi.get_pair, pair_addresses)
            )
            # dexscreener_pairs = list(filter(lambda x: x, dexscreener_pairs))

        for dex_pair, gecko_pair in zip(dexscreener_pairs, pairs):
            if dex_pair:
                gecko_pair["info"] = dex_pair.get("info")
            else:
                gecko_pair["info"] = {}

        # serialized = PairSerializer(pairs, many=True)

        for pair in pairs:
            pair["attributes"]["symbol"] = pair["attributes"]["name"].split(" ")[0]
            if pair.get("info"):
                pair["attributes"]["image_url"] = pair["info"].get("imageUrl", "missing.png")
            else:
                pair["attributes"]["image_url"] = "missing.png"

        cache.set("trending_pairs", pairs, 120)
        return Response(pairs)


class GetAddressInformation(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, address):
        address_info = TonCenterApi.get_account_info(address)
        return Response(address_info)


class GetCreateUserOrders(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pass

    def get(self, request):
        pass


class GetCreateUserPositions(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PositionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data["user"] = request.user
        new_position = serializer.save()

        return Response(PositionSerializer(new_position).data)

    def get(self, request):
        all_user_positions = Position.objects.filter(user=request.user)
        all_user_positions = PositionSerializer(all_user_positions, many=True).data
        for position in all_user_positions:
            pair_data = DexScreenerApi.get_pair(position["pair_address"])
            pair_price_usd = float(pair_data["priceUsd"])
            pair_price_native = float(pair_data["priceNative"])

            position["pnl"] = (pair_price_usd / position["created_at_price"] - 1) * 100

        return Response(all_user_positions)


class SwapView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = MakeSwapSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data

        user = request.user
        wallet = user.wallet
        try:
            swap_tx = async_to_sync(WalletUtils.make_swap)(
                pool_address=data.get("pair_address"),
                jetton_address=data.get("jetton_address"),
                is_ton_transfer=data.get("is_ton_transfer"),
                amount=data.get("amount"),
                slippage=data.get("slippage"),
                mnemonic=wallet.mnemonic,
            )
            swap_tx = "success" if swap_tx == 1 else swap_tx
        except ValueError as e:
            print(e, type(e))
            detail = None
            text_error = e.args[0]
            if text_error == "Insufficient balance":
                detail = "Wallet balance insufficient"
            elif text_error == "Min amount":
                detail = (
                    f"Minimal amount is {WalletUtils.DEFAULT_GAS} TON. Ensure that amount and balance at least "
                    f"{WalletUtils.DEFAULT_GAS} TON"
                )

            return Response(data={"detail": detail})

        return Response(data={"status": swap_tx})


class GetJettonBalance(APIView):
    serializer_class = JettonBalanceSerializer

    def get(self, request, address, jetton_address):
        jetton_balance = TonCenterApi.get_jetton_balance(address, jetton_address)
        return Response(
            data={
                "balance": jetton_balance,
                "address": address,
                "jetton": jetton_address,
            }
        )


class GetWalletInfo(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = UserWalletsAddresses

    def get_queryset(self):
        return self.request.user.wallet

    def get(self, request):
        serialized_data = self.serializer_class(self.get_queryset()).data
        return Response(data=serialized_data)


class CreateGetOrders(ListCreateAPIView):
    serializer_class = OrderSerializer
    queryset = Order.objects.filter()
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(data={"orders": serializer.data})

    def perform_create(self, serializer):
        serializer.user = self.request.user
        serializer.save()


class IsUserExists(APIView):
    def get(self, request, address: str):
        address = WalletUtils.to_user_friendly_address(address)
        is_user_exists = User.objects.filter(address=address).exists()
        return Response(data={"exists": is_user_exists, "address": address})
