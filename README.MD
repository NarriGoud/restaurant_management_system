# 🍽️ TablePay: Smart Dining Management System

[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Database](https://img.shields.io/badge/Database-MongoDB-47A248?logo=mongodb)](https://www.mongodb.com/)
[![Cache](https://img.shields.io/badge/Cache-Redis-DC382D?logo=redis)](https://redis.io/)

---

## 🚀 Project Goal

**TablePay** is a high-performance, full-stack web application designed to modernize restaurant operations. It provides role-based portals for **Admin**, **Cashier**, and **Kitchen** staff, using a fast caching layer (**Redis**) for real-time order updates and reliable persistence (**MongoDB**) for completed transactions.

---

## ✨ Key Features & Roles

The system is built around three distinct user experiences:

### 👨‍💼 Admin Portal (`admin_dashboard.html`)
* **Menu Management:** Full **CRUD** (Create, Read, Update, Delete) functionality for all menu items.
* **Data Control:** Handles master data, ensuring consistency across the system.

### 💰 Cashier Portal (`cashier_dashboard.html`)
* **Order Creation:** Intuitive interface for building new orders tied to a specific table ID.
* **Billing & Export:** Generates bills, including a dynamic **QR Code** and an exportable **PDF** receipt (using `jspdf` and `qrcodejs`).
* **Kitchen Submission:** Finalizes the order and sends it immediately to the Kitchen queue.

### 🧑‍🍳 Kitchen Portal (`kitchen_dashboard.html`)
* **Real-time Queue:** Displays all active orders in **Pending**, **Preparing**, and **Ready** statuses.
* **Auto-Refresh:** Automatically refreshes the order list every **10 seconds** for low-latency updates.
* **Status Updates:** Allows staff to quickly update an order's status, moving it toward completion.

---

## ⚙️ Technology Stack

| Component | Files | Technologies | Role |
| :--- | :--- | :--- | :--- |
| **Backend API** | `main.py`, `cache.py` | **FastAPI**, **Python**, **Motor**, **Pydantic** | Handles business logic and routing |
| **Caching Layer** | `cache.py` | **Redis** | Stores and retrieves *active, in-progress* orders quickly |
| **Persistence** | `main.py` | **MongoDB** | Stores *served/completed* orders permanently |
| **Frontend UI** | `.html`, `.css`, `.js` | **HTML5**, **CSS3** (`style.css`), **JavaScript** (`index.js`) | Multi-portal user interface |
| **Dependencies** | `cashier_dashboard.html` | `html2canvas`, `jspdf`, `qrcodejs` | Client-side PDF generation and QR codes |

---

## 🛠️ Architecture & Data Flow

The system uses a **Redis-as-Cache/MongoDB-as-DB** pattern for optimized performance in a high-turnover environment.

1.  **New Order Creation (Cashier)**
    * Cashier submits order via `/api/order/new`.
    * `main.py` validates the order and calls `cache.set_active_order_cache()`.
    * The new order is immediately stored in **Redis** with the status **'pending'**.

2.  **Order Processing (Kitchen)**
    * Kitchen Dashboard calls `/api/orders/active` every 10 seconds.
    * `main.py` calls `cache.get_all_active_orders()`.
    * All in-progress orders are retrieved directly from the fast **Redis** cache.

3.  **Status Change (Kitchen)**
    * Kitchen staff updates status via `/api/order/{order_id}/status`.
    * `main.py` updates the order's status in **Redis** (`cache.update_active_order_status()`).

4.  **Order Completion (Persistence)**
    * When the status is set to **'served'**:
        * `main.py` saves the final order document to the **MongoDB** `ORDER_COLLECTION`.
        * `main.py` calls `cache.delete_active_order_cache()` to remove the order from **Redis**, ensuring the cache only holds active items.

---

## 💻 Setup and Installation

### Prerequisites

Ensure you have the following services running and accessible:

* **Python 3.8+**
* **MongoDB** instance
* **Redis** server

### 1. Backend Setup

The project uses a standard `requirements.txt` for all Python dependencies.

#### A. Create `requirements.txt`
Create a file named `requirements.txt` in your project root with the following contents:

```text
# requirements.txt
fastapi
uvicorn[standard]
motor
python-dotenv
redis
pydantic