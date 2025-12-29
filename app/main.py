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

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
# テーブル作成（MVPなので create_all でOK）
Base.metadata.create_all(bind=engine)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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


@app.get("/items", response_model=List[ClothingItemResponse])
def list_items(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    color: Optional[str] = None,
    season: Optional[str] = None,
    db: Session = Depends(get_db),
):
    categories = _split_csv(category)
    colors = _split_csv(color)
    seasons = _split_csv(season)

    q = db.query(ClothingItemModel)

    # keyword（nameの部分一致）
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(ClothingItemModel.name.ilike(like))  # SQLiteでも動く

        # materialも検索対象にしたいならこれを足す：
        # q = q.filter(or_(
        #     ClothingItemModel.name.ilike(like),
        #     ClothingItemModel.material.ilike(like),
        # ))

    # categories / colors / seasons（JSON配列の “含む” 判定）
    cat_cond = _json_array_contains_any(ClothingItemModel.categories, categories)
    if cat_cond is not None:
        q = q.filter(cat_cond)

    color_cond = _json_array_contains_any(ClothingItemModel.colors, colors)
    if color_cond is not None:
        q = q.filter(color_cond)

    season_cond = _json_array_contains_any(ClothingItemModel.seasons, seasons)
    if season_cond is not None:
        q = q.filter(season_cond)

    # 新しい順
    q = q.order_by(ClothingItemModel.created_at.desc())

    return q.all()

@app.post("/upload")
def upload_image(file: UploadFile = File(...)):
    # 拡張子チェック（最低限）
    allowed = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    ext = allowed[file.content_type]
    filename = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join("uploads", filename)

    # 保存
    with open(save_path, "wb") as f:
        f.write(file.file.read())

    # クライアントに返す（DBに保存する用）
    return {"path": f"/uploads/{filename}"}
