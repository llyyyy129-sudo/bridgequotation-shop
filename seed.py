from database import SessionLocal
from models import Product
from database import Base
from database import engine

Base.metadata.create_all(bind=engine)

db = SessionLocal()

products = [
    Product(id=1, name="VR", price=500, description="Basic item",image="image/vr.jpg"),
    Product(id=2, name="GP", price=1000, description="Premium item",image="image/GP.jpg"),
    Product(id=3, name="SF", price=520, description="I LOVE YOU",image="image/SF.jpg"),
    Product(id=4, name="PJ", price=1314, description="WILL BE TOGETHER FOREVER",image="image/PJ.jpg"),
    Product(id=5, name="Heart", price=9999, description="LYY IS THE BEST",image="image/1.png"),
    Product(id=6, name="Product F", price=8888, description="WXY IS THE BEST",image="https://via.placeholder.com/200"),
    Product(id=7, name="Product G", price=6666, description="WE ARE THE BEST",image="https://via.placeholder.com/200"),
    Product(id=8, name="Product H", price=4444, description="WE WILL BE TOGETHER FOREVER",image="https://via.placeholder.com/200"),
    Product(id=9, name="Product I", price=2222, description="I MISS YOU",image="https://via.placeholder.com/200"),
    Product(id=10, name="Product J", price=1111, description="I LOVE YOU TOO",image="https://via.placeholder.com/200"),
   ]

for p in products:
    existing = db.query(Product).filter(Product.id == p.id).first()

    if not existing:
        db.add(p)

db.commit()

db.close()

print("Products inserted successfully")