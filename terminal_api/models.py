from django.db import models


class UserWallets(models.Model):
    address = models.CharField(max_length=200)
    public_key = models.CharField(max_length=200)
    mnemonic = models.CharField(max_length=200)
    private_key = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now=True)


class User(models.Model):
    address = models.CharField(max_length=200)
    wallet = models.ForeignKey(UserWallets, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
