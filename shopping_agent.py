from typing import Optional
from dotenv import load_dotenv
import os
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from product_api import get_product_details, get_famous_products, get_products_by_category, get_products_by_price_range, get_organic_products, search_products, get_product_price, get_products_by_keyword, get_products_by_rating, place_order
from review_api import get_product_rating, get_products_rating
from langgraph.checkpoint.memory import MemorySaver
import json
load_dotenv()

# Load system prompt from external file
def load_system_prompt(file_path: str = "system_prompt.txt") -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: {file_path} not found. Using default prompt.")
        return "You are a helpful shopping assistant."

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.5)

#agent memory
checkpoint = MemorySaver()

# tools that will be used by the agent to interact with the product and review APIs
@tool("get_product_details", description="Get details of a product by its ID. Input should be the product ID as an integer.")
def get_product_details_tool(product_id: int) -> dict:
    return get_product_details(product_id)

@tool("get_famous_products", description="Get a list of famous products by category. Input should be the category name as a string.")
def get_famous_products_tool(category: str) -> list:
    return get_famous_products(category)

@tool("get_products_by_category", description="Get products by category. Input should be the category name as a string.")
def get_products_by_category_tool(category: str) -> list:
    return get_products_by_category(category)

@tool("get_products_by_price_range", description="Get products within a price range. Input should be the minimum and maximum prices as floats.")
def get_products_by_price_range_tool(min_price: float, max_price: float) -> list:
    return get_products_by_price_range(min_price, max_price)

@tool("get_organic_products", description="Get a list of organic products. No input required.")
def get_organic_products_tool() -> list:
    return get_organic_products()

@tool("search_products", description="Search for products by keyword. Input should be the keyword as a string.")
def search_products_tool(keyword: str) -> list:
    return search_products(keyword)

@tool("get_product_price", description="Get the price of a product by its ID or name. Input should be either the product ID as an integer or the product name as a string.")
def get_product_price_tool(product_id: int = None, product_name: str = None) -> Optional[float]:
    return get_product_price(product_id=product_id, product_name=product_name)

@tool("get_products_by_keyword", description="Get products with a specific keyword in the description. Input should be the keyword as a string.")
def get_products_by_keyword_tool(keyword: str) -> list:
    return get_products_by_keyword(keyword)

@tool("get_products_by_rating", description="Get products with a specific minimum rating. Input should be the minimum rating as a float.")
def get_products_by_rating_tool(min_rating: float) -> list:
    return get_products_by_rating(min_rating)

@tool("get_product_rating", description="Get the average rating of a product by its ID. Input should be the product ID as an integer.")
def get_product_rating_tool(product_id: int) -> float:
    return get_product_rating(product_id)

@tool("get_products_rating", description="Get the average ratings of a list of products by their IDs. Input should be a list of product IDs as integers.")
def get_products_rating_tool(product_ids: list[int]) -> list:
    return get_products_rating(product_ids)

@tool("place_order", description="Place an order for a product. Input should be the product ID as an integer and quantity as an integer.")
def place_order_tool(product_id: int, quantity: int) -> str:
    return place_order(product_id, quantity)



# create the agent with the defined tools and the language model
system_prompt = load_system_prompt()

agent = create_agent(
    model=llm,
    tools=[
        get_product_details_tool,
        get_famous_products_tool,
        get_products_by_category_tool,
        get_products_by_price_range_tool,
        get_organic_products_tool,
        search_products_tool,
        get_product_price_tool,
        get_products_by_keyword_tool,
        get_products_by_rating_tool,
        get_product_rating_tool,
        get_products_rating_tool,
        place_order_tool,
    ],
    system_prompt=system_prompt,
    checkpointer=checkpoint
)

def agent_invoke(messages, config=None):
    if config is None:
        config = {}
    return agent.invoke(
        {
            "messages": messages
        },
        config=config
    )
