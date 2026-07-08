from sqlalchemy import Column, Integer, String, Float
from database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Integer)
    description = Column(String)
    slogan = Column(String, default="")
    image = Column(String)

    image_2 = Column(String, default="")
    image_3 = Column(String, default="")
    image_4 = Column(String, default="")
    image_5 = Column(String, default="")
    image_6 = Column(String, default="")
    video = Column(String, default="")

    moq = Column(Integer)
    material = Column(String)
    volume = Column(String)
    size = Column(String)
    packing = Column(String, default="")
    category = Column(String)
    price_500 = Column(Float)
    price_1000 = Column(Float)
    price_3000 = Column(Float)
    price_10000 = Column(Float)
    price_50000 = Column(Float)
    is_active = Column(Integer, default=1)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True, index=True)
    password = Column(String)

    role = Column(String, default="customer")
    assigned_sales = Column(String, default="BILL")

    company_name = Column(String, default="")
    email = Column(String, default="")
    account_type = Column(String, default="customer")
    approval_status = Column(String, default="Pending")
    customer_level = Column(String, default="A")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    sales_username = Column(String)
    items = Column(String)
    total = Column(Float)
    status = Column(String, default="Pending")
    created_at = Column(String, default="")
    return_comment = Column(String, default="")


class PricingSetting(Base):
    __tablename__ = "pricing_settings"

    id = Column(Integer, primary_key=True, index=True)
    b_multiplier = Column(Float, default=1.2)
