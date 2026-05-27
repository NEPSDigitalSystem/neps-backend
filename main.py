from fastapi import FastAPI

app = FastAPI(title="NEPS API")

@app.get("/")
def read_root():
    return {"message": "hello neps"}