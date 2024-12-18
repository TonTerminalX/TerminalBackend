# Generated by Django 5.1.4 on 2024-12-14 17:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "terminal_api",
            "0003_alter_userwallets_address_alter_userwallets_mnemonic_and_more",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="PairInfo",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("base_ticker", models.CharField(max_length=50)),
                ("quote_ticker", models.CharField(max_length=50)),
                ("base_token_address", models.CharField(max_length=50)),
                ("quote_token_address", models.CharField(max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.RemoveField(
            model_name="order",
            name="base_token",
        ),
        migrations.RemoveField(
            model_name="order",
            name="created_at_native_price",
        ),
        migrations.RemoveField(
            model_name="order",
            name="quote_token",
        ),
        migrations.AlterField(
            model_name="user",
            name="wallet",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="user",
                to="terminal_api.userwallets",
            ),
        ),
        migrations.AlterField(
            model_name="userwallets",
            name="address",
            field=models.CharField(max_length=48, unique=True),
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("tx_hash", models.CharField()),
                ("tx_timestamp", models.TimeField(null=True)),
                ("from_address", models.CharField()),
                ("amount", models.FloatField()),
                ("type_of_transaction", models.CharField()),
                ("token_address", models.CharField()),
                ("pool_address", models.CharField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="terminal_api.user",
                    ),
                ),
            ],
        ),
    ]
