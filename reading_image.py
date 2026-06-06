from pandas.core.algorithms import mode
import os
import base64
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()

from langchain_groq import ChatGroq

vision_llm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0.5
)


def describe_product_image(image_path:str) -> str:
    """
       Analyze a product image and return its key attributes as a JSON object.
       Use this when the user uploadds a photo of a product they interested in.
       The returned attribute can be used directly with search_products_tool.
    """
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    ext = Path(image_path).suffix.lower().lstrip('.')
    mime = "image/jpeg" if ext in ('jpg', 'jpeg') else f"image/{ext}"
    human_message = HumanMessage(
        content=[
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime};base64,{image_data}"
                }
            },
            {
                "type": "text",
                "text": (
                    "Look at this product image and extract its key attributes. "
                    "return ONLY a JSON object with these fields:\n"
                    "- product_type: what kind of product it is (e.g. honey, olive oil, almonds)\n"
                    "- search_type : a short keyword to search for it (e.g. 'honey', 'olive oil')\n"
                    "- is_organic : true if the label says organic, false if not, null if unclear\n"
                    "- brand: the brand name if visible (e.g. 'local', 'Amlou')\n"
                    "- flavor: the flavor if visible (e.g. 'honey', 'almonds', 'olive oil')\n"
                    "- image_description: a short description of the product in one sentence" 
                )
            }
        ]
    )
    response = vision_llm.invoke([human_message])
    return response.content



    
