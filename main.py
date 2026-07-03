from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from database import engine, SessionLocal
from models import Product, User, Order, Base

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
        "orders",
        "sales_username",
        "VARCHAR DEFAULT 'BILL'"
    )

    add_column_if_missing(
        "orders",
        "status",
        "VARCHAR DEFAULT 'Pending'"
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
def get_products():
    db = SessionLocal()
    products = db.query(Product).all()

    result = []

    for p in products:
        result.append({
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "description": p.description,
            "image": p.image,
            "image_2": p.image_2,
            "image_3": p.image_3,
            "image_4": p.image_4,
            "image_5": p.image_5,
            "image_6": p.image_6,
            "video": p.video,
            "price_500": p.price_500,
            "price_1000": p.price_1000,
            "price_3000": p.price_3000,
            "price_10000": p.price_10000,
            "price_50000": p.price_50000,
            "category": p.category
        })

    db.close()
    return result


@app.get("/products/{product_id}")
def get_product(product_id: int):
    db = SessionLocal()
    product = db.query(Product).filter(Product.id == product_id).first()
    db.close()

    if product:
        gallery_images = [
            product.image,
            product.image_2,
            product.image_3,
            product.image_4,
            product.image_5,
            product.image_6
        ]

        gallery_images = [
            image for image in gallery_images
            if image and str(image).strip()
        ]

        return {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "description": product.description,
            "image": product.image,
            "image_2": product.image_2,
            "image_3": product.image_3,
            "image_4": product.image_4,
            "image_5": product.image_5,
            "image_6": product.image_6,
            "gallery_images": gallery_images,
            "video": product.video,
            "moq": product.moq,
            "material": product.material,
            "volume": product.volume,
            "size": product.size,
            "price_500": product.price_500,
            "price_1000": product.price_1000,
            "price_3000": product.price_3000,
            "price_10000": product.price_10000,
            "price_50000": product.price_50000,
            "category": product.category
        }

    return {"error": "Product not found"}


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
        approval_status="Pending"
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
        "email": existing.email
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
        "approval_status": u.approval_status
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

    customer = db.query(User).filter(
        User.username == data["username"]
    ).first()

    assigned_sales = "BILL"

    if customer and customer.assigned_sales:
        assigned_sales = customer.assigned_sales

    order = Order(
        username=data["username"],
        sales_username=assigned_sales,
        items=json.dumps(data["items"]),
        total=data["total"],
        status="Pending"
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
        result.append({
            "id": order.id,
            "username": order.username,
            "customer": order.username,
            "sales_username": order.sales_username,
            "total": order.total,
            "status": order.status,
            "items": order.items
        })

    db.close()
    return result


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

    order.status = "Confirmed"

    db.commit()
    db.close()

    return {
        "success": True,
        "message": "Order confirmed successfully!"
    }


@app.post("/sales/orders/{order_id}/reject")
def reject_order(order_id: int):
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

    order.status = "Rejected"

    db.commit()
    db.close()

    return {
        "success": True,
        "message": "Order rejected successfully!"
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
        "approval_status": user.approval_status
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
        result.append({
            "id": order.id,
            "status": order.status,
            "total": order.total
        })

    db.close()
    return result


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
    from reportlab.lib.styles import getSampleStyleSheet

    items = data.get("items", [])

    customer_name = data.get("customerName", "")
    customer_company = data.get("customerCompany", "")
    customer_email = data.get("customerEmail", "")

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
    elements.append(Spacer(1, 16))

    quote_info = Paragraph(
        f"""
        <font size=11>
        <b>Quotation No:</b> BQ-{datetime.now().strftime('%Y%m%d%H%M')}<br/>
        <b>Website:</b> bridgequotation.com<br/>
        <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}<br/>
        <b>Valid Until:</b> 30 days
        </font>
        """,
        styles["Normal"]
    )

    elements.append(quote_info)
    elements.append(Spacer(1, 14))

    customer_info = Paragraph(
        f"""
        <font size=11>
        <b>Customer:</b> {customer_name}<br/>
        <b>Company:</b> {customer_company}<br/>
        <b>Email:</b> {customer_email}
        </font>
        """,
        styles["Normal"]
    )

    elements.append(customer_info)
    elements.append(Spacer(1, 18))

    table_data = [
        [
            "Image",
            "Product",
            "MOQ",
            "Material",
            "Size",
            "Qty",
            "Unit Price",
            "Amount"
        ]
    ]

    def money(value):
        return "${:,.2f}".format(float(value))

    grand_total = 0

    for item in items:

        qty = int(item["quantity"])
        price = float(item["price"])

        total = qty * price
        grand_total += total

        image_path = "." + item["image"]

        try:
            product_image = Image(
                image_path,
                width=55,
                height=55
            )
        except Exception:
            product_image = "No Image"

        table_data.append([
            product_image,
            item["name"],
            item.get("moq", ""),
            item.get("material", ""),
            item.get("size", ""),
            f"{qty:,}",
            money(price),
            money(total)
        ])

    table_data.append([
        "",
        "",
        "",
        "",
        "",
        "",
        "Grand Total",
        money(grand_total)
    ])

    table = Table(
        table_data,
        colWidths=[65, 120, 50, 75, 65, 45, 65, 75]
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),

        ("GRID", (0, 0), (-1, -1), 1, colors.grey),

        ("BACKGROUND", (0, 1), (-1, -2), colors.whitesmoke),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#dbeafe")),

        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),

        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),

        ("ALIGN", (2, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
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
