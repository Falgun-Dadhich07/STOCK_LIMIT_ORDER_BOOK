from django.db import models
from django.utils.timezone import now
from django.core.exceptions import ValidationError


class BaseUser(models.Model):
    username = models.CharField(max_length=100, unique=True)
    ROLE_CHOICES = (
        ('TRADER', 'Trader'),
        ('MARKET_MAKER', 'Market Maker'),
        ('ADMIN', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    def __str__(self):
        return self.username


class Trader(BaseUser):
    def allowed_order_modes(self):
        return ['MARKET']


class MarketMaker(BaseUser):
    def allowed_order_modes(self):
        return ['LIMIT']

from datetime import datetime

class Order(models.Model):
    ORDER_TYPE_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]

    ORDER_MODE_CHOICES = [
        ('LIMIT', 'Limit'),
        ('MARKET', 'Market'),
    ]

    ROLE_CHOICES = [
        ('TRADER', 'Trader'),
        ('MARKET_MAKER', 'Market Maker'),
    ]

    def clean(self):
        if self.user_role == 'TRADER' and self.order_mode != 'MARKET':
            raise ValidationError("Trader can only place MARKET orders")

        if self.user_role == 'MARKET_MAKER' and self.order_mode != 'LIMIT':
            raise ValidationError("Market Maker can only place LIMIT orders")

        if self.order_mode == 'MARKET' and self.price is not None:
            raise ValidationError("Market orders cannot have price")

        if self.order_mode == 'LIMIT' and self.price is None:
            raise ValidationError("Limit orders must have price")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    


    user = models.ForeignKey(BaseUser, on_delete=models.CASCADE)
    user_role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES)
    order_mode = models.CharField(max_length=10, choices=ORDER_MODE_CHOICES)
    quantity = models.IntegerField()
    disclosed = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_matched = models.BooleanField(default=False)
    # original_quantity = models.IntegerField()
    original_quantity = models.IntegerField(default=0)  # New field added

 

    is_ioc = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.order_type} {self.order_mode} Order #{self.id} by {self.user}"

class Trade(models.Model):
    buyer = models.ForeignKey(BaseUser, related_name='buy_trades', on_delete=models.CASCADE)
    seller = models.ForeignKey(BaseUser, related_name='sell_trades', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trade #{self.id}: {self.buyer} ⇄ {self.seller} ({self.quantity} @ {self.price})"


class Stoploss_Order(models.Model):
    ORDER_TYPE_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]

    ORDER_MODE_CHOICES = [
        ('LIMIT', 'Limit'),
        ('MARKET', 'Market'),
    ]
    
    user = models.ForeignKey(BaseUser, on_delete=models.CASCADE)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES)
    order_mode = models.CharField(max_length=10, choices=ORDER_MODE_CHOICES)
    quantity = models.IntegerField()
    disclosed= models.IntegerField(default=0)
    target_price=models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_matched = models.BooleanField(default=False)
    is_ioc = models.BooleanField(default=False)

    def __str__(self):
        return f"StopLoss {self.order_type} Order #{self.id} (Target: {self.target_price})"
