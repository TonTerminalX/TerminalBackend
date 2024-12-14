from pytoniq_core import Address
from rest_framework import serializers

from terminal_api.models import Position, Order, User, UserWallets
from terminal_api.utils.address import is_valid_address


class RegisterOrLoginUserSerializer(serializers.Serializer):
    address = serializers.CharField(max_length=200)
    signature = serializers.CharField()
    message = serializers.CharField()


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        exclude = ["user"]


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserWallets
        fields = ["address", "created_at"]


class GetUserSerializer(serializers.ModelSerializer):
    wallet = WalletSerializer()

    class Meta:
        model = User
        depth = 1
        fields = ["address", "created_at", "wallet"]


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    created_at = serializers.DateTimeField(read_only=True)
    filled_at = serializers.DateTimeField(read_only=True)

    def validate(self, attrs):
        # validate address
        for address in (attrs["base_token_address"], attrs["quote_token_address"]):
            if not is_valid_address(address):
                message = f"Validation address failed."
                raise serializers.ValidationError(message)

            return super().validate(attrs)

    class Meta:
        model = Order
        fields = "__all__"


class PairSerializer(serializers.Serializer):
    chain_id = serializers.CharField(source='chainId')
    dex_id = serializers.CharField(source='dexId')
    url = serializers.CharField()
    pair_address = serializers.CharField(source='pairAddress')
    base_token = serializers.JSONField(source='baseToken')
    quote_token = serializers.JSONField(source='quoteToken')
    price_native = serializers.FloatField(source='priceNative')
    price_usd = serializers.FloatField(source='priceUsd')
    txns = serializers.JSONField()
    volume = serializers.JSONField()
    price_change = serializers.JSONField(source='priceChange')
    liquidity = serializers.JSONField()
    fdv = serializers.IntegerField(min_value=0)
    market_cap = serializers.IntegerField(source='marketCap', min_value=0)
    pair_created_at = serializers.IntegerField(source='pairCreatedAt', min_value=0, allow_null=True, required=False)
    info = serializers.JSONField(allow_null=True, default=None, required=False)


class PairDetailedInfoSerializer(serializers.Serializer):
    ...


class MakeSwapSerializer(serializers.Serializer):
    pair_address = serializers.CharField(max_length=200)
    jetton_address = serializers.CharField(max_length=200)
    is_ton_transfer = serializers.BooleanField()
    amount = serializers.FloatField(min_value=0)
    slippage = serializers.FloatField(min_value=0, max_value=100)


class WalletInfoSerializer(serializers.Serializer):
    pass


class JettonBalanceSerializer(serializers.Serializer):
    jetton_address = serializers.CharField(max_length=48)
    balance = serializers.FloatField(min_value=0)


class UserWalletsAddresses(serializers.ModelSerializer):
    class Meta:
        model = UserWallets
        fields = ["created_at", "address", "public_key"]
