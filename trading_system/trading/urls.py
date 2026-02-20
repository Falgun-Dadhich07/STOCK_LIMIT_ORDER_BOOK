from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', auth_views.LoginView.as_view(template_name='trading/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('home/', views.home, name='home'),
    path('orderbook/', views.orderbook, name='orderbook'),
    path('modify/', views.modify, name='modify'),
    path('clear/', views.clear_database, name='clear_database'),
    path('orderbook/get_best_ask/', views.get_best_ask, name='get_best_ask'),
    path('orderbook/get_best_bid/', views.get_best_bid, name='get_best_bid'),
    path('orderbook/get_buy_orders/', views.get_buy_orders, name='get_buy_orders'),
    path('orderbook/get_sell_orders/', views.get_sell_orders, name='get_sell_orders'),
    path('orderbook/get_recent_trades/', views.get_recent_trades, name='get_recent_trades'),
    path('orderbook/get_best_ask/', views.get_best_ask, name='get_best_ask'),
    path('modify/get_best_bid/', views.get_best_bid, name='get_best_bid'),
    path('modify/get_buy_orders/', views.get_buy_orders, name='get_buy_orders'),
    path('modify/get_sell_orders/', views.get_sell_orders, name='get_sell_orders'),
    path('modify_order/', views.modify_order_page, name='modify_order'),
    path('modify_order/update_prev_order/', views.update_prev_order, name='update_prev_order'),
    path('cancel_order/', views.cancel_order, name='cancel_order'),
    path('cancel_stoploss_order/', views.cancel_stoploss_order, name='cancel_stoploss_order'),
]

