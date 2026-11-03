from fastapi import FastAPI

app = FastAPI()


@app.get("/hello")
def hello():
    return {"message": "Hey there! 👋 Hope your day's going great."}


@app.get("/goodbye")
def goodbye():
    return {"message": "Catch you later! Take it easy. ✌️"}
