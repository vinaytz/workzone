# app.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="WorkZone Public API",
    description="Open API - anyone can access",
    version="1.0.0",
    openapi_url="/openapi.json",  # OpenAPI docs available
    docs_url="/docs"               # Swagger UI
)

# Sample model
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float

# Open endpoint
@app.get("/")
def root():
    return {"message": "Welcome to WorkZone Public API"}

# Example POST endpoint
@app.post("/items/")
def create_item(item: Item):
    return {"message": "Item received", "item": item}

# Example GET endpoint with param
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id, "name": f"Item {item_id}"}
