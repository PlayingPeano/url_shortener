from pydantic import BaseModel, HttpUrl


class LinkCreate(BaseModel):
    original_url: HttpUrl


class LinkUpdate(BaseModel):
    original_url: HttpUrl


class LinkOut(BaseModel):
    id: int
    original_url: str
    short_code: str

    model_config = {"from_attributes": True}