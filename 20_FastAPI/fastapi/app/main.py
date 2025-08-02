from fastapi import FastAPI, Response, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from .image_utils import make_gradient_png

app = FastAPI(title="Toy ML-serving API")
security = HTTPBasic()

def verify_user(credentials: HTTPBasicCredentials = Depends(security)):
    if not (
        secrets.compare_digest(credentials.username, "demo_user")
        and secrets.compare_digest(credentials.password, "demo_pass")
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid credentials",
                            headers={"WWW-Authenticate": "Basic"})
    return credentials.username

@app.get("/")
def root():
    return {"msg": "Hi! Use /generate?seed=42 to get a PNG."}

@app.get("/secure")
def secure_area(username: str = Depends(verify_user)):
    return {"msg": f"Welcome {username}, this is a protected route."}

@app.get("/generate", responses={200: {"content": {"image/png": {}}}})
def generate(seed: int = 0):
    """
    Генерирует PNG-картинку-градиент.
    Параметр `seed` делает ответ детерминированным для тестов.
    """
    png_bytes = make_gradient_png(seed=seed)
    return Response(content=png_bytes, media_type="image/png")
