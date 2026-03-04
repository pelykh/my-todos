from fastapi import FastAPI
from database import Base, engine
from routers import auth

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth.router)


@app.get("/")
def read_root():
    return {"message": "Hello World"}
