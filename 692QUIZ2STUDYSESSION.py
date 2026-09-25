from fastapi import FastAPI
# Microservices and Containerization (Concept)
import requests
 


# first example reading API Documentation
# Call current weather data - referencing lecture slides we went over in class
# https://api.openweathermap.org/data/2.5/weather"
# based on the signature what type of https request does it take?
# you can tell based on parameters
# we're going over examples now

lat = 1234
lon = 2345
api_key = "1234"
url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API key}"
requests.get(url)

# option2
url = "https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API key}"
params = {"lat": lat, "lon": lon, "appid": api_key}
requests.get(url, params=params)

# possible question: whether information by longitude or latitude
# possible question: can u call by cityid by getting the data
# she'll give example mockup API documents and ask whether you can call it through paramaters
# other example could be her giving the /docs for /seach_and_save/jobs what type of request would you use? Answer: Post
# based off documentation how many parameters does it take?
# in this document which section is showing the possible status code? Answer is response, how many codes are available
# 20 questions, 1 is a dummy question, dummy question is telling you to write your name on cheat sheet, 19 questions and 1 is programming
# 3 questions are just for reading api documentation. she said "MAKE SURE" to read those questions carefully. there are 2 questions related to reading the route defintion
# and how to send the parameters

# Now covering Day 6:
# 5 core components
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
# 1st instantiate the app. #1. FastAPI app
app = FastAPI()
items = dict()

#3 Define pydantic model for data validation
class Product(BaseModel):
    name: str
    id: int
    price: float =1

class PriceOutputModel(BaseModel):
    price: float

# 2 Assign a route to a function #she said she's going to do something similar to what we did in class. Example: Items and price and stuff We checked whether item exists and price


@app.post("/add_item")
def add_item(product: Product):
    product_name = product.name
    product_id = product.id
    product_price = product.price
    #make sure name/id does not already exists, throw exception if it does
    #put id as key
    if id in items.keys():
        raise HTTPException(status_code=404,detail="id already exists")
    
    for item in items.values():
        item.name.lower() == product_name.lower() or item.id == product_id
        raise HTTPException(status_code=404,detail="id already exists")
    items[product_id] = product
    return {"message": "item successfully added"}
    #{1234:{"id":1234, "name": "pencil", "price":1}}






#Step 4 Limit response
@app.get("/check_price_by_name", response_model=PriceOutputModel)
def check_item_price(name:str):
    for item in items.values():
        if item.name == name:
            return {"price":item.price, "id":item.id} #she's going to ask questions where she swaps the "variable" and the actual variable and going to ask you what it returns 
    raise HTTPException(status_code=404,
                        detail = "Item not found")


#TRUE FALSE QUESTION SHE'S GOING TO ASK, RUNNING FAST API IN DEVELOPMENT MODE, BY DEFAULT DOES IT USE 127.0.0.1 AS A URL ADRESS, THE ANSWER IS TRUE
#TRUE/FALSE IF YOUR USING FAST API IN PRODUCT MODE THE URL IT USES IS 0.0.0.0 IS TRUE
#FastAPI uses 8000 as a port by default - TRUE
#We can use FASTAPI for production - TRUE


import requests
url = "http://127.0.0.1:8000"
response = requests.get(url+"/check_price_by_name", params = {"name":"pencil"})

response.status_code #output would be 404

response.content #b'{"detail":Item not Found"}'

product = {"name": "pencil", "id":1, "price":1}
response = requests.post(url+"/add_item", json = product) #pydantic = json
response.status_code #output 200


response.content #b{message: item succesfully added}


product = {"name": "pencil", "id":2, "price":1}
response = requests.post(url+"/add_item", json = product) #pydantic = json
response.status_code #output 404


url = "https://127.0.0.1:8000"
response = requests.get(url+"/check_price_by_name", params = {"name":"pencil"})


##11:13 AM REVIEW WHAT WE JUST DID ^^^^^^ IN STEP 4  and check how the output changes when u fuck with the return statement in step 4
## Also fun Diane lore: she takes the actual quiz before every review  session and thats how she goes off her quiz session


#Now moving onto Asynchronous session
## TRUE FALSE TIME : SYNCHRONOUS OPERATIONS ARE GOOD FOR SEQUENTIAL OPERATIONS: TRUE
## SYNCRHONOUS OPERATIONS ARE BLOCKING OPERATIONS: TRUE
# ASYNCHRONOUS FUNCTIONS ARE GOOD FOR EXECUTING CODE THAT TAKES A LONG TIME TO RUN AND WHEN U WANNA DO OTHER THINGS: TRUE

@app.get("/async_product_search"):
async def async_product_search(products: list):
        await product_search_api(products) #assume product_search_api is imported # this is different than the class example because we aren't using an httpx url asynchronously 





# DAY 6  LOOK OVER SENDING PARAMETERS AND DATA TO FASTAPI VIA REQUEST GET PUT/POST SLIDE 26

#DAY 8 MICROSERVICES AND CONTAINERS 2 CONCEPTUAL QUESTIONS

# TRUE FALSE I ALREADY BUILT AN IMAGE AND IT SAYS I CAN DEPLOY IT TO ANY ENVIORNMENT TRUE OR FALSE: TRUE BC IF IMAGE IS ALREADY BUILT I CAN REUSE IT
#MICROSERVICES ARE TALKING TO EACH OTHER THROUGH FUNCTION CALL : FALSE THEY ARE COMMUNICATING TO EACH OTHER THROUGH API 
# YOU CANNOT CONTAINERIZE A MICROSERVICE, TRUE OR FALSE: FALSE, YOU CAN CONTAINERIZE A MICROSERVICE
#qui 2 is going to ask u to create and call fast api


##Moving onto hw 2, 11:41 I am losing my mindddddddd


#we're looking at the fastapi folder extract_save_data.py
#creating a input/base model if she doesn't prove it
#def call_google_Search, she made this function to understand how to use differrent libraries to correctly call data idk if this is relevant to Q2
#11:48 she didn't post the answers to hw2 and we just doing that rn
#wants us to think about raise HTTPException under call_google_search -> this seems likely it might be on quiz
# just focus on creating the route and how to call it and shaping the input/output model 

                        