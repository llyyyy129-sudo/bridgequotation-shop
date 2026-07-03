from sqlalchemy import Column, Integer, String, Float
from database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Integer)
    description = Column(String)
    image = Column(String)
    moq = Column(Integer)
    material = Column(String)
    volume = Column(String)
    size = Column(String)
    category = Column(String)
    price_500 = Column(Float)
    price_1000 = Column(Float)
    price_3000 = Column(Float)
    price_10000 = Column(Float)
    price_50000 = Column(Float)


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


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    sales_username = Column(String)
    items = Column(String)
    total = Column(Float)
    status = Column(String, default="Pending")
