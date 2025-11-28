# cache.py
import redis
import os
import json
from typing import Optional, List, Any
from dotenv import load_dotenv
load_dotenv()

# Get Redis URI from environment
REDIS_URI = os.getenv("REDIS_URI") 

# Global Redis client variable
R: Optional[redis.Redis] = None
REDIS_MENU_KEY = "cached_menu_items"
REDIS_USER_KEY = "cached_users"
ACTIVE_ORDER_PREFIX = "active_order:" # Prefix for all active orders

def get_redis_client():
    """Initializes and returns the global Redis client."""
    global R
    if R is not None:
        return R

    try:
        # Decode responses as strings for ease of use
        R = redis.from_url(REDIS_URI, decode_responses=True)
        R.ping() 
        print(f"✅ Redis client connected to {REDIS_URI}")
        return R
    except redis.exceptions.ConnectionError as e:
        # If connection fails, R remains None, and the main app uses MongoDB fallback
        print(f"🚨 WARNING: Could not connect to Redis at {REDIS_URI}. Caching disabled. Error: {e}")
        R = None
        return None

def set_menu_cache(menu_items_pydantic: List[Any]):
    """Caches the list of menu items in Redis."""
    if R:
        try:
            # We use model_dump_json() here because MenuItemDB uses the alias _id for MongoDB.
            menu_json = json.dumps([item.model_dump(by_alias=True) for item in menu_items_pydantic]) 
            R.set(REDIS_MENU_KEY, menu_json)
            print(f"⚡ Successfully cached {len(menu_items_pydantic)} MENU ITEMS in Redis.")
        except Exception as e:
            print(f"🚨 Failed to cache menu items: {e}")

def get_menu_cache() -> Optional[List[Any]]:
    """Retrieves the list of menu items from Redis."""
    if R:
        try:
            menu_json = R.get(REDIS_MENU_KEY)
            if menu_json:
                menu_data = json.loads(menu_json)
                # Note: Menu data is loaded back as dicts, Pydantic handles final serialization to client
                return menu_data 
        except Exception as e:
            print(f"🚨 Failed to retrieve menu items from Redis: {e}")
    return None

def invalidate_menu_cache():
    """Removes the menu cache key from Redis."""
    if R:
        try:
            R.delete(REDIS_MENU_KEY)
            print("🗑️ Redis menu cache invalidated after modification.")
        except Exception as e:
            print(f"🚨 Failed to invalidate menu cache: {e}")

def set_active_order_cache(order_db_model: Any, order_id: str):
    """
    Caches an active order in Redis using its ID as part of the key.
    The model is dumped using by_alias=True to ensure MongoDB's _id format is stored.
    """
    if R:
        try:
            # CRITICAL: Ensure the Pydantic model dumps using the MongoDB alias (_id)
            order_json = order_db_model.model_dump_json(by_alias=True) 
            R.set(ACTIVE_ORDER_PREFIX + order_id, order_json)
            # print(f"⚡ Successfully cached active order {order_id} in Redis.")
        except Exception as e:
            print(f"🚨 Failed to cache active order {order_id} in Redis: {e}")

def get_active_order_cache(order_id: str) -> Optional[dict]:
    """Retrieves a single active order dictionary by ID."""
    if R:
        try:
            order_json = R.get(ACTIVE_ORDER_PREFIX + order_id)
            if order_json:
                return json.loads(order_json)
        except Exception as e:
            print(f"🚨 Failed to retrieve active order {order_id} from Redis: {e}")
    return None

def delete_active_order_cache(order_id: str):
    """Deletes a single active order from Redis."""
    if R:
        try:
            R.delete(ACTIVE_ORDER_PREFIX + order_id)
            print(f"🗑️ Deleted active order {order_id} from Redis cache.")
        except Exception as e:
            print(f"🚨 Failed to delete order {order_id} from Redis: {e}")

# NEW FUNCTION TO CLEAR CORRUPTED ORDERS ON STARTUP
def clear_active_orders_cache():
    """
    Clears all active orders from Redis on startup to avoid corrupt data issues.
    """
    if R:
        try:
            keys = R.keys(ACTIVE_ORDER_PREFIX + '*')
            if keys:
                R.delete(*keys)
                print(f"🧹 Cleared {len(keys)} active orders from Redis.")
            else:
                print("🧹 No active orders to clear from Redis.")
        except Exception as e:
            print(f"🚨 Failed to clear active orders cache: {e}")


def get_all_active_orders() -> List[dict]:
    """
    Retrieves all currently active orders for the Kitchen Dashboard by listing keys.
    """
    orders = []
    if R:
        try:
            # Use keys for simplicity. In production, R.scan_iter() is better for large DBs.
            keys = R.keys(ACTIVE_ORDER_PREFIX + '*')
            
            # Use a pipeline for efficient retrieval of multiple keys
            pipe = R.pipeline()
            for key in keys:
                pipe.get(key)
            
            results = pipe.execute()
            
            for order_json in results:
                if order_json:
                    # Returns a dictionary, where ID field is stored as '_id'
                    orders.append(json.loads(order_json))
        except Exception as e:
            print(f"🚨 Failed to retrieve active orders from Redis: {e}")
    return orders

def cache_initial_data(test_users: List[dict]):
    """Caches the initial dummy users data (optional, but good for logging)."""
    if R:
        try:
            # Cache Users (DUMMY DATA)
            user_json = json.dumps(test_users)
            R.set(REDIS_USER_KEY, user_json)
            print(f"⚡ Successfully cached {len(test_users)} DUMMY USERS in Redis under key: {REDIS_USER_KEY}")
        except Exception as e:
            print(f"🚨 Failed to cache initial user data: {e}")