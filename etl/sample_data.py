"""Built-in synthetic sample datasets generator."""

import io

import polars as pl


def get_sample_customers_csv() -> bytes:
    data = """customer_id,full_name,email,signup_date,country,latitude,longitude,account_balance
CUST_1001,Alice Smith,alice@example.com,2023-01-15,USA,37.7749,-122.4194,1250.50
CUST_1002,Bob Jones,bob@example.com,2023-02-20,Canada,45.4215,-75.6972,3400.00
CUST_1003,Charlie Brown,charlie@example.com,2023-03-10,UK,51.5074,-0.1278,890.25
CUST_1004,Diana Prince,diana@example.com,2023-04-05,USA,34.0522,-118.2437,5600.75
CUST_1005,Evan Wright,evan@example.com,2023-05-12,Germany,52.5200,13.4050,2100.00
"""
    return data.encode("utf-8")


def get_sample_dirty_transactions_csv() -> bytes:
    data = """txn_id,user_id,amount,status,txn_timestamp,ssn
TXN_101,CUST_1001,150.00,COMPLETED,2023-06-01 10:30:00,123-45-6789
TXN_102,CUST_1002,-50.00,PENDING,2023-06-01 11:15:00,987-65-4321
TXN_103,CUST_1003,999999.00,FAILED,invalid-date,555-12-3456
TXN_104,,200.50,COMPLETED,2023-06-02 09:00:00,
TXN_101,CUST_1001,150.00,COMPLETED,2023-06-01 10:30:00,123-45-6789
"""
    return data.encode("utf-8")


def get_sample_parquet_bytes() -> bytes:
    df = pl.DataFrame(
        {
            "product_id": ["PROD_1", "PROD_2", "PROD_3"],
            "product_name": ["Widget A", "Widget B", "Gadget X"],
            "price": [19.99, 29.99, 99.50],
            "in_stock": [True, True, False],
        }
    )
    buf = io.BytesIO()
    df.write_parquet(buf)
    return buf.getvalue()
