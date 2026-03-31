from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
from app.api.routers import health, chat, auth, rooms
from app.core.config import settings

# Создаем приложение
app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

# Подключаем роутеры
app.include_router(health.router, prefix="/api")
app.include_router(chat.router)
app.include_router(auth.router)
app.include_router(rooms.router)

# Создаем папку static если ее нет
os.makedirs("static", exist_ok=True)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} is running"}

@app.get("/chat")
async def get_chat():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>index.html not found</h1><p>Please create static/index.html</p>", status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)