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
from io import BytesIO
from datetime import datetime

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

Base.metadata.create_all(bind=engine)

def seed_products():

    db = SessionLocal()

    if db.query(Product).count() == 0:

        products = [

            Product(
                id=1,
                name="VR",
                price=500,
                description="Basic item",
                image="/static/image/VR.jpg"
            ),

            Product(
                id=2,
                name="GP",
                price=1000,
                description="Premium item",
                image="/static/image/GP.jpg"
            ),

            Product(
                id=3,
                name="SF",
                price=520,
                description="I LOVE YOU",
                image="/static/image/SF.jpg"
            ),

            Product(
                id=4,
                name="PJ",
                price=1314,
                description="WILL BE TOGETHER FOREVER",
                image="/static/image/PJ.jpg"
            ),

            Product(
                id=5,
                name="Heart",
                price=9999,
                description="LYY IS THE BEST",
                image="/static/image/1.png"
            ),
            Product(
                id=6, 
                    name="BATHROOM_SETS", 
                    price=8888, 
                    description="WXY IS THE BEST",
                    image="/static/image/BATHROOM_SETS.png"),
            
            Product(
                    id=7, 
                    name="COFFEE_MAKER", 
                    price=6666, 
                    description="WE ARE THE BEST",
                    moq =500,
                    material = "Plastic",
                    volume = "2m³",
                    size = 5*5*5,
                    image="/static/image/COFFEE_MAKER.png"),

            Product(
                id=8, 
                name="SNACK_BOX", 
                price=4444, 
                description="WE WILL BE TOGETHER FOREVER",
                moq =3300,
                material = "Plastic",
                volume = "5m³",
                size = 25*25*5,
                image="/static/image/SNACK_BOX.png"),

            Product(
                id=9, 
                name="BAKE_SET", 
                price=2222, 
                description="4PCS BAKEWARE SET",
                moq =500,
                material = "Aluminum",
                volume = "1m³",
                size = 15*45*25,
                image="/static/image/BAKE_SET.png"),

            Product(
                id=10, 
                name="STORGE_BOX", 
                price=1111, 
                description="I LOVE YOU TOO",
                moq =500,
                material = "Plastic",
                volume = "2m³",
                size = 5*5*5,
                image="/static/image/STORGE_BOX.png"),
        ]

        db.add_all(products)

        db.commit()

    db.close()

seed_products()

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
            "image": p.image
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
            "size": product.size
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

    items = data.get("items", [])

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4

    # TITLE
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(25 * mm, height - 25 * mm, "QUOTATION")

    # WEBSITE
    pdf.setFont("Helvetica", 10)
    pdf.drawString(25 * mm, height - 35 * mm, "bridgequotation.com")

    # DATE
    pdf.drawString(
        25 * mm,
        height - 42 * mm,
        f"Date: {datetime.now().strftime('%Y-%m-%d')}"
    )

    # TABLE HEADER
    y = height - 65 * mm

    pdf.setFont("Helvetica-Bold", 11)

    pdf.drawString(25 * mm, y, "Product")
    pdf.drawString(100 * mm, y, "Qty")
    pdf.drawString(125 * mm, y, "Price")
    pdf.drawString(155 * mm, y, "Total")

    y -= 5 * mm

    pdf.line(25 * mm, y, 185 * mm, y)

    y -= 10 * mm

    grand_total = 0

    pdf.setFont("Helvetica", 10)

    for item in items:

        name = item["name"]
        qty = item["quantity"]
        price = item["price"]

        total = qty * price

        grand_total += total

        pdf.drawString(25 * mm, y, str(name))
        pdf.drawString(100 * mm, y, str(qty))
        pdf.drawString(125 * mm, y, f"${price}")
        pdf.drawString(155 * mm, y, f"${total}")

        y -= 10 * mm

    # TOTAL
    y -= 5 * mm

    pdf.line(120 * mm, y, 185 * mm, y)

    y -= 10 * mm

    pdf.setFont("Helvetica-Bold", 12)

    pdf.drawString(125 * mm, y, "Grand Total:")
    pdf.drawString(155 * mm, y, f"${grand_total}")

    pdf.save()

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=quotation.pdf"
        }
    )