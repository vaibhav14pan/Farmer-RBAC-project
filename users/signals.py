from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Farmer
from .tasks import update_daily_farmer_count, update_block_farmer_count

@receiver(post_save, sender=Farmer)
def farmer_saved(sender, instance, created, **kwargs):
    """Trigger tasks when a farmer is saved."""
    if created:
        # New farmer added
        update_daily_farmer_count.delay(instance.added_by.id)
        update_block_farmer_count.delay(instance.block.id, increment=True)

@receiver(post_delete, sender=Farmer)
def farmer_deleted(sender, instance, **kwargs):
    """Trigger tasks when a farmer is deleted."""
    update_block_farmer_count.delay(instance.block.id, increment=False) 