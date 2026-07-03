import pandas as pd

from database import SessionLocal, Base, engine
from models import Product

Base.metadata.create_all(bind=engine)


def value(row, column, default=""):
    if column not in row:
        return default

    item = row[column]

    if pd.isna(item):
        return default

    return item


def seed_products():

    db = SessionLocal()

    try:

        df = pd.read_excel("Products.xlsx")
        df.columns = df.columns.str.strip().str.lower()

        print(df.columns.tolist())

        for _, row in df.iterrows():

            existing = db.query(Product).filter(
                Product.id == row["id"]
            ).first()

            product_data = {
                "name": value(row, "name"),
                "price": value(row, "price", 0),
                "description": value(row, "description"),
                "image": value(row, "image"),

                "image_2": value(row, "image_2"),
                "image_3": value(row, "image_3"),
                "image_4": value(row, "image_4"),
                "image_5": value(row, "image_5"),
                "image_6": value(row, "image_6"),
                "video": value(row, "video"),

                "moq": value(row, "moq", 1),
                "material": value(row, "material"),
                "volume": value(row, "volume"),
                "size": value(row, "size"),
                "packing": value(row, "packing"),
                "category": value(row, "category"),
                "price_500": value(row, "price_500", 0),
                "price_1000": value(row, "price_1000", 0),
                "price_3000": value(row, "price_3000", 0),
                "price_10000": value(row, "price_10000", 0),
                "price_50000": value(row, "price_50000", 0),
            }

            if existing:
                for key, item in product_data.items():
                    setattr(existing, key, item)

            else:
                product = Product(
                    id=row["id"],
                    **product_data
                )

                db.add(product)

        db.commit()

        print("Products imported successfully")

    finally:
        db.close()


if __name__ == "__main__":
    seed_products()
