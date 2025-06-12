
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from wifi import list_networks, connect_to_network, get_current_connection

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    networks = list_networks()
    current = get_current_connection()
    return templates.TemplateResponse("index.html", {"request": request, "networks": networks, "current": current})

@app.post("/connect", response_class=RedirectResponse)
def connect(ssid: str = Form(...), password: str = Form(...)):
    connect_to_network(ssid, password)
    return RedirectResponse("/", status_code=303)
