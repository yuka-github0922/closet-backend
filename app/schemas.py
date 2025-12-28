from pydantic import BaseModel
from app.enums import Category, Color, Season


class ClothingItemCreate(BaseModel):
    name: str
    categories: list[Category]
    colors: list[Color]
    seasons: list[Season]
    size: str = ""
    material: str = ""
    image_path: str = ""


class ClothingItemResponse(BaseModel):
    id: int
    name: str
    categories: list[Category]
    colors: list[Color]
    seasons: list[Season]
    size: str = ""
    material: str = ""
    image_path: str = ""

    model_config = {"from_attributes": True}
