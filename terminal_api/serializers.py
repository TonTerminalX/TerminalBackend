from rest_framework import serializers


class RegisterUserSerializer(serializers.Serializer):
    address = serializers.CharField(max_length=200)
    signature = serializers.CharField()
    message = serializers.CharField()
