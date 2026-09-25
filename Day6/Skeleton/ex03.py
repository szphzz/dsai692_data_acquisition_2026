from fastapi import FastAPI
from pydantic import BaseModel


# 1. Create a FastAPI App Instance
app = FastAPI()
items = {}  # In-memory database


class Item(BaseModel):
    # 3. Define Pydantic Model
    name: str
    price: float
    instock_qt: int


class ItemResponse(BaseModel):  # added to control response
    total_worth: float  # only this will return
    # anything here must be included in return below, otherwise error i think


@app.post("/add_items/", response_model=ItemResponse)
def create_item(item: Item):
    items[item.name] = item
    total_worth = item.instock_qt * item.price
    return {"total_worth": total_worth}  # anything else that is not in ItemResponse will not throw an error
