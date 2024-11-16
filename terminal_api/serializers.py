from rest_framework import serializers

from terminal_api.models import Position, Order


class RegisterOrLoginUserSerializer(serializers.Serializer):
    address = serializers.CharField(max_length=200)
    signature = serializers.CharField()
    message = serializers.CharField()


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ["-user"]


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["-user"]
