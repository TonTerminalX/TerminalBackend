from django.db import models


class UserWallets(models.Model):
    address = models.CharField(max_length=200)
    public_key = models.CharField(max_length=200)
    mnemonic = models.CharField(max_length=200)
    private_key = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)


class User(models.Model):
    address = models.CharField(max_length=200)
    wallet = models.ForeignKey(UserWallets, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Position(models.Model):
    base_token = models.CharField(max_length=50)
    quote_token = models.CharField(max_length=50)
    base_token_address = models.CharField(max_length=50)
    quote_token_address = models.CharField(max_length=50)

    created_at_price = models.FloatField()
    created_at_native_price = models.FloatField()
    sold_price = models.FloatField()
    sold_native_price = models.FloatField()

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pair_address = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Order(models.Model):
    base_token = models.CharField(max_length=50)
    quote_token = models.CharField(max_length=50)
    base_token_address = models.CharField(max_length=50)
    quote_token_address = models.CharField(max_length=50)

    created_at_price = models.FloatField()
    created_at_native_price = models.FloatField()

    limit_price = models.FloatField()

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pair_address = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    filled_at = models.DateTimeField()
