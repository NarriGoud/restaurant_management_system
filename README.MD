# 🍽️ TablePay: Smart Dining Management System

[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)](https://www.python.org/) [![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/) [![Database](https://img.shields.io/badge/Database-MongoDB-47A248?logo=mongodb)](https://www.mongodb.com/) [![Cache](https://img.shields.io/badge/Cache-Redis-DC382D?logo=redis)](https://redis.io/)

---

## 💡 Project Overview

**TablePay** is a high-performance, full-stack web application designed to modernize restaurant operations. It provides role-based portals for **Admin**, **Cashier**, and **Kitchen** staff, leveraging a two-tier data strategy: **Redis** for real-time order updates and **MongoDB** for reliable transaction persistence.

---

## ✨ Key Features & Roles

The system is split into specialized dashboards for efficient workflow management:

| Portal | File | Core Functionality | Technologies |
| :--- | :--- | :--- | :--- |
| **👨‍💼 Admin** | `admin_dashboard.html` | **CRUD** (Create, Read, Update, Delete) for Menu Items. | HTML, JS, FastAPI API |
| **💰 Cashier** | `cashier_dashboard.html` | Order creation, bill generation, **PDF** export, and **QR Code** payment link generation. | JS (`jspdf`, `qrcodejs`) |
| **🧑‍🍳 Kitchen** | `kitchen_dashboard.html` | Real-time queue, display of orders by status (Pending, Preparing, Ready), **10-second auto-refresh**. | HTML, JS, Redis Cache |

---

## 🛠️ Architecture & Data Flow

TablePay is built on a Python **FastAPI** backend (`main.py`) using an optimized **Cache-Aside Pattern** to handle high-volume, low-latency order updates.

### Data Strategy:

* **Active Orders (High Speed):** New and in-progress orders (Pending, Preparing, Ready) are stored in the **Redis** cache (`cache.py`) for millisecond access by the Kitchen portal.  
* **Completed Orders (Persistence):** When an order is marked as **'served'**, it is logged to the **MongoDB** `ORDER_COLLECTION` for permanent records and immediately removed from Redis.

---

## 💻 Setup and Installation

### Prerequisites

Ensure you have the following services running and accessible before starting the application:

1. **Python 3.8+**  
2. **MongoDB** instance  
3. **Redis** server  

### 1. Cloning the Repository

Clone the repository to your local system:

```bash git clone https://github.com/NarriGoud/restaurant_management_system.git

### 2. Navigate to repo

Navigate to the repository:

```bash cd <repo name>

### 3. Installing Dependencies

Install all necessary Python packages using the provided requirements.txt file:

```bash pip install -r requirements.txt