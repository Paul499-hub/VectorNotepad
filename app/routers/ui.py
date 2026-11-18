from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
# Modules
from app.core.helpers import parse_into_markdown

router = APIRouter(prefix="/ui", tags=["Front-End"])
templates = Jinja2Templates(directory="app/templates") # Allows jinja {$ include "partials/" %} referencing

@router.get("/home")
def r_home(
            request: Request
        ):
    try:
        return templates.TemplateResponse(
            request=request,
            name='index.html',
            context={}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/get_markdown")
def get_markdown(text: str):
    try:
        return parse_into_markdown(text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))