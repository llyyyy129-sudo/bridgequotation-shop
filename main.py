from fastapi import FastAPI, Request, Form, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from database import engine, SessionLocal
from models import Product, User, Order, Base

from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.platypus import Image
from io import BytesIO
from datetime import datetime

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

Base.metadata.create_all(bind=engine)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return FileResponse("templates/login.html")

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
        return {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "description": product.description,
            "image": product.image,
            "moq": product.moq,
            "material": product.material,
            "volume": product.volume,
            "size": product.size,
            "category": product.category
        }

    return {"error": "Product not found"}

@app.post("/register")
def register(user: dict):
    db = SessionLocal()

    existing = db.query(User).filter(User.username == user["username"]).first()

    if existing:
        db.close()
        return {"success": False, "message": "Username already exists!"}

    new_user = User(
        username=user["username"],
        password=user["password"]
    )

    db.add(new_user)
    db.commit()
    db.close()

    return {"success": True, "message": "Registration successful!"}


@app.post("/login")
def login(user: dict):
    db = SessionLocal()

    existing = db.query(User).filter(
        User.username == user["username"],
        User.password == user["password"]
    ).first()

    db.close()

    if existing:
        return {"success": True, "message": "Login successful!"}

    return {"success": False, "message": "Invalid username or password"}

@app.post("/create-order")
def create_order(data: dict):

    db = SessionLocal()

    order = Order(
        username=data["username"],
        items=str(data["items"]),
        total=data["total"]
    )

    db.add(order)

    db.commit()

    db.close()

    return {
        "success": True,
        "message": "Order created successfully!"
    }
@app.get("/login.html")
def login_page():
    return FileResponse("templates/login.html")

@app.get("/register.html")
def register_page():
    return FileResponse("templates/register.html")

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

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    elements = []

    styles = getSampleStyleSheet()

    # TITLE
    title = Paragraph(
        "<font size=24><b>QUOTATION</b></font>",
        styles["Title"]
    )

    elements.append(title)
    elements.append(Spacer(1, 20))

    # WEBSITE
    website = Paragraph(
        f"""
        <font size=12>
        bridgequotation.com<br/>
        Date: {datetime.now().strftime('%Y-%m-%d')}
        </font>
        """,
        styles["Normal"]
    )

    elements.append(website)
    elements.append(Spacer(1, 20))

    # TABLE
    table_data = [
        ["Image", "Product", "Qty", "Price", "Total"]
    ]

    grand_total = 0

    for item in items:

        qty = item["quantity"]
        price = item["price"]

        total = qty * price

        grand_total += total

        image_path = "." + item["image"]

        try:
            product_image = Image(
                image_path,
                width=60,
                height=60
            )
        except:
            product_image = "No Image"

        table_data.append([
            product_image,
            item["name"],
            str(qty),
            f"${price}",
            f"${total}"
        ])

    # TOTAL ROW
    table_data.append([
        "",
        "",
        "",
        "Grand Total",
        f"${grand_total}"
    ])

    table = Table(
        table_data,
        colWidths=[80, 180, 60, 80, 80]
    )

    table.setStyle(TableStyle([

        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),

        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 11),

        ("GRID", (0,0), (-1,-1), 1, colors.grey),

        ("BACKGROUND", (0,1), (-1,-2), colors.whitesmoke),

        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#dbeafe")),

        ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),

        ("BOTTOMPADDING", (0,0), (-1,0), 12),

        ("ALIGN", (2,1), (-1,-1), "CENTER"),

        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),

    ]))

    elements.append(table)

    elements.append(Spacer(1, 30))

    # FOOTER
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

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=quotation.pdf"
        }
    )