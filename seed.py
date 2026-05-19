from database import SessionLocal
from models import Product
from database import Base
from database import engine

Base.metadata.create_all(bind=engine)

db = SessionLocal()

def seed_products():
    db = SessionLocal()

    if db.query(Product).count() == 0:
        products = [
    Product(id=1, name="VR", price=500, description="Basic item",image="/static/image/VR.jpg"),
    Product(id=2, name="GP", price=1000, description="Premium item",image="/static/image/GP.jpg"),
    Product(id=3, name="SF", price=520, description="I LOVE YOU",image="/static/image/SF.jpg"),
    Product(id=4, name="PJ", price=1314, description="WILL BE TOGETHER FOREVER",image="/static/image/PJ.jpg"),
    Product(id=5, name="Heart", price=9999, description="LYY IS THE BEST",image="/static/image/1.png"),
    Product(id=6, name="BATHROOM_SETS", price=8888, description="WXY IS THE BEST",image="/static/image/BATHROOM_SETS.png"),
    Product(id=7, name="COFFEE_MAKER", price=6666, description="WE ARE THE BEST",image="/static/image/COFFEE_MAKER.png"),
    Product(id=8, name="SNACK_BOX", price=4444, description="WE WILL BE TOGETHER FOREVER",image="/static/image/SNACK_BOX.png"),
    Product(id=9, name="BAKE_SET", price=2222, description="I MISS YOU",image="/static/image/BAKE_SET.png"),
    Product(id=10, name="STORGE_BOX", price=1111, description="I LOVE YOU TOO",image="/static/image/STORGE_BOX.png")
   ]
        db.add_all(products)
        db.commit()

    db.close()

seed_products()


print("Products inserted successfully")