# 🍽️ Restaurant Management System – README
This project contains both backend (Python/FastAPI) and a Redis caching layer for a Restaurant Management System. The Redis cache improves performance by storing frequently accessed data, reducing load on MongoDB. The cache.py module handles Redis-based caching for menu items, users (dummy data), and active orders (for the kitchen dashboard). MongoDB is the primary database, and Redis acts as a high-speed cache layer.

Features:
- Redis Client Initialization: Connects automatically using the REDIS_URI environment variable. Safe fallback if Redis fails.
- Menu Cache: set_menu_cache(), get_menu_cache(), invalidate_menu_cache(). Key: cached_menu_items
- User Cache: dummy users stored under cached_users
- Active Orders Caching: set_active_order_cache(), get_active_order_cache(), delete_active_order_cache(), clear_active_orders_cache(), get_all_active_orders(). Uses Redis pipelines for performance.

Environment Variable:
REDIS_URI=redis://localhost:6379

Setup:
1. Install dependencies: pip install redis python-dotenv
2. Load Redis client:
   from cache import get_redis_client
   get_redis_client()

Example Usage:
- Cache Menu: set_menu_cache(menu_items)
- Get Menu: menu = get_menu_cache()
- Cache Order: set_active_order_cache(order_model, "ORDER123")
- Get All Active Orders: orders = get_all_active_orders()
- Clear Corrupted Orders (On Startup): clear_active_orders_cache()

Summary:
cache.py provides high-speed Redis caching, safe MongoDB fallback, menu caching, active order caching for the kitchen dashboard, and easy FastAPI integration. It significantly boosts performance and reduces load on MongoDB.
