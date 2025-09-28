# app.py
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Form
import requests, os
from utils import is_valid_hostname, resolves_to_server, generate_token, poll_txt


app = FastAPI(
    title="WorkZone API",
    description="Public API for WorkZone",
    version="1.0.0"
)

# Sample model
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float

# Open endpoint
@app.get("/api/")
def root():
    return {"message": "Welcome to WorkZone Public API"}

# Example POST endpoint
@app.post("/api/items/")
def create_item(item: Item):
    return {"message": "Item received", "item": item}

# Example GET endpoint with param
@app.get("/api/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id, "name": f"Item {item_id}"}


CADDY_API = "http://localhost:2019"   # Caddy Admin API
FRONTEND_PORT = 3000
BACKEND_PORT = 8000

def caddy_add_route(host: str):
    # JSON route that matches host, routes /api* to backend and the rest to frontend
    payload = {
      "match": [{"host":[host]}],
      "handle": [
        {
          "handler":"subroute",
          "routes":[
            {
              "match":[{"path":["/api*"]}],
              "handle":[{"handler":"reverse_proxy","upstreams":[{"dial":f"127.0.0.1:{BACKEND_PORT}"}]}]
            },
            {
              "handle":[{"handler":"reverse_proxy","upstreams":[{"dial":f"127.0.0.1:{FRONTEND_PORT}"}]}]
            }
          ]
        }
      ],
      "terminal": True
    }
    r = requests.post(f"{CADDY_API}/config/apps/http/servers/srv0/routes", json=payload)
    if r.status_code not in (200, 204):
        raise Exception(f"Caddy API error: {r.status_code} {r.text}")

@app.post("/register-domain/")
async def register_domain(domain: str = Form(...)):
    # 1) basic validation
    domain = domain.strip().lower()
    if not is_valid_hostname(domain):
        raise HTTPException(400, "invalid domain format")

    # 2) if it's a subdomain of your domain, accept immediately
    if domain.endswith(".workzone.tech"):
        caddy_add_route(domain)
        return {"status":"ok","method":"subdomain","domain":domain}

    # 3) try A/CNAME -> server IP automatic check
    if resolves_to_server(domain):
        # success: register and done
        caddy_add_route(domain)
        return {"status":"ok","method":"a_record","domain":domain}

    # 4) fallback: TXT verification (manual)
    token = generate_token()
    # save token to DB with domain and timestamp (pseudo)
    # DB.set_verification_token(domain, token)
    instructions = {
      "type":"txt",
      "name": "_verify",              # user should add _verify.domain TXT
      "value": token,
      "note": "After adding record, wait a few minutes and click 'Verify' or we'll poll automatically."
    }
    # We can start a background poll (or return and let user trigger verify)
    return {"status":"pending","verification":instructions}
