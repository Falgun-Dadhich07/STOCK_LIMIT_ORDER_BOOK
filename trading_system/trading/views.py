from django.shortcuts import render, redirect
from .models import User, Order, Trade, Stoploss_Order
from django.db.models import Q
from django.db import transaction
from django.contrib.auth.decorators import login_required
import json
from django.contrib import messages
from .utils import broadcast_orderbook_update  # Assuming broadcast_orderbook_update is in utils.py

from .utils import match_order  # Assuming match_order is in utils.py
from django.http import JsonResponse

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        user, created = User.objects.get_or_create(username=username)
        return redirect('home', user_id=user.id)
    return render(request, 'trading/login.html')
def fetch_best_ask():
    # Fetch the best ask price (lowest available price for a buy order)
    return Order.objects.filter(order_type="SELL", is_matched=False).order_by('price').values('price', 'quantity').first()

def fetch_best_bid():
    # Fetch the best bid price (highest available price for a sell order)
    return Order.objects.filter(order_type="BUY", is_matched=False).order_by('-price').values('price', 'quantity').first()

def get_best_ask(request):
    if request.method == 'GET':
    # Fetch the best ask price (lowest available price for a buy order)
        best_ask = Order.objects.filter(order_type="SELL", is_matched=False).order_by('price').values('price', 'disclosed').first()
        return JsonResponse({'best_ask': best_ask})
    return JsonResponse({'best_ask': None})

def get_best_bid(request):
    if request.method == 'GET':
    # Fetch the best bid price (highest available price for a sell order)
        best_bid = Order.objects.filter(order_type="BUY", is_matched=False).order_by('-price').values('price', 'disclosed').first()
        return JsonResponse({'best_bid': best_bid})
    return JsonResponse({'best_bid': None})

@login_required  # Ensure the user is logged in before accessing this view
def home(request):
    user = request.user  # Get the logged-in user
    user, created = User.objects.get_or_create(username=user)

    if request.method == "POST":
        order_type = request.POST.get('order_type')
        order_mode = request.POST.get('order_mode')
        quantity = int(request.POST.get('quantity'))
        disclosed = int(request.POST.get('disclosed_quantity'))
        stoploss_order =  request.POST.get('Stoploss_order')
        target_price = request.POST.get('Target_price')
        is_ioc=request.POST.get('is_ioc')=='True'
        original_quantity=quantity

        price = None
        end_time=request.POST.get('end_time')

        if disclosed==0:
            disclosed=quantity

        try:
            if order_mode == "LIMIT":
                price = float(request.POST.get('price', 0))  # Default to 0 if no price is provided

            elif order_mode == "MARKET":
                if order_type == "BUY":
                    # Fetch the JSON response from the best ask view
                    best_ask_response = fetch_best_ask()
                    best_ask_data=best_ask_response
                    price = best_ask_data['price']

                elif order_type == "SELL":
                    # Fetch the JSON response from the best bid view
                    best_bid_response = fetch_best_bid()
                    best_bid_data=best_bid_response
                    price = best_bid_data['price']

                if price is None:
                    return render(request, 'trading/home.html', {'error': 'Unable to fetch market price for the order type.'})
                    # Create and save the new order

            if disclosed>quantity:
                disclosed=quantity

            if(stoploss_order=='NO' or stoploss_order==None):
                    # Save or process the order here
                new_order = Order(
                    order_type=order_type,
                    order_mode=order_mode,
                    quantity=quantity,
                    disclosed=disclosed,
                    price=price,
                    is_matched=False,
                    is_ioc=is_ioc,
                    user=user,  # Ensure the order is associated with the logged-in user
                    original_quantity=original_quantity

                )

                if disclosed < 0.1 * quantity:  # disclosed_quantity should not be > 10% of quantity
                    messages.error(request, "Disclosed Quantity cannot be less than 10% greater than Quantity.")

                else:
                    # Proceed with saving the order or further logic
                    messages.success(request, "Order placed successfully!")
                    print("I am here")
                    try:
                        new_order.save()
                        print("Order saved!")
                        broadcast_orderbook_update()
                        print("call1")
                        if not is_ioc:
                            match_order(new_order)
                        messages.success(request, 'Your order has been placed successfully!')
                    except Exception as e:
                        print("Error saving order:", e)
                        messages.error(request, f"Order could not be saved: {e}")
                    return redirect('/home')

            else:
                new_order = Stoploss_Order (
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

                if disclosed < 0.1 * quantity:  # disclosed_quantity should not be > 10% of quantity
                    messages.error(request, "Disclosed Quantity cannot be less than 10% greater than Quantity.")

                else:
                    # Proceed with saving the order or further logic
                    messages.success(request, "Stoploss Order placed successfully!")
                    new_order.save()
                    broadcast_orderbook_update()
                    messages.success(request, 'Your Stoploss order has been placed successfully!')
                    return redirect('/home')


        except Exception as e:
            return render(request, 'trading/home.html', {'error': 'Unable to fetch market price for the order type.'})
        


    # Fetch orders associated with the user
    orders = Order.objects.filter(user=user)  # Filter orders by the logged-in user
    trades = Trade.objects.filter(Q(buyer=user) | Q(seller=user))
    # changes:
    stoploss_orders = Stoploss_Order.objects.filter(user=user)

    execute_order()
    return render(request, 'trading/home.html', {'user': user, 'orders': orders,'trades': trades,'stoploss_orders': stoploss_orders})




from django.shortcuts import render
from .models import Order
from django.shortcuts import render
from .models import Order, Trade

def orderbook(request):
    # Retrieve unmatched buy orders (sorted by price in descending order)
    buy_orders = Order.objects.filter(is_matched=False, order_type='BUY').order_by('-price')
    # Retrieve unmatched sell orders (sorted by price in ascending order)
    sell_orders = Order.objects.filter(is_matched=False, order_type='SELL').order_by('price')
    
    # Retrieve all trades (you may filter or sort as needed)
    trades = Trade.objects.all().order_by('-timestamp')  # Sorting trades by timestamp
  
    # Display both buy and sell orders in the orderbook, along with trades
    return render(request, 'trading/orderbook.html', {
        'buy_orders': buy_orders,
        'sell_orders': sell_orders,
        'best_bid': buy_orders.first() if buy_orders else None,
        'best_ask': sell_orders.first() if sell_orders else None,
        'trades': trades  # Pass trades to the template
    })

@login_required
def modify(request):
    # Retrieve unmatched buy orders (sorted by price in descending order)
    buy_orders = Order.objects.filter(is_matched=False, order_type='BUY').order_by('-price')
    # Retrieve unmatched sell orders (sorted by price in ascending order)
    sell_orders = Order.objects.filter(is_matched=False, order_type='SELL').order_by('price')
    
    # Retrieve all trades (you may filter or sort as needed)
    trades = Trade.objects.all().order_by('-timestamp')  # Sorting trades by timestamp
    
    # Display both buy and sell orders in the orderbook, along with trades
    return render(request, 'trading/modify.html', {
        'buy_orders': buy_orders,
        'sell_orders': sell_orders,
        'best_bid': buy_orders.first() if buy_orders else None,
        'best_ask': sell_orders.first() if sell_orders else None,
        'trades': trades  # Pass trades to the template
    })

@login_required  
def modify_order_page(request):
    # Retrieve unmatched buy orders (sorted by price in descending order)
    buy_orders = Order.objects.filter(is_matched=False, order_type='BUY').order_by('-price')
    # Retrieve unmatched sell orders (sorted by price in ascending order)
    sell_orders = Order.objects.filter(is_matched=False, order_type='SELL').order_by('price')
    
    # Retrieve all trades (you may filter or sort as needed)
    trades = Trade.objects.all().order_by('-timestamp')  # Sorting trades by timestamp

    # Display both buy and sell orders in the orderbook, along with trades
    return render(request, 'trading/modify_order.html', {
        'buy_orders': buy_orders,
        'sell_orders': sell_orders,
        'trades': trades  # Pass trades to the template
    })
     
@login_required  
def update_prev_order(request):
    if request.method == 'POST':
        try:
            # Extract the order_id, quantity, and price from the JSON body
            data = json.loads(request.body)
            order_id = data.get('order_id')
            new_quantity = data.get('quantity')
            new_disclosed = data.get('disclosed_quantity')
            new_price = data.get('price')

            # Validate the order_id, new_quantity, and new_price
            order_id = int(order_id)
            new_quantity = int(new_quantity)
            new_disclosed = int(new_disclosed)
            new_price = float(new_price)
            
            print(f"Received order update: Order ID = {order_id}, Quantity = {new_quantity}, Disclosed Quantity = {new_disclosed}, Price = {new_price}")
              
            # Check if the order exists
            order = Order.objects.get(id=order_id)
            if order.is_matched == True:
                return JsonResponse({'success': False, 'message': 'Order has already been placed. No modifications allowed.'})
            if new_disclosed < new_quantity * 0.1:
                return JsonResponse({'success': False, 'message': 'Disclosed value must be greater then 10% of quantity.'})
            if new_disclosed > new_quantity:
                return JsonResponse({'success': False, 'message': 'Cannot disclose more than the quantity.'})
            if new_price <= 0:
                return JsonResponse({'success': False, 'message': 'Price must be greater than 0.'})
            
            order.quantity = new_quantity
            order.disclosed = new_disclosed
            order.price = new_price
            order.save()
            broadcast_orderbook_update()

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
    return redirect('login')

def get_buy_orders(request):
    if request.method == 'GET':
        buy_orders = Order.objects.filter(order_type='BUY', is_matched = False).values('user','price','disclosed', 'is_matched', 'id','is_ioc','quantity','original_quantity')
        return JsonResponse({'buy_orders': list(buy_orders)})

def get_sell_orders(request):
    if request.method == 'GET':
        sell_orders = Order.objects.filter(order_type='SELL', is_matched = False).values('user','price','disclosed', 'is_matched','id','is_ioc','quantity','original_quantity')
        return JsonResponse({'sell_orders': list(sell_orders)})

def get_recent_trades(request):
    if request.method == 'GET':
        recent_trades = Trade.objects.all().order_by('-timestamp')[:10].values(
            'buyer','seller', 'price', 'quantity', 'timestamp'
        )  # Adjust fields and ordering as needed
        return JsonResponse({'trades': list(recent_trades)})

import logging
logger = logging.getLogger(__name__)
@login_required
def cancel_order(request):
    if request.method == 'POST':
        try:
            logger.debug(f"Cancellation request received: {request.body}")
            # Get current user using the same pattern as order placement
            user = User.objects.get(username=request.user.username)
            
            data = json.loads(request.body)
            order_id = data.get('order_id')
            
            with transaction.atomic():
                order = Order.objects.get(
                    id=order_id,
                    user=user,
                    is_matched=False
                )
                order.delete()
            
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
        
        
    
    # changes:
    
@login_required
def cancel_stoploss_order(request):
    if request.method == 'POST':
        try:
            logger.debug(f"Stoploss cancellation request received: {request.body}")
            user = User.objects.get(username=request.user.username)
            
            data = json.loads(request.body)
            order_id = data.get('order_id')
            
            with transaction.atomic():
                order = Stoploss_Order.objects.get(
                    id=order_id,
                    user=user,
                    is_matched=False
                )
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
from django.db import transaction
from django.utils import timezone
import logging
from .models import Stoploss_Order, Order
from .views import match_order

logger = logging.getLogger(__name__)

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

@transaction.atomic
def execute_order():
    print("was called!")
    last_trade = Trade.objects.last()
    if not last_trade:
        logger.info("No last trade found.")
        return
    
    closing_price = last_trade.price
    logger.info("Last trade price: %s", closing_price)

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
    