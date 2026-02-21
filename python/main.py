from fastapi import FastAPI

app = FastAPI(title="Sample FastAPI App")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "fastapi-app"
    }

@app.get("/hello")
def hello():
    return {
        "message": "Hello from FastAPI"
    }

@app.get("/products/{product_id}")
def get_product(product_id: int):
    return {
        "id": product_id,
        "name": "Sample Product",
        "price": 999
    }