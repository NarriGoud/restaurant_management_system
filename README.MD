# TablePay: Smart Dining Management System

## 🌟 Project Overview

**TablePay** is a full-stack web application designed to streamline operations in a modern dining environment. It provides a multi-portal interface for different restaurant roles: Admin (for menu management), Cashier (for order creation and billing), and Kitchen (for order preparation and status updates).

The system leverages a high-performance architecture using Python's **FastAPI** framework, a **Redis** caching layer for real-time order data, and **MongoDB** for reliable persistence of completed transactions.

---

## ✨ Key Features

### 💻 Multi-Portal System
A single landing page (`index.html`) provides login access to specialized dashboards for three roles:
* **Admin Dashboard** (`admin_dashboard.html`): Manages the menu with full **CRUD** (Create, Read, Update, Delete) functionality.
* **Cashier Dashboard** (`cashier_dashboard.html`): Handles new order creation, bill generation (including **PDF** export using `jspdf` and a **QR Code** using `qrcodejs`), and sending orders to the kitchen.
* **Kitchen Dashboard** (`kitchen_dashboard.html`): Displays all active orders, allows filtering by status (Pending, Preparing, Ready), and enables staff to update an order's status.

### ⚡ Caching & Persistence
* **Active Order Management**: New and in-progress orders (Pending, Preparing, Ready) are stored in **Redis** (`cache.py`) for extremely fast access and low-latency updates required by the Kitchen portal.
* **Persistent Storage**: Once an order is marked as **'served'** via the kitchen dashboard, it is logged to **MongoDB** (`main.py`) and removed from the active Redis cache to prevent data growth issues.

### ⏱️ Real-time Updates
* The Kitchen Dashboard implements an **auto-refresh mechanism** (every 10 seconds) to ensure kitchen staff always see the latest orders and status changes, improving operational efficiency.

---

## 🛠️ Technology Stack

| Component | Files | Technologies |
| :--- | :--- | :--- |
| **Backend API** | `main.py`, `cache.py` | Python, **FastAPI**, **Motor** (Async MongoDB Driver), **Redis-py**, **Pydantic** |
| **Frontend** | `index.html`, `admin_dashboard.html`, `cashier_dashboard.html`, `kitchen_dashboard.html` | **HTML5**, **CSS3** (`style.css`), **JavaScript** (`index.js`) |
| **Database** | Handled in `main.py` | **MongoDB** (for persistence) |
| **Caching** | Handled in `cache.py` | **Redis** (for active data) |
| **Client-Side Libs** | `cashier_dashboard.html` | `html2canvas`, `jspdf`, `qrcodejs` |

---

## 🏗️ Architecture & Flow

The system operates on a standard client-server model with a critical caching layer:

1.  **Login (`index.html` & `index.js`)**: Users log in, and credentials are sent to the `/api/login` endpoint in `main.py`. Successful login stores the user's role and name in `localStorage` and redirects to the correct dashboard.
2.  **Menu/User Data**: Initial configuration (like users and the menu) is handled via caching functions in `cache.py` and potentially persisted in MongoDB. The Admin dashboard uses the API to modify this data.
3.  **New Order**: The Cashier creates an order and sends it to the API, which uses `cache.py` to store the new order in **Redis** under the `active_order:` prefix.
4.  **Order Processing**: The Kitchen dashboard periodically polls the API (`fetchOrders`) which retrieves all active orders from the **Redis** cache (`get_all_active_orders` in `cache.py`).
5.  **Order Completion**: When the kitchen updates an order status to **'served'**, the API endpoint (`/api/order/{order_id}/status`) ensures the order is saved to the **MongoDB** `ORDER_COLLECTION` for permanent records and then deleted from the fast **Redis** cache.

---

## ⚙️ Setup and Installation

### Prerequisites

You must have the following running locally or accessible via network:

* **Python 3.8+**
* **MongoDB** instance
* **Redis** server

### Backend Setup

1.  **Clone the Repository (Hypothetical):**
    ```bash
    git clone <repository-url>
    cd tablepay-project
    ```
2.  **Create Environment File:**
    Create a `.env` file in the root directory and define the connection strings:
    ```env
    # .env
    REDIS_URI="redis://localhost:6379/0"
    MONGO_URI="mongodb://localhost:27017/"
    DB_NAME="TablePayDB"
    ```
3.  **Install Dependencies:**
    ```bash
    pip install fastapi uvicorn motor python-dotenv redis pydantic
    ```
4.  **Run the Server:**
    Start the FastAPI application.
    ```bash
    uvicorn main:app --reload
    ```
5.  The application will be accessible at `http://127.0.0.1:8000`.