import datetime
from celery import shared_task
import redis
from django.conf import settings

# Connect to Redis
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

@shared_task
def update_daily_farmer_count(user_id):
    """Update the count of farmers added by a user for the current day."""
    today = datetime.date.today().isoformat()
    key = f"user:{user_id}:farmers:added:{today}"
    
    redis_client.incr(key)
    redis_client.expire(key, 60*24*60*60)  # 60 days in seconds
    
    return key

@shared_task
def update_block_farmer_count(block_id, increment=True):
    """Update the count of farmers in a block."""
    key = f"block:{block_id}:farmers:count"
    
    if increment:
        redis_client.incr(key)
    else:

        current = int(redis_client.get(key) or 0)
        if current > 0:
            redis_client.decr(key)
    
    return key

@shared_task
def sync_block_counts():
    """Synchronize Redis block counts with the database."""
    from .models import Block, Farmer
    
    # Get all blocks
    blocks = Block.objects.all()
    
    for block in blocks:
        # Count farmers in this block
        count = Farmer.objects.filter(block=block).count()
        
        # Update Redis
        key = f"block:{block.id}:farmers:count"
        redis_client.set(key, count)
    
    return "Block counts synchronized" 