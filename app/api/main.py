import os
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security.api_key import APIKeyHeader
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.orm import Session
import secrets as secrets_mod

from app.db.database import Base, engine, SessionLocal
from app.db.models import Link
from app.api.schemas import LinkCreate, LinkUpdate, LinkOut

app = FastAPI()

STATIC_DIR = Path(__file__).resolve().parent / "static"

API_KEY = os.getenv("API_KEY", "").strip()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(provided: str | None = Security(api_key_header)) -> None:
    if not API_KEY:
        return
    if not provided or not secrets_mod.compare_digest(provided, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

Instrumentator(
    excluded_handlers=["/metrics", "/health"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/links", response_model=list[LinkOut])
def list_links(limit: int = 50, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 200))
    return db.query(Link).order_by(Link.id.desc()).limit(limit).all()


@app.post("/links", response_model=LinkOut, dependencies=[Depends(require_api_key)])
def create_link(payload: LinkCreate, db: Session = Depends(get_db)):
    for _ in range(5):
        code = secrets_mod.token_urlsafe(6)[:8]
        exists = db.query(Link).filter(Link.short_code == code).first()
        if not exists:
            break
    else:
        raise HTTPException(status_code=500, detail="Could not generate unique short code")

    link = Link(original_url=str(payload.original_url), short_code=code)
    db.add(link)
    db.commit()
    db.refresh(link)
    return link

@app.get("/links/{link_id}", response_model=LinkOut)
def get_link(link_id: int, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link

@app.put("/links/{link_id}", response_model=LinkOut, dependencies=[Depends(require_api_key)])
def update_link(link_id: int, payload: LinkUpdate, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    link.original_url = str(payload.original_url)
    db.commit()
    db.refresh(link)
    return link


@app.delete("/links/{link_id}", status_code=204, dependencies=[Depends(require_api_key)])
def delete_link(link_id: int, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    db.delete(link)
    db.commit()
    return None


@app.get("/r/{code}")
def redirect_by_code(code: str, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.short_code == code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")

    return RedirectResponse(url=link.original_url, status_code=307)


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")