# 5 core components
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 1. FastAPI app
app = FastAPI()

items = dict()

# 3. Define pydantic model for data validation
class Product(BaseModel):
    name: str
    id: int
    price: float=1

class PriceOutputModel(BaseModel):
    price : float

# 2. Assign a route to a function
@app.post("/add_item")
def add_item(product: Product):
    product_name = product.name
    product_id = product.id
    product_price = product.price
    # Make sure name or id does not already exists, throw exception
    # I will put id as a key.
    # if id in items.keys():
    #      raise HTTPException(status_code=404,
    #                          detail="id already exists")
    for item in items.values():
        if item.name.lower() == product_name.lower() or\
           item.id == product_id:
            # 5. HTTPException
            raise HTTPException(status_code=404,
                                detail="name/id already exists")
    items[product_id] = product
    return {"message":"item successfully added"}
    # {1234:{"id":1234, "name": "pencil", "price":1}}

#4. Limite Response
@app.get("/check_price_by_name", response_model=PriceOutputModel)
def check_item_price(name:str):
    for item in items.values():
        if item.name == name:
           return {"price": item.price}
    raise HTTPException(status_code=404, 
                        detail="Item not found")


# @app.get("/async_product_search"):
# async def async_product_search(products: list):
#         await product_search_api(products) # assume product_search_api is imported