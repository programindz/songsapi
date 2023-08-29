from fastapi import FastAPI, Request, Depends, HTTPException, status, Query, Form
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.templating import Jinja2Templates
import bcrypt
import jwt 
from datetime import datetime, timedelta

from models import User
from database import users_collection, songs_collection


app = FastAPI()

SECRET_KEY = "44b9b59f15897cb0549c7a153ba8aa8b"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

templates = Jinja2Templates(directory= "templates")

@app.get("/register")
def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/")
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/search")
def search(request: Request, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    token = credentials.credentials
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    return templates.TemplateResponse("search.html", {"request": request, "username": username})



def create_token(username: str):
    payload = {
        "username": username,
        "exp": datetime.utcnow()+ timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    token = jwt.encode(payload = payload,
                    key = SECRET_KEY,
                    algorithm = ALGORITHM)
    return token

async def validate_token(token: str):
    try:
        payload = jwt.decode(token, key = SECRET_KEY, algorithms=[ALGORITHM])
        return True
    except (jwt.exceptions.DecodeError, jwt.exceptions.ExpiredSignatureError):
        return False
    

@app.post("/register")
def register_user(request: Request,
                  email: str = Form(...),
                  username: str = Form(...),
                  password: str = Form(...)):
    if users_collection.find_one({"username": username}) or users_collection.find_one({"email": email}) :
        return {"status": "Username or Email already exists"}

    hash_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    user_dict = dict()
    user_dict["username"] = username
    user_dict["email"] = email
    user_dict["password"] = hash_pw

    users_collection.insert_one(user_dict)
    return templates.TemplateResponse("login.html", {"request": request})



@app.post("/login")
def login_user(request: Request, email: str=Form(...), password: str=Form(...)):
    user = users_collection.find_one({"email": email})
    if user and bcrypt.checkpw(password.encode(), user["password"]):
        token = create_token(user["username"])
        return templates.TemplateResponse("search.html", 
            {"request": request, 
            "username": user["username"], 
            "token": token,
            "songs": list()})
    return {"status": "Invalid Username or Password"}



@app.get("/home")
async def search_song(request: Request, artist: str = Query(...), username: str=Query(...), 
    token: str = Query(..., description="Authentication token")):
    is_valid = await validate_token(token)
    if not is_valid:
        raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED, 
                detail = "Invalid Token",
                headers={"WWW-Authenticate": "Bearer"})
    artist = artist.lower().replace(" ","")
    songs = songs_collection.find({"artist": artist}, {"_id":0})
    return templates.TemplateResponse("search.html", 
        {"request": request, 
        "username": username, 
        "token": token,
        "songs": list(songs)})