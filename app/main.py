from dotenv import load_dotenv
load_dotenv()

from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, exists, literal, func
from fastapi.staticfiles import StaticFiles

from app.database import SessionLocal, engine


from app.models import Base, ClothingItem as ClothingItemModel
from app.schemas import ClothingItemCreate, ClothingItemResponse
from app.enums import Category, Color, Season

import os
import uuid
from fastapi import UploadFile, File

from app.services.supabase_storage import upload_image_to_supabase
from app.services.supabase_storage import delete_file_by_public_url
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
# テーブル作成（MVPなので create_all でOK）
Base.metadata.create_all(bind=engine)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.add_middleware(
    CORSMiddleware,
        allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ★ 必ず Depends より前に定義する
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _split_csv(value: Optional[str]) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def _json_array_contains_any(column, values: list[str]):
    """
    SQLite: JSON配列 column が values のどれかを含むか
    EXISTS (SELECT 1 FROM json_each(column) WHERE value IN (...))
    """
    if not values:
        return None

    je = func.json_each(column).table_valued("value").alias("je")
    return exists(
        select(literal(1)).select_from(je).where(je.c.value.in_(values))
    )


@app.get("/")
def root():
    return {"message": "hello"}

@app.post("/items", response_model=ClothingItemResponse)
def create_item(
    body: ClothingItemCreate,
    db: Session = Depends(get_db),
):
    item = ClothingItemModel(
        name=body.name,
        categories=[c.value for c in body.categories],
        colors=[c.value for c in body.colors],
        seasons=[s.value for s in body.seasons],
        size=body.size,
        material=body.material,
        image_path=body.image_path,
        owner_id=1,
    )

    db.add(item)
    db.commit()
    db.refresh(item)
    # ★ DBのstr配列 → Enum配列に戻して返す（ここ大事）
    return ClothingItemResponse(
        id=item.id,
        name=item.name,
        categories=[Category(v) for v in item.categories],
        colors=[Color(v) for v in item.colors],
        seasons=[Season(v) for v in item.seasons],
        size=item.size,
        material=item.material,
        image_path=item.image_path,
    )

def _split_csv(value: Optional[str]) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def _json_array_contains_any(column, values: list[str]):
    """
    SQLiteのJSON配列 column が values のどれかを含むか
    → json_each(column) の value に一致する行が存在するかで判定
    """
    if not values:
        return None

    # json_each は table-valued function（key, value, type などを返す）
    je = func.json_each(column).table_valued("value").alias("je")

    # EXISTS (SELECT 1 FROM json_each(column) AS je WHERE je.value IN (...))
    return exists(
        select(literal(1)).select_from(je).where(je.c.value.in_(values))
    )


@app.get("/items")
def list_items(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    color: Optional[str] = None,
    season: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(ClothingItemModel)

    if keyword:
        q = q.filter(ClothingItemModel.name.contains(keyword))
    if category:
        q = q.filter(ClothingItemModel.categories.contains([category]))
    if color:
        q = q.filter(ClothingItemModel.colors.contains([color]))
    if season:
        q = q.filter(ClothingItemModel.seasons.contains([season]))

    items = q.order_by(ClothingItemModel.id.desc()).all()

    return [
        {
            "id": item.id,
            "name": item.name,
            "categories": item.categories,
            "colors": item.colors,
            "seasons": item.seasons,
            "size": item.size,
            "material": item.material,
            "image_path": item.image_path,
        }
        for item in items
    ]

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    # バリデーション（最低限）
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="image file only")

    data = await file.read()
    try:
        public_url = upload_image_to_supabase(
            file_bytes=data,
            content_type=file.content_type,
            filename=file.filename,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"upload failed: {e}")

    # フロントはこれをimage_pathとして/itemsに渡す
    return {"image_path": public_url}


@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(ClothingItemModel).filter(ClothingItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="item not found")

    # 先に画像URLを退避
    image_url = item.image_path

    # DB削除
    db.delete(item)
    db.commit()

    # Storage削除（失敗してもDBは消えてるので、ここは落とさないのがMVP的に良い）
    try:
        delete_file_by_public_url(image_url)
    except Exception as e:
        print("WARN: failed to delete storage file:", e)

    return {"ok": True}