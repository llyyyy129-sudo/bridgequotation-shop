from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, SessionLocal
from models import Product, User, Order, Base

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Backend is running!"}


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
            "image": product.image
        }

    return {"error": "Product not found"}

@app.post("/register")
def register(user: dict):
    db = SessionLocal()

    existing = db.query(User).filter(User.username == user["username"]).first()

    if existing:
        db.close()
        return {"success": False, "message": "宝~用户名已存在啦！"}

    new_user = User(
        username=user["username"],
        password=user["password"]
    )

    db.add(new_user)
    db.commit()
    db.close()

    return {"success": True, "message": "注册成功了捏！"}


@app.post("/login")
def login(user: dict):
    db = SessionLocal()

    existing = db.query(User).filter(
        User.username == user["username"],
        User.password == user["password"]
    ).first()

    db.close()

    if existing:
        return {"success": True, "message": "登上啦！"}

    return {"success": False, "message": "用户名或密码输入错误咯"}

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
        "message": "订单创建成功了捏！"
    }