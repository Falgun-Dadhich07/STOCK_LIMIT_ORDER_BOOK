from django.contrib import admin
from .models import User, Order, Trade, Stoploss_Order, MarketMaster


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username')
    search_fields = ('username',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order_type', 'order_mode', 'quantity', 'disclosed', 'price', 'is_matched', 'is_ioc', 'timestamp')
    list_filter = ('order_type', 'order_mode', 'is_matched', 'is_ioc')
    search_fields = ('user__username',)


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'seller', 'quantity', 'price', 'timestamp')
    search_fields = ('buyer__username', 'seller__username')


@admin.register(Stoploss_Order)
class StoplossOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order_type', 'order_mode', 'quantity', 'price', 'target_price', 'is_matched', 'timestamp')
    list_filter = ('order_type', 'order_mode', 'is_matched')
    search_fields = ('user__username',)


@admin.register(MarketMaster)
class MarketMasterAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'last_traded_price', 'total_trades', 'total_volume', 'day_high', 'day_low', 'opening_price', 'updated_at')
    list_filter = ('is_active',)
