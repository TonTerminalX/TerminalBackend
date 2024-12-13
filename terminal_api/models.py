from django.db import models


class UserWallets(models.Model):
    address = models.CharField(max_length=48)
    public_key = models.CharField(max_length=64)
    mnemonic = models.CharField(max_length=220)
    private_key = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)


class User(models.Model):
    REQUIRED_FIELDS = ["address"]
    USERNAME_FIELD = "address"
    is_anonymous = False
    is_active = models.BooleanField(default=True)

    address = models.CharField(max_length=200, unique=True)
    wallet = models.ForeignKey(UserWallets, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_authenticated(self):
        return True

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
