from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from .utils import match_order

@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    if created and instance.order_mode == 'LIMIT':  # Only match LIMIT orders
        match_order(instance)