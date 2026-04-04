from django.db import models
from django.utils.timezone import now
from decimal import Decimal


class User(models.Model):
    username = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.username

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

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES)
    order_mode = models.CharField(max_length=10, choices=ORDER_MODE_CHOICES)
    quantity = models.IntegerField()
    disclosed = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_matched = models.BooleanField(default=False)
    original_quantity = models.IntegerField(default=0)
    is_ioc = models.BooleanField(default=False)
    is_market_maker = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.order_type} {self.order_mode} Order #{self.id} by {self.user}"

class Trade(models.Model):
    buyer = models.ForeignKey(User, related_name='buy_trades', on_delete=models.CASCADE)
    seller = models.ForeignKey(User, related_name='sell_trades', on_delete=models.CASCADE)
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
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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


class MarketMaster(models.Model):
    name = models.CharField(max_length=100, default="Default Market")
    is_active = models.BooleanField(default=True)
    last_traded_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_trades = models.IntegerField(default=0)
    total_volume = models.IntegerField(default=0)
    day_high = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    day_low = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    opening_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Market Master"
        verbose_name_plural = "Market Masters"

    def __str__(self):
        status = "OPEN" if self.is_active else "CLOSED"
        return f"{self.name} [{status}] - LTP: {self.last_traded_price or 'N/A'}"

    def update_on_trade(self, trade_price, trade_quantity):
        """Update market stats after a trade executes."""
        self.last_traded_price = trade_price
        self.total_trades += 1
        self.total_volume += trade_quantity
        if self.day_high is None or trade_price > self.day_high:
            self.day_high = trade_price
        if self.day_low is None or trade_price < self.day_low:
            self.day_low = trade_price
        if self.opening_price is None:
            self.opening_price = trade_price
        self.save()

    def reset_daily_stats(self):
        """Reset daily stats (call at market open)."""
        self.day_high = None
        self.day_low = None
        self.opening_price = None
        self.total_trades = 0
        self.total_volume = 0
        self.save()


class MarketMakerConfig(models.Model):
    """Configuration for a user's automated market-making strategy."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='market_maker')
    is_active = models.BooleanField(default=False)
    reference_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Base price for orders. Leave blank to use Last Traded Price."
    )
    spread_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('1.00'),
        help_text="Spread percentage per level (e.g. 1.0 = 1%)"
    )
    quantity = models.IntegerField(
        default=100,
        help_text="Number of shares per order at each level"
    )
    num_levels = models.IntegerField(
        default=3,
        help_text="Number of buy/sell price levels to maintain (1-10)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Market Maker Config"
        verbose_name_plural = "Market Maker Configs"

    def __str__(self):
        status = "ACTIVE" if self.is_active else "INACTIVE"
        return f"MarketMaker({self.user.username}) [{status}]"
