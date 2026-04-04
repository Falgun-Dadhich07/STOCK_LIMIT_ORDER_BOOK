from django.shortcuts import render, redirect
from .models import User, Order, Trade, Stoploss_Order, MarketMaster, MarketMakerConfig
from django.db.models import Q
from django.db import transaction
from django.contrib.auth.decorators import login_required
import json
from decimal import Decimal, ROUND_HALF_UP
from django.contrib import messages
from .utils import broadcast_orderbook_update, match_order, get_or_create_market
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        user, created = User.objects.get_or_create(username=username)
        return redirect('home', user_id=user.id)
    return render(request, 'trading/login.html')


def fetch_best_ask():
    return Order.objects.filter(order_type="SELL", is_matched=False).order_by('price').values('price', 'quantity').first()


def fetch_best_bid():
    return Order.objects.filter(order_type="BUY", is_matched=False).order_by('-price').values('price', 'quantity').first()


def get_best_ask(request):
    if request.method == 'GET':
        best_ask = Order.objects.filter(order_type="SELL", is_matched=False).order_by('price').values('price', 'disclosed').first()
        return JsonResponse({'best_ask': best_ask})
    return JsonResponse({'best_ask': None})


def get_best_bid(request):
    if request.method == 'GET':
        best_bid = Order.objects.filter(order_type="BUY", is_matched=False).order_by('-price').values('price', 'disclosed').first()
        return JsonResponse({'best_bid': best_bid})
    return JsonResponse({'best_bid': None})


@login_required
def home(request):
    user = request.user
    user, created = User.objects.get_or_create(username=user.username)
    market = get_or_create_market()

    if request.method == "POST":
        # Check if market is active
        if not market.is_active:
            messages.error(request, "Market is currently CLOSED. Orders cannot be placed.")
            return redirect('/home')

        order_type = request.POST.get('order_type')
        order_mode = request.POST.get('order_mode')
        quantity = int(request.POST.get('quantity'))
        disclosed = int(request.POST.get('disclosed_quantity'))
        stoploss_order = request.POST.get('Stoploss_order')
        target_price = request.POST.get('Target_price')
        is_ioc = request.POST.get('is_ioc') == 'True'
        original_quantity = quantity

        price = None
        end_time = request.POST.get('end_time')

        if disclosed == 0:
            disclosed = quantity

        try:
            if order_mode == "LIMIT":
                price = float(request.POST.get('price', 0))
            elif order_mode == "MARKET":
                if order_type == "BUY":
                    best_ask_response = fetch_best_ask()
                    best_ask_data = best_ask_response
                    price = best_ask_data['price']
                elif order_type == "SELL":
                    best_bid_response = fetch_best_bid()
                    best_bid_data = best_bid_response
                    price = best_bid_data['price']

                if price is None:
                    return render(request, 'trading/home.html', {'error': 'Unable to fetch market price for the order type.'})

            if disclosed > quantity:
                disclosed = quantity

            if stoploss_order == 'NO' or stoploss_order is None:
                new_order = Order(
                    order_type=order_type,
                    order_mode=order_mode,
                    quantity=quantity,
                    disclosed=disclosed,
                    price=price,
                    is_matched=False,
                    is_ioc=is_ioc,
                    user=user,
                    original_quantity=original_quantity
                )

                if disclosed < 0.1 * quantity:
                    messages.error(request, "Disclosed Quantity cannot be less than 10% of Quantity.")
                else:
                    messages.success(request, "Order placed successfully!")
                    try:
                        new_order.save()
                        broadcast_orderbook_update()
                        if not is_ioc:
                            match_order(new_order)
                        messages.success(request, 'Your order has been placed successfully!')
                    except Exception as e:
                        messages.error(request, f"Order could not be saved: {e}")
                    return redirect('/home')
            else:
                new_order = Stoploss_Order(
                    order_type=order_type,
                    order_mode=order_mode,
                    quantity=quantity,
                    disclosed=disclosed,
                    target_price=target_price,
                    price=price,
                    is_matched=False,
                    is_ioc=is_ioc,
                    user=user,
                )
                broadcast_orderbook_update()

                if disclosed < 0.1 * quantity:
                    messages.error(request, "Disclosed Quantity cannot be less than 10% of Quantity.")
                else:
                    messages.success(request, "Stoploss Order placed successfully!")
                    new_order.save()
                    broadcast_orderbook_update()
                    messages.success(request, 'Your Stoploss order has been placed successfully!')
                    return redirect('/home')

        except Exception as e:
            return render(request, 'trading/home.html', {'error': 'Unable to fetch market price for the order type.'})

    orders = Order.objects.filter(user=user)
    trades = Trade.objects.filter(Q(buyer=user) | Q(seller=user))
    stoploss_orders = Stoploss_Order.objects.filter(user=user)

    execute_order()
    return render(request, 'trading/home.html', {
        'user': user,
        'orders': orders,
        'trades': trades,
        'stoploss_orders': stoploss_orders,
        'market': market,
    })


def orderbook(request):
    buy_orders = Order.objects.filter(is_matched=False, order_type='BUY').order_by('-price')
    sell_orders = Order.objects.filter(is_matched=False, order_type='SELL').order_by('price')
    trades = Trade.objects.all().order_by('-timestamp')
    market = get_or_create_market()

    return render(request, 'trading/orderbook.html', {
        'buy_orders': buy_orders,
        'sell_orders': sell_orders,
        'best_bid': buy_orders.first() if buy_orders else None,
        'best_ask': sell_orders.first() if sell_orders else None,
        'trades': trades,
        'market': market,
    })


@login_required
def modify(request):
    buy_orders = Order.objects.filter(is_matched=False, order_type='BUY').order_by('-price')
    sell_orders = Order.objects.filter(is_matched=False, order_type='SELL').order_by('price')
    trades = Trade.objects.all().order_by('-timestamp')

    return render(request, 'trading/modify.html', {
        'buy_orders': buy_orders,
        'sell_orders': sell_orders,
        'best_bid': buy_orders.first() if buy_orders else None,
        'best_ask': sell_orders.first() if sell_orders else None,
        'trades': trades,
    })


@login_required
def modify_order_page(request):
    buy_orders = Order.objects.filter(is_matched=False, order_type='BUY').order_by('-price')
    sell_orders = Order.objects.filter(is_matched=False, order_type='SELL').order_by('price')
    trades = Trade.objects.all().order_by('-timestamp')

    return render(request, 'trading/modify_order.html', {
        'buy_orders': buy_orders,
        'sell_orders': sell_orders,
        'trades': trades,
    })


@login_required
def update_prev_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            new_quantity = data.get('quantity')
            new_disclosed = data.get('disclosed_quantity')
            new_price = data.get('price')

            order_id = int(order_id)
            new_quantity = int(new_quantity)
            new_disclosed = int(new_disclosed)
            new_price = float(new_price)

            order = Order.objects.get(id=order_id)
            if order.is_matched:
                return JsonResponse({'success': False, 'message': 'Order has already been placed. No modifications allowed.'})
            if new_disclosed < new_quantity * 0.1:
                return JsonResponse({'success': False, 'message': 'Disclosed value must be greater than 10% of quantity.'})
            if new_disclosed > new_quantity:
                return JsonResponse({'success': False, 'message': 'Cannot disclose more than the quantity.'})
            if new_price <= 0:
                return JsonResponse({'success': False, 'message': 'Price must be greater than 0.'})

            order.quantity = new_quantity
            order.disclosed = new_disclosed
            order.price = new_price
            order.save()
            broadcast_orderbook_update()

            # Try matching again after modification
            match_order(order)

            return JsonResponse({'success': True})

        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Order not found.'})
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Invalid data provided.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})


def clear_database(request):
    Order.objects.all().delete()
    Trade.objects.all().delete()
    # Reset market stats
    try:
        market = MarketMaster.objects.get(pk=1)
        market.reset_daily_stats()
    except MarketMaster.DoesNotExist:
        pass
    return redirect('login')


def get_buy_orders(request):
    if request.method == 'GET':
        buy_orders = Order.objects.filter(order_type='BUY', is_matched=False).values(
            'user', 'price', 'disclosed', 'is_matched', 'id', 'is_ioc', 'quantity', 'original_quantity'
        )
        return JsonResponse({'buy_orders': list(buy_orders)})


def get_sell_orders(request):
    if request.method == 'GET':
        sell_orders = Order.objects.filter(order_type='SELL', is_matched=False).values(
            'user', 'price', 'disclosed', 'is_matched', 'id', 'is_ioc', 'quantity', 'original_quantity'
        )
        return JsonResponse({'sell_orders': list(sell_orders)})


def get_recent_trades(request):
    if request.method == 'GET':
        recent_trades = Trade.objects.all().order_by('-timestamp')[:10].values(
            'buyer', 'seller', 'price', 'quantity', 'timestamp'
        )
        return JsonResponse({'trades': list(recent_trades)})


@login_required
def cancel_order(request):
    if request.method == 'POST':
        try:
            user = User.objects.get(username=request.user.username)
            data = json.loads(request.body)
            order_id = data.get('order_id')

            with transaction.atomic():
                order = Order.objects.get(id=order_id, user=user, is_matched=False)
                order.delete()

            broadcast_orderbook_update()
            return JsonResponse({'success': True, 'message': 'Order cancelled successfully'})

        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User authentication failed'}, status=401)
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Order not found or already matched'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid request format'}, status=400)
        except Exception as e:
            logger.error(f"Cancel order error: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
def cancel_stoploss_order(request):
    if request.method == 'POST':
        try:
            user = User.objects.get(username=request.user.username)
            data = json.loads(request.body)
            order_id = data.get('order_id')

            with transaction.atomic():
                order = Stoploss_Order.objects.get(id=order_id, user=user, is_matched=False)
                order.delete()

            return JsonResponse({'success': True, 'message': 'Stoploss order cancelled successfully'})

        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User authentication failed'}, status=401)
        except Stoploss_Order.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Order not found or already matched'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid request format'}, status=400)
        except Exception as e:
            logger.error(f"Cancel stoploss order error: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


def convert_stoploss_to_order(stoploss_order):
    return Order(
        user=stoploss_order.user,
        order_type=stoploss_order.order_type,
        order_mode=stoploss_order.order_mode,
        quantity=stoploss_order.quantity,
        price=stoploss_order.price,
        disclosed=stoploss_order.disclosed,
        original_quantity=stoploss_order.quantity,
        timestamp=timezone.now(),
        is_matched=False
    )


from django.utils import timezone


@transaction.atomic
def execute_order():
    """Execute stop-loss orders when trigger conditions are met."""
    last_trade = Trade.objects.last()
    if not last_trade:
        return

    closing_price = last_trade.price

    stop_loss_buy_orders = Stoploss_Order.objects.filter(order_type='BUY').order_by('target_price')
    stop_loss_sell_orders = Stoploss_Order.objects.filter(order_type='SELL').order_by('-target_price')

    for buy_order in stop_loss_buy_orders:
        if buy_order.target_price >= closing_price:
            new_order = convert_stoploss_to_order(buy_order)
            new_order.save()
            match_order(new_order)
            buy_order.delete()

    for sell_order in stop_loss_sell_orders:
        if sell_order.target_price <= closing_price:
            new_order = convert_stoploss_to_order(sell_order)
            new_order.save()
            match_order(new_order)
            sell_order.delete()


# ===========================
# Market Master Views
# ===========================

@login_required
def market_dashboard(request):
    """Market Master dashboard - accessible to ALL logged-in users."""
    market = get_or_create_market()
    buy_orders_count = Order.objects.filter(is_matched=False, order_type='BUY').count()
    sell_orders_count = Order.objects.filter(is_matched=False, order_type='SELL').count()
    total_trades = Trade.objects.count()
    recent_trades = Trade.objects.order_by('-timestamp')[:20]

    return render(request, 'trading/market_dashboard.html', {
        'market': market,
        'buy_orders_count': buy_orders_count,
        'sell_orders_count': sell_orders_count,
        'total_trades': total_trades,
        'recent_trades': recent_trades,
        'is_admin': request.user.is_superuser,
    })


@login_required
def toggle_market(request):
    """Toggle market open/close - admin only."""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Admin only'}, status=403)

    if request.method == 'POST':
        market = get_or_create_market()
        data = json.loads(request.body) if request.body else {}
        action = data.get('action', 'toggle')

        if action == 'open':
            market.is_active = True
            market.reset_daily_stats()
        elif action == 'close':
            market.is_active = False
        else:
            market.is_active = not market.is_active
            if market.is_active:
                market.reset_daily_stats()

        market.save()
        broadcast_orderbook_update()
        return JsonResponse({
            'success': True,
            'is_active': market.is_active,
            'message': f"Market {'OPENED' if market.is_active else 'CLOSED'} successfully"
        })

    return JsonResponse({'success': False, 'message': 'POST required'}, status=405)


def get_market_stats(request):
    """Get current market statistics as JSON."""
    market = get_or_create_market()
    return JsonResponse({
        'name': market.name,
        'is_active': market.is_active,
        'last_traded_price': float(market.last_traded_price) if market.last_traded_price else None,
        'total_trades': market.total_trades,
        'total_volume': market.total_volume,
        'day_high': float(market.day_high) if market.day_high else None,
        'day_low': float(market.day_low) if market.day_low else None,
        'opening_price': float(market.opening_price) if market.opening_price else None,
    })


def download_trades_csv(request):
    """Download all trades as CSV."""
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="trades.csv"'

    writer = csv.writer(response)
    writer.writerow(['Trade ID', 'Buyer', 'Seller', 'Quantity', 'Price', 'Timestamp'])

    trades = Trade.objects.all().order_by('-timestamp')
    for trade in trades:
        writer.writerow([trade.id, trade.buyer.username, trade.seller.username, trade.quantity, trade.price, trade.timestamp])

    return response


# ===========================
# Market Maker Views
# ===========================

@login_required
def market_maker_page(request):
    """Market Maker configuration and control page for regular users."""
    user = request.user
    trading_user, _ = User.objects.get_or_create(username=user.username)
    market = get_or_create_market()

    mm_config, _ = MarketMakerConfig.objects.get_or_create(
        user=trading_user,
        defaults={
            'spread_pct': Decimal('1.00'),
            'quantity': 100,
            'num_levels': 3,
        }
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save':
            try:
                ref_price_raw = request.POST.get('reference_price', '').strip()
                mm_config.reference_price = Decimal(ref_price_raw) if ref_price_raw else None
                mm_config.spread_pct = Decimal(request.POST.get('spread_pct', '1.00'))
                mm_config.quantity = int(request.POST.get('quantity', 100))
                mm_config.num_levels = min(10, max(1, int(request.POST.get('num_levels', 3))))
                mm_config.save()
                messages.success(request, 'Market Maker configuration saved.')
            except Exception as e:
                messages.error(request, f'Failed to save configuration: {e}')
            return redirect('market_maker')

        elif action == 'activate':
            if not market.is_active:
                messages.error(request, 'Cannot activate Market Maker — market is currently CLOSED.')
                return redirect('market_maker')
            try:
                _activate_market_maker(trading_user, mm_config, market)
                mm_config.is_active = True
                mm_config.save()
                messages.success(request, f'Market Maker activated — placed {mm_config.num_levels * 2} orders.')
            except Exception as e:
                messages.error(request, f'Failed to activate Market Maker: {e}')
            return redirect('market_maker')

        elif action == 'deactivate':
            try:
                _cancel_market_maker_orders(trading_user)
                mm_config.is_active = False
                mm_config.save()
                messages.success(request, 'Market Maker deactivated. All pending MM orders cancelled.')
            except Exception as e:
                messages.error(request, f'Failed to deactivate Market Maker: {e}')
            return redirect('market_maker')

    mm_orders = Order.objects.filter(user=trading_user, is_market_maker=True, is_matched=False).order_by('-order_type', 'price')
    buy_mm_orders = [o for o in mm_orders if o.order_type == 'BUY']
    sell_mm_orders = [o for o in mm_orders if o.order_type == 'SELL']

    return render(request, 'trading/market_maker.html', {
        'mm_config': mm_config,
        'market': market,
        'buy_mm_orders': buy_mm_orders,
        'sell_mm_orders': sell_mm_orders,
    })


@login_required
def market_maker_status(request):
    """JSON endpoint: return current market maker status for the logged-in user."""
    trading_user, _ = User.objects.get_or_create(username=request.user.username)
    try:
        mm_config = MarketMakerConfig.objects.get(user=trading_user)
        pending = Order.objects.filter(user=trading_user, is_market_maker=True, is_matched=False).count()
        return JsonResponse({
            'is_active': mm_config.is_active,
            'spread_pct': float(mm_config.spread_pct),
            'quantity': mm_config.quantity,
            'num_levels': mm_config.num_levels,
            'reference_price': float(mm_config.reference_price) if mm_config.reference_price else None,
            'pending_orders': pending,
        })
    except MarketMakerConfig.DoesNotExist:
        return JsonResponse({'is_active': False, 'pending_orders': 0})


def _activate_market_maker(trading_user, mm_config, market):
    """Internal helper: place limit orders based on Market Maker config."""
    # Determine the reference price
    ref_price = mm_config.reference_price
    if ref_price is None:
        if market.last_traded_price:
            ref_price = market.last_traded_price
        else:
            raise ValueError("No reference price available. Please set one or wait for a trade.")

    ref_price = Decimal(str(ref_price))
    spread = Decimal(str(mm_config.spread_pct)) / Decimal('100')
    qty = mm_config.quantity

    # Cancel existing MM orders first to avoid duplicates
    _cancel_market_maker_orders(trading_user)

    new_orders = []
    for level in range(1, mm_config.num_levels + 1):
        level_d = Decimal(str(level))
        buy_price = (ref_price * (1 - spread * level_d)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        sell_price = (ref_price * (1 + spread * level_d)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        if buy_price <= 0:
            continue

        new_orders.append(Order(
            user=trading_user,
            order_type='BUY',
            order_mode='LIMIT',
            quantity=qty,
            disclosed=qty,
            price=buy_price,
            original_quantity=qty,
            is_matched=False,
            is_market_maker=True,
        ))
        new_orders.append(Order(
            user=trading_user,
            order_type='SELL',
            order_mode='LIMIT',
            quantity=qty,
            disclosed=qty,
            price=sell_price,
            original_quantity=qty,
            is_matched=False,
            is_market_maker=True,
        ))

    Order.objects.bulk_create(new_orders)

    # Attempt to match newly created orders
    for order in Order.objects.filter(user=trading_user, is_market_maker=True, is_matched=False):
        match_order(order)

    broadcast_orderbook_update()


def _cancel_market_maker_orders(trading_user):
    """Internal helper: cancel all pending MM orders for a user."""
    Order.objects.filter(user=trading_user, is_market_maker=True, is_matched=False).delete()
    broadcast_orderbook_update()