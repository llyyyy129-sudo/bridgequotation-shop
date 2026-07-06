from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from database import engine, SessionLocal
from models import Product, User, Order, PricingSetting, Base

from reportlab.lib.pagesizes import A4

from io import BytesIO
from datetime import datetime

from sqlalchemy import text, inspect
import json


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

Base.metadata.create_all(bind=engine)


# =========================
# AUTO DATABASE MIGRATION
# =========================

def column_exists(table_name, column_name):
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    return any(column["name"] == column_name for column in columns)


def add_column_if_missing(table_name, column_name, column_sql):
    try:
        if not column_exists(table_name, column_name):
            with engine.connect() as conn:
                conn.execute(text(f"""
                    ALTER TABLE {table_name}
                    ADD COLUMN {column_name} {column_sql};
                """))
                conn.commit()
                print(f"Added column: {table_name}.{column_name}")
    except Exception as e:
        print(f"Migration skipped for {table_name}.{column_name}:", e)


def run_migrations():
    add_column_if_missing(
        "users",
        "role",
        "VARCHAR DEFAULT 'customer'"
    )

    add_column_if_missing(
        "users",
        "assigned_sales",
        "VARCHAR DEFAULT 'BILL'"
    )

    add_column_if_missing(
        "users",
        "company_name",
        "VARCHAR DEFAULT ''"
    )

    add_column_if_missing(
        "users",
        "email",
        "VARCHAR DEFAULT ''"
    )

    add_column_if_missing(
        "users",
        "account_type",
        "VARCHAR DEFAULT 'customer'"
    )

    add_column_if_missing(
        "users",
        "approval_status",
        "VARCHAR DEFAULT 'Approved'"
    )

    add_column_if_missing(
        "users",
        "customer_level",
        "VARCHAR DEFAULT 'A'"
    )

    add_column_if_missing(
        "products",
        "image_2",
        "VARCHAR DEFAULT ''"
    )

    add_column_if_missing(
        "products",
        "image_3",
        "VARCHAR DEFAULT ''"
    )

    add_column_if_missing(
        "products",
        "image_4",
        "VARCHAR DEFAULT ''"
    )

    add_column_if_missing(
        "products",
        "image_5",
        "VARCHAR DEFAULT ''"
    )

    add_column_if_missing(
        "products",
        "image_6",
        "VARCHAR DEFAULT ''"
    )

    add_column_if_missing(
        "products",
        "video",
        "VARCHAR DEFAULT ''"
    )

    add_column_if_missing(
        "products",
        "packing",
        "VARCHAR DEFAULT ''"
    )

    add_column_if_missing(
        "orders",
        "sales_username",
        "VARCHAR DEFAULT 'BILL'"
    )

    add_column_if_missing(
        "orders",
        "status",
        "VARCHAR DEFAULT 'Pending'"
    )

    add_column_if_missing(
        "orders",
        "created_at",
        "VARCHAR DEFAULT ''"
    )

    add_column_if_missing(
        "orders",
        "return_comment",
        "VARCHAR DEFAULT ''"
    )


run_migrations()


def ensure_orange_admin():
    db = SessionLocal()

    orange = db.query(User).filter(
        User.username == "orange"
    ).first()

    if orange:
        orange.role = "admin"
        orange.account_type = "employee"
        orange.approval_status = "Approved"
        orange.assigned_sales = ""
        orange.company_name = orange.company_name or "COPEC"
        db.commit()
        db.close()
        return

    orange = User(
        username="orange",
        password="Orange123456",
        role="admin",
        assigned_sales="",
        company_name="COPEC",
        email="",
        account_type="employee",
        approval_status="Approved"
    )

    db.add(orange)
    db.commit()
    db.close()


ensure_orange_admin()


def ensure_pricing_setting():
    db = SessionLocal()

    setting = db.query(PricingSetting).filter(
        PricingSetting.id == 1
    ).first()

    if not setting:
        setting = PricingSetting(
            id=1,
            b_multiplier=1.2
        )
        db.add(setting)
        db.commit()

    db.close()


ensure_pricing_setting()


def get_b_multiplier(db):
    setting = db.query(PricingSetting).filter(
        PricingSetting.id == 1
    ).first()

    if not setting:
        setting = PricingSetting(
            id=1,
            b_multiplier=1.2
        )
        db.add(setting)
        db.commit()

    return float(setting.b_multiplier or 1.2)


def get_price_multiplier(db, username=None):
    if not username:
        return 1.0

    user = db.query(User).filter(
        User.username == username
    ).first()

    if not user:
        return 1.0

    level = (user.customer_level or "A").upper()

    if level == "B":
        return get_b_multiplier(db)

    return 1.0


def apply_price_multiplier(value, multiplier):
    if value is None:
        return value

    try:
        return round(float(value) * float(multiplier), 2)
    except Exception:
        return value




def safe_load_order_items(raw_items):
    if not raw_items:
        return []

    if isinstance(raw_items, list):
        return raw_items

    try:
        loaded = json.loads(raw_items)
        if isinstance(loaded, list):
            return loaded
        return []
    except Exception:
        return []


def normalize_order_items(order):
    items = safe_load_order_items(order.items)

    for item in items:
        if not isinstance(item, dict):
            continue

        current_status = item.get("item_status")

        if not current_status:
            if order.status == "Confirmed":
                current_status = "Confirmed"
            elif order.status in ["Returned", "Rejected"]:
                current_status = "Returned"
            else:
                current_status = "Pending"

            item["item_status"] = current_status

        if "item_return_comment" not in item:
            if current_status == "Returned":
                item["item_return_comment"] = order.return_comment or ""
            else:
                item["item_return_comment"] = ""

    return items


def recalculate_order_status(order, items):
    statuses = []

    for item in items:
        if not isinstance(item, dict):
            continue

        statuses.append(item.get("item_status", "Pending"))

    if not statuses:
        order.status = "Pending"
        order.return_comment = ""
        order.items = json.dumps(items)
        return

    if all(status == "Confirmed" for status in statuses):
        order.status = "Confirmed"
    elif all(status == "Returned" for status in statuses):
        order.status = "Returned"
    elif any(status == "Pending" for status in statuses):
        order.status = "Pending"
    else:
        # Mixed confirmed + returned, no pending products left.
        # The order is finished, but item details still show which products were returned.
        order.status = "Confirmed"

    return_comments = []

    for item in items:
        if not isinstance(item, dict):
            continue

        if item.get("item_status") == "Returned":
            comment = item.get("item_return_comment", "").strip()
            if comment:
                product_name = item.get("name", "Product")
                return_comments.append(f"{product_name}: {comment}")

    order.return_comment = "; ".join(return_comments)
    order.items = json.dumps(items)


def serialize_product(product, multiplier=1.0):
    return {
        "id": product.id,
        "name": product.name,
        "price": apply_price_multiplier(product.price, multiplier),
        "description": product.description,
        "image": product.image,
        "image_2": product.image_2,
        "image_3": product.image_3,
        "image_4": product.image_4,
        "image_5": product.image_5,
        "image_6": product.image_6,
        "gallery_images": [
            image for image in [
                product.image,
                product.image_2,
                product.image_3,
                product.image_4,
                product.image_5,
                product.image_6
            ]
            if image and str(image).strip()
        ],
        "video": product.video,
        "packing": product.packing,
        "moq": product.moq,
        "material": product.material,
        "volume": product.volume,
        "size": product.size,
        "price_500": apply_price_multiplier(product.price_500, multiplier),
        "price_1000": apply_price_multiplier(product.price_1000, multiplier),
        "price_3000": apply_price_multiplier(product.price_3000, multiplier),
        "price_10000": apply_price_multiplier(product.price_10000, multiplier),
        "price_50000": apply_price_multiplier(product.price_50000, multiplier),
        "category": product.category
    }



try:
    from seed import seed_products
    seed_products()
except Exception as e:
    print("Seed products skipped:", e)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# PAGE ROUTES
# =========================

@app.get("/")
def root():
    return FileResponse("templates/login.html")


@app.get("/login.html")
def login_page():
    return FileResponse("templates/login.html")


@app.get("/register.html")
def register_page():
    return FileResponse("templates/register.html")


@app.get("/change_password.html")
def change_password_page():
    return FileResponse("templates/change_password.html")


@app.get("/account_status.html")
def account_status_page():
    return FileResponse("templates/account_status.html")


@app.get("/products.html")
def products_page():
    return FileResponse("templates/products.html")


@app.get("/product.html")
def product_page():
    return FileResponse("templates/product.html")


@app.get("/cart.html")
def cart_page():
    return FileResponse("templates/cart.html")


@app.get("/my_orders.html")
def my_orders_page():
    return FileResponse("templates/my_orders.html")


@app.get("/share.html")
def share_page():
    return FileResponse("templates/share.html")


@app.get("/sales.html")
def sales_page():
    return FileResponse("templates/sales.html")


@app.get("/admin.html")
def admin_page():
    return FileResponse("templates/admin.html")


# =========================
# PRODUCTS
# =========================

@app.get("/products")
def get_products(username: str = ""):
    db = SessionLocal()

    multiplier = get_price_multiplier(db, username)
    products = db.query(Product).all()

    result = [
        serialize_product(product, multiplier)
        for product in products
    ]

    db.close()
    return result


@app.get("/products/{product_id}")
def get_product(product_id: int, username: str = ""):
    db = SessionLocal()

    multiplier = get_price_multiplier(db, username)

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        db.close()
        return {
            "error": "Product not found"
        }

    result = serialize_product(product, multiplier)

    db.close()
    return result




# =========================
# AUTH
# =========================

@app.post("/register")
def register(user: dict):
    db = SessionLocal()

    username = user.get("username", "").strip()
    password = user.get("password", "").strip()
    company_name = user.get("company_name", "").strip()
    email = user.get("email", "").strip()
    account_type = user.get("account_type", "customer").strip()

    if not username or not password or not company_name or not email:
        db.close()
        return {
            "success": False,
            "message": "Please fill in username, password, company name and email."
        }

    if len(password) < 8:
        db.close()
        return {
            "success": False,
            "message": "Password must be at least 8 characters."
        }

    if account_type not in ["customer", "employee"]:
        db.close()
        return {
            "success": False,
            "message": "Invalid account type."
        }

    existing_username = db.query(User).filter(
        User.username == username
    ).first()

    if existing_username:
        db.close()
        return {
            "success": False,
            "message": "Username already exists!"
        }

    existing_email = db.query(User).filter(
        User.email == email
    ).first()

    if existing_email:
        db.close()
        return {
            "success": False,
            "message": "Email already exists!"
        }

    if account_type == "employee":
        role = "sales"
        assigned_sales = ""
    else:
        role = "customer"
        assigned_sales = "BILL"

    new_user = User(
        username=username,
        password=password,
        role=role,
        assigned_sales=assigned_sales,
        company_name=company_name,
        email=email,
        account_type=account_type,
        approval_status="Pending",
        customer_level="A"
    )

    db.add(new_user)
    db.commit()
    db.close()

    return {
        "success": True,
        "message": "Registration submitted. Please wait for admin approval."
    }


@app.post("/login")
def login(user: dict):
    db = SessionLocal()

    username = user.get("username", "").strip()
    password = user.get("password", "").strip()

    existing = db.query(User).filter(
        User.username == username,
        User.password == password
    ).first()

    if not existing:
        db.close()
        return {
            "success": False,
            "message": "Invalid username or password"
        }

    approval_status = existing.approval_status or "Approved"

    if approval_status == "Pending":
        result = {
            "success": False,
            "message": "Your account is waiting for admin approval.",
            "username": existing.username,
            "role": existing.role,
            "account_type": existing.account_type,
            "approval_status": "Pending",
            "company_name": existing.company_name,
            "email": existing.email
        }
        db.close()
        return result

    if approval_status == "Rejected":
        result = {
            "success": False,
            "message": "Your registration request has been rejected.",
            "username": existing.username,
            "role": existing.role,
            "account_type": existing.account_type,
            "approval_status": "Rejected",
            "company_name": existing.company_name,
            "email": existing.email
        }
        db.close()
        return result

    result = {
        "success": True,
        "message": "Login successful!",
        "username": existing.username,
        "role": existing.role,
        "assigned_sales": existing.assigned_sales,
        "account_type": existing.account_type,
        "approval_status": approval_status,
        "company_name": existing.company_name,
        "email": existing.email,
        "customer_level": existing.customer_level
    }

    db.close()
    return result


@app.post("/change-password")
def change_password(data: dict):
    db = SessionLocal()

    username = data.get("username", "").strip()
    current_password = data.get("current_password", "").strip()
    new_password = data.get("new_password", "").strip()

    if not username or not current_password or not new_password:
        db.close()
        return {
            "success": False,
            "message": "Please fill in username, current password and new password."
        }

    if len(new_password) < 6:
        db.close()
        return {
            "success": False,
            "message": "New password must be at least 6 characters."
        }

    user = db.query(User).filter(
        User.username == username,
        User.password == current_password
    ).first()

    if not user:
        db.close()
        return {
            "success": False,
            "message": "Invalid username or current password."
        }

    user.password = new_password

    db.commit()
    db.close()

    return {
        "success": True,
        "message": "Password updated successfully. Please log in again."
    }


# =========================
# ADMIN USER APPROVAL
# =========================

def serialize_user(u):
    return {
        "id": u.id,
        "username": u.username,
        "company_name": u.company_name,
        "email": u.email,
        "account_type": u.account_type,
        "role": u.role,
        "assigned_sales": u.assigned_sales,
        "approval_status": u.approval_status,
        "customer_level": u.customer_level
    }


@app.get("/admin/users")
def get_all_users():
    db = SessionLocal()

    users = db.query(User).order_by(User.id.desc()).all()
    result = [serialize_user(u) for u in users]

    db.close()
    return result


@app.get("/admin/users/pending")
def get_pending_users():
    db = SessionLocal()

    users = db.query(User).filter(
        User.approval_status == "Pending"
    ).order_by(User.id.desc()).all()

    result = [serialize_user(u) for u in users]

    db.close()
    return result


@app.post("/admin/users/{user_id}/approve")
def approve_user(user_id: int):
    db = SessionLocal()

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        db.close()
        return {
            "success": False,
            "message": "User not found."
        }

    username = user.username

    user.approval_status = "Approved"

    if user.account_type == "employee":
        user.role = "sales"
        user.assigned_sales = ""
    else:
        user.role = "customer"
        user.assigned_sales = "BILL"
        user.customer_level = user.customer_level or "A"

    db.commit()
    db.close()

    return {
        "success": True,
        "message": f"{username} has been approved."
    }


@app.post("/admin/users/{user_id}/reject")
def reject_user(user_id: int):
    db = SessionLocal()

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        db.close()
        return {
            "success": False,
            "message": "User not found."
        }

    username = user.username

    if username == "orange":
        db.close()
        return {
            "success": False,
            "message": "Admin user cannot be rejected."
        }

    user.approval_status = "Rejected"

    db.commit()
    db.close()

    return {
        "success": True,
        "message": f"{username} has been rejected."
    }




@app.get("/admin/sales-users")
def get_sales_users():
    db = SessionLocal()

    users = db.query(User).filter(
        User.role == "sales",
        User.approval_status == "Approved"
    ).order_by(User.username.asc()).all()

    result = [
        {
            "id": u.id,
            "username": u.username,
            "company_name": u.company_name,
            "email": u.email
        }
        for u in users
        if u.username != "orange"
    ]

    db.close()
    return result



@app.get("/admin/pricing")
def get_admin_pricing():
    db = SessionLocal()

    setting = db.query(PricingSetting).filter(
        PricingSetting.id == 1
    ).first()

    if not setting:
        setting = PricingSetting(
            id=1,
            b_multiplier=1.2
        )
        db.add(setting)
        db.commit()

    result = {
        "success": True,
        "b_multiplier": float(setting.b_multiplier or 1.2),
        "b_percentage": round(float(setting.b_multiplier or 1.2) * 100, 2)
    }

    db.close()
    return result


@app.post("/admin/pricing")
def update_admin_pricing(data: dict):
    db = SessionLocal()

    try:
        percentage = float(data.get("b_percentage", 120))
    except Exception:
        percentage = 120

    if percentage < 100:
        db.close()
        return {
            "success": False,
            "message": "B Class percentage cannot be lower than 100%."
        }

    if percentage > 300:
        db.close()
        return {
            "success": False,
            "message": "B Class percentage cannot be higher than 300%."
        }

    setting = db.query(PricingSetting).filter(
        PricingSetting.id == 1
    ).first()

    if not setting:
        setting = PricingSetting(
            id=1,
            b_multiplier=percentage / 100
        )
        db.add(setting)
    else:
        setting.b_multiplier = percentage / 100

    db.commit()
    db.close()

    return {
        "success": True,
        "message": f"B Class price percentage updated to {percentage}%."
    }


@app.post("/admin/customers/{customer_id}/level")
def update_customer_level(customer_id: int, data: dict):
    db = SessionLocal()

    customer = db.query(User).filter(
        User.id == customer_id
    ).first()

    if not customer:
        db.close()
        return {
            "success": False,
            "message": "Customer not found."
        }

    if customer.role != "customer":
        db.close()
        return {
            "success": False,
            "message": "Only customer users can have customer level."
        }

    level = data.get("customer_level", "A").strip().upper()

    if level not in ["A", "B"]:
        db.close()
        return {
            "success": False,
            "message": "Customer level must be A or B."
        }

    customer_username = customer.username
    customer.customer_level = level

    db.commit()
    db.close()

    return {
        "success": True,
        "message": f"{customer_username} customer level updated to {level}."
    }

@app.post("/admin/customers/{customer_id}/assign-sales")
def assign_sales_to_customer(customer_id: int, data: dict):
    db = SessionLocal()

    customer = db.query(User).filter(
        User.id == customer_id
    ).first()

    if not customer:
        db.close()
        return {
            "success": False,
            "message": "Customer not found."
        }

    if customer.role != "customer":
        db.close()
        return {
            "success": False,
            "message": "Only customer users can be assigned to sales."
        }

    sales_username = data.get("sales_username", "").strip()

    if not sales_username:
        db.close()
        return {
            "success": False,
            "message": "Please choose a sales user."
        }

    sales_user = db.query(User).filter(
        User.username == sales_username,
        User.role == "sales",
        User.approval_status == "Approved"
    ).first()

    if not sales_user:
        db.close()
        return {
            "success": False,
            "message": "Sales user not found or not approved."
        }

    customer_username = customer.username

    customer.assigned_sales = sales_username

    # Demo-friendly behavior:
    # move this customer's existing orders to the newly assigned sales.
    orders = db.query(Order).filter(
        Order.username == customer_username
    ).all()

    for order in orders:
        order.sales_username = sales_username

    db.commit()
    db.close()

    return {
        "success": True,
        "message": f"{customer_username} has been assigned to {sales_username}."
    }

@app.post("/admin/users/{user_id}/change-password")
def change_user_password(user_id: int, data: dict):
    db = SessionLocal()

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        db.close()
        return {
            "success": False,
            "message": "User not found."
        }

    username = user.username

    if user.approval_status != "Approved":
        db.close()
        return {
            "success": False,
            "message": "Only approved users can change password."
        }

    new_password = data.get("password", "").strip()

    if not new_password:
        db.close()
        return {
            "success": False,
            "message": "Password cannot be empty."
        }

    if len(new_password) < 6:
        db.close()
        return {
            "success": False,
            "message": "Password must be at least 6 characters."
        }

    user.password = new_password

    db.commit()
    db.close()

    return {
        "success": True,
        "message": f"Password for {username} has been updated."
    }

@app.post("/admin/users/{user_id}/delete")
def delete_user(user_id: int):
    db = SessionLocal()

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        db.close()
        return {
            "success": False,
            "message": "User not found."
        }

    username = user.username

    if username == "orange":
        db.close()
        return {
            "success": False,
            "message": "Admin user cannot be deleted."
        }

    db.delete(user)
    db.commit()
    db.close()

    return {
        "success": True,
        "message": f"{username} has been deleted."
    }


# =========================
# ORDERS
# =========================

@app.post("/create-order")
def create_order(data: dict):
    db = SessionLocal()

    order_username = (
        data.get("order_username") or
        data.get("customer_username") or
        data.get("username")
    )

    if not order_username:
        db.close()
        return {
            "success": False,
            "message": "Customer username is required."
        }

    customer = db.query(User).filter(
        User.username == order_username
    ).first()

    assigned_sales = "BILL"

    if customer and customer.assigned_sales:
        assigned_sales = customer.assigned_sales

    # Sales users can create an order for a customer.
    # In that case, the order still belongs to the customer,
    # but sales_username is the current sales account.
    if data.get("sales_username"):
        assigned_sales = data.get("sales_username")

    items = data.get("items", [])

    for item in items:
        if isinstance(item, dict):
            item["item_status"] = "Pending"
            item["item_return_comment"] = ""

    order = Order(
        username=order_username,
        sales_username=assigned_sales,
        items=json.dumps(items),
        total=data["total"],
        status="Pending",
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        return_comment=""
    )

    db.add(order)
    db.commit()
    db.close()

    return {
        "success": True,
        "message": "Order created successfully!"
    }


@app.get("/sales/orders/{sales_username}")
def get_sales_orders(sales_username: str):
    db = SessionLocal()

    orders = db.query(Order).filter(
        Order.sales_username == sales_username
    ).all()

    result = []

    for order in orders:
        items = normalize_order_items(order)

        result.append({
            "id": order.id,
            "username": order.username,
            "customer": order.username,
            "sales_username": order.sales_username,
            "total": order.total,
            "status": order.status,
            "created_at": order.created_at,
            "return_comment": order.return_comment,
            "items": json.dumps(items)
        })

    db.close()
    return result


@app.post("/sales/orders/{order_id}/items/{item_index}/confirm")
def confirm_order_item(order_id: int, item_index: int):
    db = SessionLocal()

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:
        db.close()
        return {
            "success": False,
            "message": "Order not found."
        }

    items = normalize_order_items(order)

    if item_index < 0 or item_index >= len(items):
        db.close()
        return {
            "success": False,
            "message": "Product item not found."
        }

    items[item_index]["item_status"] = "Confirmed"
    items[item_index]["item_return_comment"] = ""

    recalculate_order_status(order, items)

    db.commit()
    db.close()

    return {
        "success": True,
        "message": "Product confirmed successfully!"
    }


@app.post("/sales/orders/{order_id}/items/{item_index}/return")
def return_order_item(order_id: int, item_index: int, data: dict):
    db = SessionLocal()

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:
        db.close()
        return {
            "success": False,
            "message": "Order not found."
        }

    return_comment = data.get("return_comment", "").strip()

    if not return_comment:
        db.close()
        return {
            "success": False,
            "message": "Please enter a return comment first."
        }

    items = normalize_order_items(order)

    if item_index < 0 or item_index >= len(items):
        db.close()
        return {
            "success": False,
            "message": "Product item not found."
        }

    items[item_index]["item_status"] = "Returned"
    items[item_index]["item_return_comment"] = return_comment

    recalculate_order_status(order, items)

    db.commit()
    db.close()

    return {
        "success": True,
        "message": "Product returned successfully!"
    }


@app.post("/sales/orders/{order_id}/confirm")
def confirm_order(order_id: int):
    db = SessionLocal()

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:
        db.close()
        return {
            "success": False,
            "message": "Order not found"
        }

    items = normalize_order_items(order)

    for item in items:
        if isinstance(item, dict):
            item["item_status"] = "Confirmed"
            item["item_return_comment"] = ""

    recalculate_order_status(order, items)

    db.commit()
    db.close()

    return {
        "success": True,
        "message": "Order confirmed successfully!"
    }


@app.post("/sales/orders/{order_id}/reject")
@app.post("/sales/orders/{order_id}/return")
def return_order(order_id: int, data: dict):
    db = SessionLocal()

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:
        db.close()
        return {
            "success": False,
            "message": "Order not found"
        }

    return_comment = data.get("return_comment", "").strip()

    if not return_comment:
        db.close()
        return {
            "success": False,
            "message": "Please enter a return comment first."
        }

    items = normalize_order_items(order)

    for item in items:
        if isinstance(item, dict):
            item["item_status"] = "Returned"
            item["item_return_comment"] = return_comment

    recalculate_order_status(order, items)

    db.commit()
    db.close()

    return {
        "success": True,
        "message": "Order returned successfully!"
    }


@app.get("/customer/info/{username}")
def get_customer_info(username: str):
    db = SessionLocal()

    user = db.query(User).filter(
        User.username == username
    ).first()

    if not user:
        db.close()
        return {
            "success": False,
            "message": "User not found."
        }

    result = {
        "success": True,
        "username": user.username,
        "role": user.role,
        "account_type": user.account_type,
        "company_name": user.company_name,
        "email": user.email,
        "assigned_sales": user.assigned_sales,
        "approval_status": user.approval_status,
        "customer_level": user.customer_level
    }

    db.close()
    return result


@app.get("/customer/orders/{username}")
def get_customer_orders(username: str):
    db = SessionLocal()

    orders = db.query(Order).filter(
        Order.username == username
    ).all()

    result = []

    for order in orders:
        items = normalize_order_items(order)

        result.append({
            "id": order.id,
            "status": order.status,
            "total": order.total,
            "created_at": order.created_at,
            "return_comment": order.return_comment,
            "items": json.dumps(items)
        })

    db.close()
    return result


@app.post("/customer/orders/{order_id}/delete")
def delete_customer_order(order_id: int, data: dict):
    db = SessionLocal()

    username = data.get("username", "").strip()

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:
        db.close()
        return {
            "success": False,
            "message": "Order not found."
        }

    if order.username != username:
        db.close()
        return {
            "success": False,
            "message": "You can only delete your own orders."
        }

    db.delete(order)
    db.commit()
    db.close()

    return {
        "success": True,
        "message": f"Order #{order_id} has been deleted."
    }


# =========================
# PDF QUOTATION
# =========================

@app.post("/cart/pdf")
async def generate_cart_pdf(data: dict):

    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
        Image
    )
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.utils import ImageReader
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from pathlib import Path as LocalPath

    items = data.get("items", [])

    customer_name = data.get("customerName", "")
    customer_company = data.get("customerCompany", "")
    customer_email = data.get("customerEmail", "")
    username = data.get("username", "")

    try:
        valid_days = int(data.get("validDays", 30))
    except Exception:
        valid_days = 30

    if valid_days <= 0:
        valid_days = 30

    # Get assigned sales contact from the logged-in customer account.
    sales_name = ""
    sales_email = ""

    db = SessionLocal()

    try:
        customer_user = db.query(User).filter(
            User.username == username
        ).first()

        assigned_sales = ""

        if customer_user:
            assigned_sales = customer_user.assigned_sales or ""

        if assigned_sales:
            sales_user = db.query(User).filter(
                User.username == assigned_sales
            ).first()

            sales_name = assigned_sales

            if sales_user:
                sales_name = sales_user.username or assigned_sales
                sales_email = sales_user.email or ""

    finally:
        db.close()

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=24,
        leftMargin=24,
        topMargin=24,
        bottomMargin=24
    )

    elements = []
    styles = getSampleStyleSheet()

    normal_style = styles["Normal"]

    small_style = ParagraphStyle(
        "SmallText",
        parent=styles["Normal"],
        fontSize=9,
        leading=11
    )

    small_center_style = ParagraphStyle(
        "SmallCenterText",
        parent=small_style,
        alignment=TA_CENTER
    )

    logo = Image(
        "static/image/bg2.jpg",
        width=420,
        height=70
    )
    logo.hAlign = "CENTER"

    elements.append(logo)
    elements.append(Spacer(1, 18))

    title = Paragraph(
        "<font size=24><b>QUOTATION</b></font>",
        styles["Title"]
    )

    elements.append(title)
    elements.append(Spacer(1, 14))

    quote_customer_info = Paragraph(
        f"""
        <font size=11>
        <b>Quotation No:</b> BQ-{datetime.now().strftime('%Y%m%d%H%M')}<br/>
        <b>Website:</b> bridgequotation.com<br/>
        <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}<br/>
        <b>Valid Until:</b> {valid_days} days<br/><br/>

        <b>Customer:</b> {customer_name}<br/>
        <b>Company:</b> {customer_company}<br/>
        <b>Email:</b> {customer_email}
        </font>
        """,
        normal_style
    )

    sales_info = Paragraph(
        f"""
        <font size=11>
        <b>Sales Contact</b><br/><br/>
        <b>Name:</b> {sales_name or "Not assigned"}<br/>
        <b>Email:</b> {sales_email or ""}
        </font>
        """,
        normal_style
    )

    info_table = Table(
        [[quote_customer_info, sales_info]],
        colWidths=[330, 180]
    )

    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.25, colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    elements.append(info_table)
    elements.append(Spacer(1, 18))

    table_data = [
        [
            "Image",
            "Product",
            "MOQ",
            "Material",
            "Size",
            "Packing",
            "Qty",
            "Unit Price",
            "Amount"
        ]
    ]

    def money(value):
        return "${:,.2f}".format(float(value))

    def make_text(value, center=False, raw_html=False):
        if value is None:
            value = ""

        if raw_html:
            text = str(value)
        else:
            text = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        if center:
            return Paragraph(text, small_center_style)

        return Paragraph(text, small_style)

    def make_product_image(image_url):
        if not image_url:
            return make_text("No Image", center=True)

        image_path = str(image_url)

        if image_path.startswith("/"):
            image_path = "." + image_path

        local_path = LocalPath(image_path)

        if not local_path.exists():
            return make_text("No Image", center=True)

        try:
            reader = ImageReader(str(local_path))
            img_width, img_height = reader.getSize()

            max_width = 48
            max_height = 48

            scale = min(max_width / img_width, max_height / img_height)

            draw_width = img_width * scale
            draw_height = img_height * scale

            product_image = Image(
                str(local_path),
                width=draw_width,
                height=draw_height
            )

            product_image.hAlign = "CENTER"

            return product_image

        except Exception:
            return make_text("No Image", center=True)

    grand_total = 0

    for item in items:

        qty = int(item.get("quantity", 0))
        price = float(item.get("price", 0))

        total = qty * price
        grand_total += total

        product_image = make_product_image(item.get("image", ""))

        requirement = item.get("customer_requirement", "")

        product_text = item.get("name", "")

        if requirement:
            product_text = f"{product_text}<br/><font size='7' color='gray'>Req: {requirement}</font>"

        table_data.append([
            product_image,
            make_text(product_text, raw_html=True),
            make_text(item.get("moq", ""), center=True),
            make_text(item.get("material", ""), center=True),
            make_text(item.get("size", ""), center=True),
            make_text(item.get("packing", ""), center=True),
            make_text(f"{qty:,}", center=True),
            make_text(money(price), center=True),
            make_text(money(total), center=True)
        ])

    table_data.append([
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        make_text("Grand Total", center=True),
        make_text(money(grand_total), center=True)
    ])

    row_heights = [26]

    for _ in items:
        row_heights.append(64)

    row_heights.append(24)

    table = Table(
        table_data,
        colWidths=[55, 90, 42, 55, 45, 80, 42, 60, 68],
        rowHeights=row_heights,
        repeatRows=1
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),

        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("FONTSIZE", (0, 1), (-1, -1), 8),

        ("GRID", (0, 0), (-1, -1), 0.6, colors.grey),

        ("BACKGROUND", (0, 1), (-1, -2), colors.whitesmoke),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#dbeafe")),

        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (0, 1), (0, -2), "CENTER"),
        ("ALIGN", (2, 1), (-1, -1), "CENTER"),

        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 28))

    footer = Paragraph(
        """
        <font size=10 color='gray'>
        Thank you for your inquiry.<br/>
        Generated by bridgequotation.com
        </font>
        """,
        styles["Normal"]
    )

    elements.append(footer)

    doc.build(elements)

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=quotation.pdf"
        }
    )


# =========================
# DEBUG TOOLS
# =========================

@app.get("/debug/users")
def debug_users():
    db = SessionLocal()

    users = db.query(User).all()

    result = [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "approval_status": u.approval_status,
            "company_name": u.company_name,
            "email": u.email
        }
        for u in users
    ]

    db.close()

    return result


@app.get("/debug/make-sales/{username}")
def make_sales(username: str):
    db = SessionLocal()

    user = db.query(User).filter(
        User.username == username
    ).first()

    if not user:
        db.close()
        return {
            "success": False,
            "message": "User not found"
        }

    user.role = "sales"
    user.account_type = "employee"
    user.approval_status = "Approved"
    user.assigned_sales = ""

    db.commit()
    db.close()

    return {
        "success": True,
        "message": f"{username} is now a sales user"
    }


@app.get("/debug/delete-order/{order_id}")
def delete_order(order_id: int):
    db = SessionLocal()

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:
        db.close()

        return {
            "success": False,
            "message": "Order not found"
        }

    db.delete(order)

    db.commit()
    db.close()

    return {
        "success": True,
        "message": f"Order {order_id} deleted"
    }
