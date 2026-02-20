from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from .utils import match_order

@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    if created and instance.order_mode == 'LIMIT':  # Only match LIMIT orders
        # Skip matching for market maker orders - they should be passive/resting on the book
        if instance.user_role == 'MARKET_MAKER':
            return
        match_order(instance)
