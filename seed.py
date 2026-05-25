import pandas as pd

from database import SessionLocal, Base, engine
from models import Product

Base.metadata.create_all(bind=engine)


def seed_products():

    db = SessionLocal()

    try:

        df = pd.read_excel("Products.xlsx")
        df.columns = df.columns.str.strip()
        print(df.columns.tolist())
        for _, row in df.iterrows():

            existing = db.query(Product).filter(
                Product.id == row["id"]
            ).first()

            if existing:

                existing.name = row["name"]
                existing.price = row["price"]
                existing.description = row["description"]
                existing.image = row["image"]
                existing.moq = row["moq"]
                existing.material = row["material"]
                existing.volume = row["volume"]
                existing.size = row["size"]

            else:

                product = Product(
                    id=row["id"],
                    name=row["name"],
                    price=row["price"],
                    description=row["description"],
                    image=row["image"],
                    moq=row["moq"],
                    material=row["material"],
                    volume=row["volume"],
                    size=row["size"]
                )

                db.add(product)

        db.commit()

        print("Products imported successfully")

    finally:
        db.close()


seed_products()