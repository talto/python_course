from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, status, Response, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from .image_utils import make_gradient_png


SECRET_KEY = "CHANGE_ME"  # заглушка ключа
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ---------------------------------------------------------------------------
# заглушка вместо базы данных с пользователями
# ---------------------------------------------------------------------------
fake_users_db = {
    "demo_user": {
        "username": "demo_user",
        "full_name": "Demo User",
        "hashed_password": pwd_context.hash("demo_pass"),
    }
}

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    full_name: str | None = None

# ---------------------------------------------------------------------------
# Utility funcs
# ---------------------------------------------------------------------------

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def authenticate_user(username: str, password: str) -> User | None:
    user_dict = fake_users_db.get(username)
    if not user_dict or not verify_password(password, user_dict["hashed_password"]):
        return None
    return User(**user_dict)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user_dict = fake_users_db.get(username)
    if user_dict is None:
        raise credentials_exc
    return User(**user_dict)




app = FastAPI(title="Toy ML-serving API")
@app.post("/login", response_model=Token, tags=["auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Возвращает JWT-токен при корректном username/password"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/", tags=["public"])
async def root():
    return {"msg": "Hi! Use /generate?seed=42 to get a PNG."}


@app.get("/generate", responses={200: {"content": {"image/png": {}}}}, tags=["protected"])
async def generate(
    seed: int = Query(0, description="Seed for deterministic PNG"),
    current_user: User = Depends(get_current_user),
):
    png_bytes = make_gradient_png(seed=seed)
    return Response(content=png_bytes, media_type="image/png")


@app.get("/secure", tags=["protected"])
async def secure_area(current_user: User = Depends(get_current_user)):
    return {"msg": f"Welcome {current_user.username}, this is a protected route."}