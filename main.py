# main.py
import contextlib
import os
import json 
import cache 
from datetime import datetime 
from fastapi import FastAPI, HTTPException, status, Response, Body 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from bson import ObjectId

# --- V2 Pydantic Imports ---
from pydantic_core import core_schema 
# --------------------------

class UserLogin(BaseModel): 
    portal: str
    email: str
    password: str

# --- Helper for MongoDB ObjectId/Pydantic Compatibility ---
class PyObjectId(ObjectId):
    """
    Custom type for MongoDB ObjectIds in Pydantic V2.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        
        validation_schema = core_schema.union_schema(
            [
                core_schema.is_instance_schema(ObjectId),
                core_schema.no_info_plain_validator_function(cls.validate)
            ]
        )
        
        return core_schema.json_or_python_schema(
            json_schema=validation_schema,
            python_schema=validation_schema,
            serialization=core_schema.to_string_ser_schema(), 
        )

    @classmethod
    def validate(cls, v: Any) -> ObjectId:
        """The actual validation logic for a string input."""
        if isinstance(v, ObjectId):
            return v
        if not isinstance(v, str):
            raise ValueError("ObjectId must be a string or ObjectId instance")
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId format")
        return ObjectId(v)

# --- Menu Item Data Models ---
class MenuItemBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    price: float = Field(..., gt=0)
    category: str = Field(..., max_length=50)
    menuImageUrl: Optional[str] = None
    
class MenuItemDB(MenuItemBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    class Config:
        validate_by_name = True 
        arbitrary_types_allowed = True
        populate_by_name = True 

# --- Order Data Models ---
class OrderItem(BaseModel):
    name: str
    price: float
    quantity: int

class OrderBase(BaseModel):
    table_id: str = Field(..., description="The ID of the table placing the order.")
    items: List[OrderItem]
    total_amount: float
    payment_mode: str
    status: str = Field(default="pending", description="Order status: pending, preparing, ready, served")

class OrderDB(OrderBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id") 
    created_at: datetime = Field(default_factory=datetime.now)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

class OrderStatusUpdateInput(BaseModel):
    status: str = Field(..., description="The new status: pending, preparing, ready, or served.")

class OrderCompletionResponse(BaseModel):
    message: str
    order_id: str
    total_amount: float

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "tablepay_db") 

# --- MongoDB Setup ---
if not MONGO_URI:
    MONGO_URI = "mongodb://localhost:27017" 

try:
    client = AsyncIOMotorClient(MONGO_URI) 
    db = client[DB_NAME]
except Exception as e:
    print(f"MongoDB client initialization error: {e}")
    raise e 

MENU_COLLECTION = db.menu_items
ORDER_COLLECTION = db.orders 
# ---------------------

# --- Data Seeding Function ---
async def seed_initial_data():
    """Drops existing collections, inserts DUMMY USERS, and caches existing menu items."""
    
    TEST_USERS = [
        {"portal": "admin", "email": "admin@tablepay.com", "password": "admin_pass", "name": "Lakshmi Priya"},
        {"portal": "cashier", "email": "cashier@tablepay.com", "password": "cashier_pass", "name": "Lakshmi Priya"},
        {"portal": "kitchen", "email": "kitchen@tablepay.com", "password": "kitchen_pass", "name": "Lakshmi Priya"},
    ]
    
    user_collections = [f"{user['portal']}_users" for user in TEST_USERS]
    
    print("\n--- Starting Database Seeding/Reset ---")
    
    # 1. Drop and Re-insert Users
    print("🗑️ Dropping existing USER collections...")
    for collection_name in user_collections:
        if await db.list_collection_names(filter={"name": collection_name}):
            await db[collection_name].drop() 
            print(f"   -> Dropped: {collection_name}")
            
    print("✅ Existing User data cleared.")

    # Insert Users
    inserted_count = 0
    for user_data in TEST_USERS:
        portal_name = user_data["portal"]
        collection = db[f"{portal_name}_users"] 
        insert_doc = {
            "email": user_data["email"],
            "password": user_data["password"],
            "name": user_data["name"]
        }
        await collection.insert_one(insert_doc)
        inserted_count += 1
            
    if inserted_count > 0:
        print(f"✅ DUMMY USER VALUES ({inserted_count} records) INSERTED SUCCESSFULLY!")
    
    # 2. Setup/Cache Orders and Menu
    await ORDER_COLLECTION.create_index([("created_at", 1)])
    print("✅ Ensured index on 'orders' collection.")
    
    menu_collection = db.menu_items
    inserted_menu_items_pydantic = []
    
    print("🧹 Invalidating Menu Cache and Active Orders to ensure fresh data...")
    cache.invalidate_menu_cache() 
    cache.clear_active_orders_cache() 

    async for doc in menu_collection.find():
        inserted_menu_items_pydantic.append(MenuItemDB(**doc))

    if inserted_menu_items_pydantic:
        print(f"✅ Found {len(inserted_menu_items_pydantic)} menu items in DB.")

    # 3. Cache data using the separate cache.py module
    cache.cache_initial_data(TEST_USERS)
    cache.set_menu_cache(inserted_menu_items_pydantic)
            
    print("--- FastAPI Lifespan Startup Complete ---\n")


# --- FastAPI Application Lifespan ---
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    cache.get_redis_client() 
    await seed_initial_data() 
    yield

# --- FastAPI Initialization and Middleware Setup ---
app = FastAPI(lifespan=lifespan)

origins = [
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static") 


# --- FastAPI Routes (HTML Pages) ---

@app.get("/")
async def serve_index():
    file_path = os.path.join(os.getcwd(), "static", "index.html")
    return FileResponse(file_path)

@app.post("/api/login")
async def login_user(login_data: UserLogin):
    
    portal_collection = f"{login_data.portal.lower()}_users"
    collection = db[portal_collection]

    user = await collection.find_one({"email": login_data.email})

    if user:
        db_password = user.get("password", "")
        
        if login_data.password == db_password:
            return {
                "message": f"Login successful for {login_data.portal} portal.",
                "user_id": str(user["_id"]),
                "portal": login_data.portal,
                "name": user["name"]
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
    else:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
        
@app.get("/admin_dashboard.html")
async def serve_admin_dashboard():
    file_path = os.path.join(os.getcwd(), "static", "admin_dashboard.html")
    return FileResponse(file_path)

@app.get("/cashier_dashboard.html")
async def serve_cashier_dashboard():
    file_path = os.path.join(os.getcwd(), "static", "cashier_dashboard.html")
    return FileResponse(file_path)
    
@app.get("/kitchen_dashboard.html")
async def serve_kitchen_dashboard():
    file_path = os.path.join(os.getcwd(), "static", "kitchen_dashboard.html")
    return FileResponse(file_path)


# --- MENU MANAGEMENT API ROUTES (Assumed Correct) ---

@app.get("/api/menu", response_model=List[MenuItemDB])
async def get_menu():
    cached_menu_data = cache.get_menu_cache()
    if cached_menu_data:
        return cached_menu_data

    menu_items_pydantic = []
    async for item in MENU_COLLECTION.find():
        pydantic_item = MenuItemDB(**item)
        menu_items_pydantic.append(pydantic_item)
    
    if menu_items_pydantic:
        cache.set_menu_cache(menu_items_pydantic)
            
    return menu_items_pydantic

@app.post("/api/menu", response_model=MenuItemDB, status_code=status.HTTP_201_CREATED)
async def create_menu_item(item: MenuItemBase):
    item_dict = item.model_dump(by_alias=True)
    result = await MENU_COLLECTION.insert_one(item_dict)
    
    cache.invalidate_menu_cache()
    
    created_item = await MENU_COLLECTION.find_one({"_id": result.inserted_id})
    if created_item:
        return MenuItemDB(**created_item)
    raise HTTPException(status_code=500, detail="Failed to create menu item.")

@app.put("/api/menu/{item_id}", response_model=MenuItemDB)
async def update_menu_item(item_id: str, item: MenuItemBase):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid item ID format.")
    
    update_data = item.model_dump(exclude_unset=True, by_alias=True) 
    
    result = await MENU_COLLECTION.update_one(
        {"_id": ObjectId(item_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Menu item not found.")
    
    cache.invalidate_menu_cache()
        
    updated_item = await MENU_COLLECTION.find_one({"_id": ObjectId(item_id)})
    
    if updated_item:
        return MenuItemDB(**updated_item)
    
    raise HTTPException(status_code=500, detail="Failed to retrieve updated item.")

@app.delete("/api/menu/{item_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_menu_item(item_id: str):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid item ID format.")

    result = await MENU_COLLECTION.delete_one({"_id": ObjectId(item_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Menu item not found.")
    
    cache.invalidate_menu_cache()
        
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# --------------------------------------------------------------------------
# --- ORDER MANAGEMENT API ROUTES (CRITICAL FIXES APPLIED) ---
# --------------------------------------------------------------------------

# 5. POST a new order (from Cashier Checkout) - REDIS-FIRST CREATION
@app.post("/api/order/complete", response_model=OrderCompletionResponse, status_code=status.HTTP_201_CREATED)
async def complete_order(order_data: OrderBase):
    
    # 1. Create the OrderDB object with 'pending' status.
    new_order_data = OrderDB(
        table_id=order_data.table_id, 
        items=order_data.items,
        total_amount=order_data.total_amount,
        payment_mode=order_data.payment_mode,
        status="pending"
    )
    
    order_id_str = str(new_order_data.id)
    
    # 2. Cache the result in Redis (REDIS-FIRST)
    cache.set_active_order_cache(new_order_data, order_id_str)
    
    # CRITICAL CHECK: If Redis failed to connect, cache.R is None. Stop here and fail loudly.
    if not cache.R:
        raise HTTPException(status_code=503, detail="Order system is unavailable: Redis cache connection failed. Order was not saved.")

    return {
        "message": f"Order {order_id_str} created as PENDING and stored in Redis.",
        "order_id": order_id_str,
        "total_amount": new_order_data.total_amount
    }

# 6. GET all orders (for Kitchen Dashboard) - FETCHES FROM REDIS
@app.get("/api/orders", response_model=List[OrderDB])
async def list_orders():
    """
    Fetches all active orders from Redis for display on the Kitchen Dashboard.
    """
    orders_data = cache.get_all_active_orders()
    
    active_orders = []
    for data in orders_data:
        try:
            order_model = OrderDB(**data)
            active_orders.append(order_model)
        except Exception as e:
            print(f"🚨 Failed to parse order data from Redis: {data}. Error: {e}")
            continue 
            
    return active_orders

# 7. PUT to update order status (from Kitchen Dashboard) - HANDLES REDIS UPDATE & MONGO PERSISTENCE
@app.put("/api/orders/{order_id}/status", response_model=OrderDB)
async def update_order_status(order_id: str, status_update: OrderStatusUpdateInput):
    """
    Updates the order status in Redis. 
    Persistence (MongoDB logging/Redis deletion) only occurs when status transitions to 'served'.
    """
    valid_statuses = ["pending", "preparing", "ready", "served"]
    new_status = status_update.status
    
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status: Must be one of {valid_statuses}")
        
    # 1. Fetch current order from Redis
    order_dict = cache.get_active_order_cache(order_id)
    
    is_valid_id = ObjectId.is_valid(order_id)
    
    if not order_dict:
        
        mongo_order = None
        if is_valid_id:
            # Check if the order is already in MongoDB (i.e., status 'ready' or 'served')
            mongo_order = await ORDER_COLLECTION.find_one({"_id": ObjectId(order_id)})
        
        # --- FIX: CHECK MONGO AND RAISE 409 CONFLICT ---
        if mongo_order:
            # Order found in MongoDB: It is completed.
            if new_status == "served":
                # Allow update to final 'served' status if order is found in MongoDB
                update_result = await ORDER_COLLECTION.update_one(
                    {"_id": ObjectId(order_id)},
                    {"$set": {"status": new_status}}
                )
                updated_order = await ORDER_COLLECTION.find_one({"_id": ObjectId(order_id)})
                return OrderDB(**updated_order)
            else:
                # The order is completed. This handles the race condition.
                raise HTTPException(
                    status_code=409, 
                    detail=f"Order {order_id} is already completed (status: {mongo_order['status']}) and cannot be modified by the kitchen dashboard."
                )
        # --- END 409 FIX ---
        
        # If not found in Redis AND not found in MongoDB, it's a true 404
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found in active cache or database.")


    # 2. Update status and reconstruct Pydantic model
    # order_dict is now guaranteed to exist from the Redis fetch above.
    order_dict['status'] = new_status
    updated_order_db = OrderDB(**order_dict) 
    
    # 3. Persistence check: ONLY on 'served' status, log to MongoDB and remove from cache.
    if new_status == "served":
        try:
            # Insert the final, served order into MongoDB
            order_to_insert = updated_order_db.model_dump(by_alias=True)
            await ORDER_COLLECTION.insert_one(order_to_insert)
            
            # 4. Remove the order from the temporary Redis cache
            cache.delete_active_order_cache(order_id)
            
            return updated_order_db 

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to log final order to MongoDB: {e}")

    
    # 5. For 'pending', 'preparing', or 'ready', update Redis and return
    # The 'ready' status now stays in Redis for the kitchen to see.
    cache.set_active_order_cache(updated_order_db, order_id)
    
    return updated_order_db