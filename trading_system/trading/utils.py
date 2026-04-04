from django.db import transaction
from django.utils import timezone
from .models import Order, Trade, MarketMaster
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def get_or_create_market():
    """Get or create the default MarketMaster instance."""
    market, _ = MarketMaster.objects.get_or_create(
        pk=1,
        defaults={'name': 'Default Market', 'is_active': True}
    )
    return market


def match_order(new_order):
    """
    Match orders with EQUAL QUANTITY ONLY.
    A trade only executes when buy and sell order quantities are exactly equal.
    No partial fills — unmatched orders remain in the book.
    """
    trades_to_create = []

    with transaction.atomic():
        market = get_or_create_market()

        # Check if market is active
        if not market.is_active:
            return

        # 1. Fetch opposite orders based on order type and mode
        if new_order.order_type == 'BUY' and new_order.order_mode == 'LIMIT':
            opposite_orders = list(Order.objects.select_for_update().filter(
                order_type='SELL',
                order_mode='LIMIT',
                price__lte=new_order.price,
                quantity=new_order.quantity,  # EQUAL QUANTITY ONLY
                is_matched=False
            ).order_by('price', 'timestamp'))

        elif new_order.order_type == 'SELL' and new_order.order_mode == 'LIMIT':
            opposite_orders = list(Order.objects.select_for_update().filter(
                order_type='BUY',
                order_mode='LIMIT',
                price__gte=new_order.price,
                quantity=new_order.quantity,  # EQUAL QUANTITY ONLY
                is_matched=False
            ).order_by('-price', 'timestamp'))

        elif new_order.order_type == 'BUY' and new_order.order_mode == 'MARKET':
            opposite_orders = list(Order.objects.select_for_update().filter(
                order_type='SELL',
                quantity=new_order.quantity,  # EQUAL QUANTITY ONLY
                is_matched=False
            ).order_by('price', 'timestamp'))

        elif new_order.order_type == 'SELL' and new_order.order_mode == 'MARKET':
            opposite_orders = list(Order.objects.select_for_update().filter(
                order_type='BUY',
                quantity=new_order.quantity,  # EQUAL QUANTITY ONLY
                is_matched=False
            ).order_by('-price', 'timestamp'))
        else:
            opposite_orders = []

        # 2. Process IOC Orders
        if new_order.is_ioc:
            if opposite_orders:
                # Take the first matching order (exact quantity match)
                opposite_order = opposite_orders[0]
                match_price = opposite_order.price

                # Create trade
                trades_to_create.append(Trade(
                    buyer=new_order.user if new_order.order_type == 'BUY' else opposite_order.user,
                    seller=opposite_order.user if new_order.order_type == 'BUY' else new_order.user,
                    quantity=new_order.quantity,
                    price=match_price,
                    timestamp=timezone.now()
                ))

                # Mark both orders as matched
                opposite_order.quantity = 0
                opposite_order.disclosed = 0
                opposite_order.is_matched = True
                opposite_order.save()

                new_order.quantity = 0
                new_order.disclosed = 0
                new_order.is_matched = True
                new_order.save()

                # Update market stats
                market.update_on_trade(match_price, new_order.original_quantity)
            else:
                # No exact match found — IOC order is cancelled (deleted)
                new_order.delete()
                broadcast_orderbook_update()
                return

        # 3. Process Normal Orders (Limit/Market) — EQUAL QUANTITY MATCHING
        else:
            if opposite_orders:
                # Take the first matching order (best price, exact quantity)
                opposite_order = opposite_orders[0]
                match_price = opposite_order.price

                # Create trade
                trades_to_create.append(Trade(
                    buyer=new_order.user if new_order.order_type == 'BUY' else opposite_order.user,
                    seller=opposite_order.user if new_order.order_type == 'BUY' else new_order.user,
                    quantity=new_order.quantity,
                    price=match_price,
                    timestamp=timezone.now()
                ))

                # Mark both orders as fully matched
                opposite_order.quantity = 0
                opposite_order.disclosed = 0
                opposite_order.is_matched = True
                opposite_order.save()

                new_order.quantity = 0
                new_order.disclosed = 0
                new_order.is_matched = True
                new_order.save()

                # Update market stats
                market.update_on_trade(match_price, new_order.original_quantity)
            else:
                # No exact match found
                if new_order.order_mode == 'MARKET':
                    # Market orders with no match are cancelled
                    new_order.quantity = 0
                    new_order.is_matched = True
                    new_order.save()
                else:
                    # Limit orders stay in the book
                    new_order.timestamp = timezone.now()
                    new_order.save()

        # 4. Bulk create trades
        if trades_to_create:
            Trade.objects.bulk_create(trades_to_create)

    # 5. Single broadcast at the end
    broadcast_orderbook_update()


def broadcast_orderbook_update():
    """Broadcast orderbook updates to all connected WebSocket clients."""
    buy_orders = Order.objects.filter(order_type='BUY', is_matched=False).order_by('-price')[:20]
    sell_orders = Order.objects.filter(order_type='SELL', is_matched=False).order_by('price')[:20]
    recent_trades = Trade.objects.order_by('-timestamp')[:10]

    best_bid = buy_orders[0] if buy_orders else None
    best_ask = sell_orders[0] if sell_orders else None

    buy_orders_list = list(buy_orders)
    sell_orders_list = list(sell_orders)
    recent_trades_list = list(recent_trades)

    # Get market stats
    try:
        market = MarketMaster.objects.get(pk=1)
        market_data = {
            'is_active': market.is_active,
            'last_traded_price': float(market.last_traded_price) if market.last_traded_price else None,
            'total_trades': market.total_trades,
            'total_volume': market.total_volume,
            'day_high': float(market.day_high) if market.day_high else None,
            'day_low': float(market.day_low) if market.day_low else None,
            'opening_price': float(market.opening_price) if market.opening_price else None,
        }
    except MarketMaster.DoesNotExist:
        market_data = None

    payload = {
        'best_bid': {
            'price': float(best_bid.price),
            'disclosed': best_bid.disclosed,
        } if best_bid else None,
        'best_ask': {
            'price': float(best_ask.price),
            'disclosed': best_ask.disclosed,
        } if best_ask else None,
        'buy_orders': [
            {
                'price': float(o.price),
                'disclosed': o.disclosed,
            } for o in buy_orders_list
        ],
        'sell_orders': [
            {
                'price': float(o.price),
                'disclosed': o.disclosed,
            } for o in sell_orders_list
        ],
        'trades': [
            {
                'buyer': t.buyer.username,
                'seller': t.seller.username,
                'price': float(t.price),
                'quantity': t.quantity,
                'timestamp': t.timestamp.isoformat(),
            } for t in recent_trades_list
        ],
        'market': market_data,
    }

    channel_layer = get_channel_layer()
    try:
        async_to_sync(channel_layer.group_send)(
            'orderbook_group',
            {
                'type': 'send_order_update',
                'payload': payload,
            }
        )
    except Exception:
        pass  # Redis may be unavailable; fail silently so orders still go through