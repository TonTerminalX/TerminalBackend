from concurrent.futures import ThreadPoolExecutor

from asgiref.sync import async_to_sync
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from core.authenticate import CookieJWTAuthentication
from terminal_api.models import UserWallets, User, Position
from terminal_api.serializers import RegisterOrLoginUserSerializer, PositionSerializer, GetUserSerializer, \
    PairSerializer, MakeSwapSerializer

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
        public_key = WalletUtils.get_public_key_bytes(address)

        # is_verified_signature = WalletUtils.verify_sign(public_key, message, sign)
        # if not is_verified_signature:
        #     return Response({"detail": "Failed to verify signed message signature."}, status=status.HTTP_403_FORBIDDEN)

        # is_exists_wallet = User.objects.get(id=request.user.id).exists()
        # if is_exists_wallet:
        #     return Response({"detail": "Already registered"}, status=status.HTTP_409_CONFLICT)

        # mnemo, new_wallet = await WalletUtils.generate_wallet()

        is_user_exists = User.objects.filter(address=address).exists()
        if is_user_exists:
            return Response({"detail": "already registered"}, status=status.HTTP_409_CONFLICT)

        _, new_address, new_private_key, new_public_key, new_mnemonic = async_to_sync(WalletUtils.generate_wallet)()
        new_wallet = UserWallets(address=new_address, private_key=new_private_key, mnemonic=new_mnemonic, public_key=new_public_key)
        new_wallet.save()

        user = User(address=address, wallet=new_wallet)
        user.save()
        refresh = RefreshToken.for_user(user)

        response = Response({"address": new_address, "mnemonic": new_mnemonic, "public_key": new_public_key})
        response.set_cookie(
            key='access_token',
            value=str(refresh.access_token),
            httponly=True,
            # secure=True,
        )

        return response


class UserMeView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(GetUserSerializer(request.user, context={'request': request}).data)


class LoginUserView(APIView):
    def post(self, request):
        body = request.data
        serializer = RegisterOrLoginUserSerializer(data=body)
        serializer.is_valid(raise_exception=True)
        data = serializer.data

        sign, address, message = data["signature"], data["address"], data["message"]
        public_key = WalletUtils.get_public_key_bytes(address)
        # is_verified_signature = verify_sign(public_key, message, sign)
        # if not is_verified_signature:
        #     return Response("Failed to verify signed message signature.", status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(address=address)
        refresh = RefreshToken.for_user(user)

        response = Response(status=status.HTTP_200_OK)
        response.set_cookie(
            key='access_token',
            value=str(refresh.access_token),
            httponly=True,
            # secure=True,
        )
        return response


class GetPairsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class GetSearchPairs(APIView):
    pagination_class = GetPairsPagination
    serializer_class = PairSerializer

    def get_queryset(self):
        search_param = self.request.query_params["search"]

        pairs = DexScreenerApi.search_for_pairs(search_param)
        return [
            pair for pair in pairs
            if pair["chainId"] == "ton" and pair["dexId"] == "dedust"
        ]

    def get(self, request, *args, **kwargs):
        if not request.query_params.get("search"):
            return Response(
                {"detail": "search param is not defined"},
                status=status.HTTP_400_BAD_REQUEST
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

        serialized = self.serializer_class(result)
        return Response(serialized.data)


class GetPairsChart(APIView):
    def get(self, request, pool_address: str):
        result = GeckoTerminalApi.get_ohlcv_data(pool_address)
        return Response(result)


class GetTrendingPairs(APIView):
    def get(self, request):
        pairs = GeckoTerminalApi.get_trending_pairs()
        with ThreadPoolExecutor(max_workers=10) as executor:
            pair_addresses = list(map(lambda x: x["attributes"]["address"], pairs))
            dexscreener_pairs = list(executor.map(DexScreenerApi.get_pair, pair_addresses))

        for dex_pair, gecko_pair in zip(dexscreener_pairs, pairs):
            gecko_pair["info"] = dex_pair.get("info")

        # serialized = PairSerializer(pairs, many=True)
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

        user = request.user
        wallet = user.wallet
        swap_tx = WalletUtils.make_swap(pool_address=serializer.pair_address,
                                        jetton_address=serializer.jetton_address,
                                        is_ton_transfer=serializer.is_ton_transfer,
                                        amount=serializer.amount,
                                        private_key=wallet.private_key)

        return Response({"hash": swap_tx})
