from django.core.cache import cache
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from terminal_api.models import UserWallets, User, Position
from terminal_api.serializers import RegisterOrLoginUserSerializer, PositionSerializer
from pytoniq_core.crypto.signature import verify_sign

from terminal_api.utils.dexapi import DexScreenerApi
from terminal_api.utils.tonapi import TonCenterApi
from terminal_api.utils.wallet import WalletUtils


class RegisterUserView(APIView):
    async def post(self, request):
        body = request.data
        serializer = RegisterOrLoginUserSerializer(data=body)
        serializer.is_valid(raise_exception=True)

        sign, address, message = serializer.signature, serializer.address, serializer.message
        public_key = WalletUtils.get_public_key_bytes(address)
        is_verified_signature = verify_sign(public_key, message, sign)
        if not is_verified_signature:
            return Response("Failed to verify signed message signature.", status=status.HTTP_400_BAD_REQUEST)

        # mnemo, new_wallet = await WalletUtils.generate_wallet()
        _, new_address, new_private_key, new_public_key, new_mnemonic = WalletUtils.generate_wallet()
        UserWallets(address=new_address, private_key=new_private_key, mnemonic=new_mnemonic, public_key=new_public_key)

        return Response({"address": new_address, "mnemonic": new_mnemonic, "public_key": new_public_key})


class UserMeView(APIView):
    pass


class LoginUserView(APIView):
    def post(self, request):
        body = request.data
        serializer = RegisterOrLoginUserSerializer(data=body)
        serializer.is_valid(raise_exception=True)

        sign, address, message = serializer.signature, serializer.address, serializer.message
        public_key = WalletUtils.get_public_key_bytes(address)
        is_verified_signature = verify_sign(public_key, message, sign)
        if not is_verified_signature:
            return Response("Failed to verify signed message signature.", status=status.HTTP_400_BAD_REQUEST)

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


class GetPairsList(ListAPIView):
    pagination_class = GetPairsPagination

    def get_queryset(self):
        search_param = self.request.query_params.get("search")
        if not search_param:
            return Response("Search param is not defined", status=status.HTTP_400_BAD_REQUEST)

        pairs = DexScreenerApi.search_for_pairs(search_param)["pairs"]
        return [
            pair for pair in pairs
            if pair["chainId"] == "ton" and pair["dexId"] == "dedust"
        ]

    def list(self, request, *args, **kwargs):
        if not request.query_params.get("search"):
            return Response(
                "Search param is not defined",
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().list(request, *args, **kwargs)


class GetPair(APIView):
    def get(self, request, pair_address):
        result = DexScreenerApi.get_pair(pair_address)
        return Response(result)


class GetNewPairs(APIView):
    def get(self, request):
        pairs = DexScreenerApi.get_new_pairs()
        return Response(pairs)


class GetAddressInformation(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        address = request.user.wallet.address
        address_info = TonCenterApi.get_account_info(address)
        return Response(address_info)


class GetCreateUserOrders(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pass

    def get(self, request):
        pass


class GetCreateUserPositions(APIView):
    authentication_classes = [JWTAuthentication]
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
