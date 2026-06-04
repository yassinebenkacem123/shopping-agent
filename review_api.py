import os
from pathlib import Path
import sqlite3
from  dotenv import load_dotenv
import json
load_dotenv()
DB_NAME = os.getenv("DB_NAME")
DB_PATH = Path(__file__).parent.absolute() / DB_NAME


#1 : getting the average rating for a specific product
def get_product_rating(product_id:int) -> float:
    """retrurn average rating for a specific product"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT AVG(rating) as average_rating FROM reviews WHERE product_id = ?"
    cursor.execute(query, (product_id,))
    result = cursor.fetchone()
    average_rating = result[0] if result[0] is not None else 0
    conn.close()
    return round(average_rating, 2)




#2 :getting the average ratings for a list of products
def get_products_rating(product_ids:list) -> list:
    """return average ratings for a list of products"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT product_id, AVG(rating) as average_rating FROM reviews WHERE product_id IN ({seq}) GROUP BY product_id".format(
        seq=','.join(['?']*len(product_ids))
    )
    cursor.execute(query, product_ids)
    results = cursor.fetchall()
    average_ratings = [{"product_id": pid, "average_rating": round(avg, 2)} for pid, avg in results]
    conn.close()
    return json.dumps(average_ratings)
   



if __name__ == "__main__":
    product_id = 1
    average_rating = get_product_rating(product_id)
    print(f"Average rating for product {product_id}: {average_rating}")
    print(30 * "-")
    product_ids = [1, 2, 3]
    average_ratings_json = get_products_rating(product_ids)
    average_ratings_list = json.loads(average_ratings_json)
    for item in average_ratings_list:
        print(f"Average rating for product {item['product_id']}: {item['average_rating']}")