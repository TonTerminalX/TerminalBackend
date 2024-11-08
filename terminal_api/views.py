from nacl.signing import SigningKey
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from terminal_api.models import UserWallets
from terminal_api.serializers import RegisterUserSerializer
from pytoniq_core.crypto.signature import verify_sign
import nacl

from terminal_api.utils.dexapi import DexScreenerApi
from terminal_api.utils.tonapi import WalletUtils, TonCenterApi


class RegisterGetUserView(APIView):
    async def post(self, request):
        body = request.data
        serializer = RegisterUserSerializer(data=body)
        serializer.is_valid(raise_exception=True)

        sign, address, message = serializer.signature, serializer.address, serializer.message
        public_key = WalletUtils.get_public_key_bytes(address)
        is_verified_signature = verify_sign(public_key, message, sign)
        if not is_verified_signature:
            return Response("Failed to verify signed message signature.", status=status.HTTP_400_BAD_REQUEST)

        # mnemo, new_wallet = await WalletUtils.generate_wallet()
        new_address, new_private_key, new_public_key, new_mnemonic = WalletUtils.generate_wallet()
        UserWallets(address=new_address, private_key=new_private_key, mnemonic=new_mnemonic, public_key=new_public_key)

        return Response({"address": new_address, "mnemonic": new_mnemonic, "public_key": new_public_key})


class GetPairsList(APIView):
    def get(self, request):
        search_param = request.query_params.get("search")
        if not search_param:
            return Response("Search param is not defined", status=status.HTTP_400_BAD_REQUEST)

        pairs = DexScreenerApi.search_for_pairs(search_param)
        return pairs["pairs"]


class GetAddressInformation(APIView):
    def get(self, request, address: str):
        address_info = TonCenterApi.get_account_info(address)
        return Response(address_info)
