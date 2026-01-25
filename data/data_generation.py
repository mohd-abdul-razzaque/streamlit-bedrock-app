from faker import Faker
import pandas as pd
import random
from datetime import datetime

fake = Faker()
random.seed(42)

# ---------------- CONFIG ----------------
NUM_CLIENTS = 5
NUM_PRODUCTS = 20
NUM_CUSTOMERS = 100
NUM_ORDERS = 300

# ---------------- CLIENTS ----------------
clients = []
regions = ["North", "South", "East", "West", "APAC", "EMEA"]

for cid in range(1, NUM_CLIENTS + 1):
    clients.append({
        "client_id": cid,
        "client_name": f"{fake.company()} Motors",
        "industry": "Automobile",
        "region": random.choice(regions),
        "country": fake.country(),
        "onboarded_date": fake.date_between(start_date="-5y", end_date="-1y")
    })

clients_df = pd.DataFrame(clients)

# ---------------- PRODUCTS (VEHICLES) ----------------
products = []
product_types = ["Sedan", "SUV", "Truck", "Hatchback"]
fuel_types = ["Petrol", "Diesel", "Electric"]

for pid in range(1, NUM_PRODUCTS + 1):
    cost = round(random.uniform(500000, 1500000), 2)
    price = round(cost * random.uniform(1.25, 1.8), 2)

    products.append({
        "product_id": pid,
        "client_id": random.randint(1, NUM_CLIENTS),
        "product_name": f"Model-{pid}",
        "product_type": random.choice(product_types),
        "fuel_type": random.choice(fuel_types),
        "unit_price": price,
        "manufacturing_cost": cost,
        "launch_year": random.randint(2018, 2025),
        "is_active": True
    })

products_df = pd.DataFrame(products)

# ---------------- CUSTOMERS ----------------
customers = []

for cust_id in range(1, NUM_CUSTOMERS + 1):
    customers.append({
        "customer_id": cust_id,
        "customer_name": fake.name(),
        "customer_type": random.choice(["Individual", "Corporate", "Fleet"]),
        "country": fake.country(),
        "created_at": fake.date_time_between(start_date="-2y", end_date="now")
    })

customers_df = pd.DataFrame(customers)

# ---------------- ORDERS ----------------
orders = []
order_items = []
sales_transactions = []

order_item_id = 1
transaction_id = 1

for order_id in range(1, NUM_ORDERS + 1):
    customer_id = random.randint(1, NUM_CUSTOMERS)
    order_date = fake.date_between(start_date="-1y", end_date="today")
    order_status = random.choice(["Booked", "Delivered", "Cancelled"])

    selected_products = random.sample(products, random.randint(1, 3))
    total_order_value = 0

    for prod in selected_products:
        quantity = random.randint(1, 5)
        line_total = round(quantity * prod["unit_price"], 2)
        total_order_value += line_total

        order_items.append({
            "order_item_id": order_item_id,
            "order_id": order_id,
            "product_id": prod["product_id"],
            "quantity": quantity,
            "unit_price": prod["unit_price"],
            "line_total": line_total
        })

        order_item_id += 1

    orders.append({
        "order_id": order_id,
        "customer_id": customer_id,
        "order_date": order_date,
        "order_status": order_status,
        "total_order_value": round(total_order_value, 2)
    })

    sales_transactions.append({
        "transaction_id": transaction_id,
        "order_id": order_id,
        "payment_mode": random.choice(["Cash", "EMI", "Lease", "Bank"]),
        "amount_paid": round(total_order_value, 2),
        "transaction_date": datetime.combine(order_date, datetime.min.time())
    })

    transaction_id += 1

orders_df = pd.DataFrame(orders)
order_items_df = pd.DataFrame(order_items)
sales_transactions_df = pd.DataFrame(sales_transactions)

# ---------------- WRITE CSV FILES ----------------
clients_df.to_csv("clients.csv", index=False)
products_df.to_csv("products.csv", index=False)
customers_df.to_csv("customers.csv", index=False)
orders_df.to_csv("orders.csv", index=False)
order_items_df.to_csv("order_items.csv", index=False)
sales_transactions_df.to_csv("sales_transactions.csv", index=False)

print("CSV files generated successfully as per finalized schema.")
