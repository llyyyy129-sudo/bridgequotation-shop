from sqlalchemy import Column, Integer, String, Float, Text
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


class ProformaInvoice(Base):
    __tablename__ = "proforma_invoices"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, index=True)
    pi_no = Column(String, default="")
    pdf_path = Column(String, default="")
    status = Column(String, default="Sent")
    version = Column(Integer, default=1)
    sent_by = Column(String, default="")
    sent_at = Column(String, default="")
    received_at = Column(String, default="")
    customer_message = Column(Text, default="")


class PIHistory(Base):
    __tablename__ = "pi_histories"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, index=True)
    pi_id = Column(Integer, index=True)
    action = Column(String, default="")
    message = Column(Text, default="")
    created_by = Column(String, default="")
    created_at = Column(String, default="")
    pdf_path = Column(String, default="")


class SharedSalesFile(Base):
    __tablename__ = "shared_sales_files"

    id = Column(Integer, primary_key=True, index=True)
    folder_id = Column(Integer, index=True, default=0)
    original_name = Column(String, default="")
    file_path = Column(String, default="")
    file_type = Column(String, default="")
    file_size = Column(Integer, default=0)
    uploaded_by = Column(String, default="")
    uploaded_at = Column(String, default="")


class SharedSalesFolder(Base):
    __tablename__ = "shared_sales_folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_by = Column(String, default="")
    created_at = Column(String, default="")
