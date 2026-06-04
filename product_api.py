from dotenv import load_dotenv
import os
import sqlite3
from pathlib import Path
from typing import Optional
import json
load_dotenv()
DB_NAME = os.getenv("DB_NAME")
DB_PATH = Path(__file__).parent.absolute() / DB_NAME

# 1: get product famous products for a specific category :
def get_famous_products(category: str = "all", limit: int = 5) -> list:
    """return a list of famous products for a specific category based on average ratings"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if category == "all":
        query = """
            SELECT p.id, p.name
            FROM products p
            JOIN reviews r ON p.id = r.product_id
            GROUP BY p.id
            ORDER BY AVG(r.rating) DESC
            LIMIT ?
        """
        cursor.execute(query, (limit,))
    else:
        query = """
            SELECT p.id, p.name
            FROM products p
            JOIN reviews r ON p.id = r.product_id
            WHERE p.category = ?
            GROUP BY p.id
            ORDER BY AVG(r.rating) DESC
            LIMIT ?
        """
        cursor.execute(query, (category, limit))
    results = cursor.fetchall()
    conn.close()
    products = [{"id": pid, "name": name} for pid, name in results]
    return json.dumps(products)


# 2: search for products :
def search_products(query:str, max_price:Optional[float] = None, min_price:Optional[float] = None, category:Optional[str] = None, is_organic:Optional[bool] = None) -> list:
    """search for products based on a query and optional filters"""
    query = query.strip()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    sql_query = "SELECT id, name FROM products WHERE name LIKE ?"
    params = [f"%{query}%"]
    
    if max_price is not None:
        sql_query += " AND price <= ?"
        params.append(max_price)
    
    if min_price is not None:
        sql_query += " AND price >= ?"
        params.append(min_price)
    
    if category is not None:
        sql_query += " AND category = ?"
        params.append(category)
    
    if is_organic is not None:
        sql_query += " AND is_organic = ?"
        params.append(int(is_organic))
    
    cursor.execute(sql_query, params)
    results = cursor.fetchall()
    conn.close()
    products = [{"id": pid, "name": name} for pid, name in results]
    return json.dumps(products)

# 3: get product details by id
def get_product_details(product_id: int) -> Optional[tuple]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, category, is_organic, description FROM products WHERE id = ?", (product_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        product_details = {
            "id": result[0],
            "name": result[1],
            "price": result[2],
            "category": result[3],
            "is_organic": bool(result[4]),
            "description": result[5]
        }
        return json.dumps(product_details)
    return None

    

# 4: get products by category
def get_products_by_category(category: str) -> list:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM products WHERE category = ?", (category,))
    results = cursor.fetchall()
    conn.close()
    products = [{"id": pid, "name": name} for pid, name in results]
    return json.dumps(products)


# 5: get organic products
def get_organic_products() -> list:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM products WHERE is_organic = 1")
    results = cursor.fetchall()
    conn.close()
    products = [{"id": pid, "name": name} for pid, name in results]
    return json.dumps(products)

# 6: get products within a price range
def get_products_by_price_range(min_price: float, max_price: float) -> list:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM products WHERE price BETWEEN ? AND ?", (min_price, max_price))
    results = cursor.fetchall()
    conn.close()
    products = [{"id": pid, "name": name} for pid, name in results]
    return json.dumps(products)

# 7: get products with a specific keyword in the description
def get_products_by_keyword(keyword: str) -> list:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM products WHERE description LIKE ?", (f"%{keyword}%",))
    results = cursor.fetchall()
    conn.close()
    products = [{"id": pid, "name": name} for pid, name in results]
    return json.dumps(products)

# 8: get products with a specific rating
def get_products_by_rating(min_rating: float) -> list:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = """
        SELECT p.id, p.name
        FROM products p
        JOIN reviews r ON p.id = r.product_id
        GROUP BY p.id
        HAVING AVG(r.rating) >= ?
    """
    cursor.execute(query, (min_rating,))
    results = cursor.fetchall()
    conn.close()

    products = [{"id": pid, "name": name} for pid, name in results]
    return json.dumps(products)


# 9 : get product price by id, or name,
def get_product_price(product_id: int = None, product_name: str = None) -> Optional[float]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if product_id is not None:
        cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,))
    elif product_name is not None:
        cursor.execute("SELECT price FROM products WHERE name = ?", (product_name,))
    else:
        return None

    result = cursor.fetchone()
    conn.close()
    if result:
        product_price = result[0]
        return product_price
    return None

def place_order(product_id: int, quantity: int) -> str:
    """Place an order for a product with specified quantity"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if product exists and get its details
    cursor.execute("SELECT name, price FROM products WHERE id = ?", (product_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return json.dumps({"status": "error", "message": "Product not found."})
    
    product_name = result[0]
    product_price = result[1]
    
    # Calculate total cost
    total_cost = product_price * quantity
    
    # Insert order into orders table
    cursor.execute(
        "INSERT INTO orders (product_id, product_name, quantity, total_price) VALUES (?, ?, ?, ?)",
        (product_id, product_name, quantity, total_cost)
    )
    
    conn.commit()
    order_id = cursor.lastrowid
    conn.close()
    
    return json.dumps({
        "status": "success",
        "message": f"Order placed successfully!",
        "order_id": order_id,
        "product_name": product_name,
        "quantity": quantity,
        "unit_price": product_price,
        "total_price": total_cost
    })
