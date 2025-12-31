import os
from uuid import uuid4
from supabase import create_client, Client
from urllib.parse import urlparse

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "uploads")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY が未設定です")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def get_supabase_client():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def upload_image_to_supabase(file_bytes: bytes, content_type: str, filename: str | None = None) -> str:
    """
    Supabase Storageに画像をアップロードして「公開URL」を返す（public bucket前提）
    """
    bucket = os.environ.get("SUPABASE_BUCKET", "uploads")
    supabase = get_supabase_client()

    # 拡張子（雑でOK版）
    ext = "png"
    if filename and "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()

    object_path = f"{uuid4().hex}.{ext}"

    # upload
    res = supabase.storage.from_(bucket).upload(
        path=object_path,
        file=file_bytes,
        file_options={
            "content-type": content_type,
            "upsert": False,
        },
    )

    # supabase-pyの戻りはバージョン差があるので安全に判定
    if getattr(res, "error", None):
        raise RuntimeError(str(res.error))

    # public URL（public bucketなのでこれで見れる）
    public = supabase.storage.from_(bucket).get_public_url(object_path)
    # public の形もバージョン差があるので吸収
    if isinstance(public, dict) and "publicUrl" in public:
        return public["publicUrl"]
    if hasattr(public, "public_url"):
        return public.public_url
    return str(public)

def extract_storage_path_from_public_url(public_url: str) -> str:
    """
    例:
    https://xxxx.supabase.co/storage/v1/object/public/uploads/abc/def.png
    -> abc/def.png を返す（bucket名 uploads は除外）
    """
    if not public_url:
        return ""

    path = urlparse(public_url).path  # /storage/v1/object/public/uploads/abc/def.png
    marker = f"/storage/v1/object/public/{SUPABASE_BUCKET}/"
    if marker not in path:
        return ""

    return path.split(marker, 1)[1]


def delete_file_by_public_url(public_url: str) -> None:
    storage_path = extract_storage_path_from_public_url(public_url)

    if not storage_path:
        raise RuntimeError("storage_path が空。URL形式か bucket 名が合ってない")

    res = supabase.storage.from_(SUPABASE_BUCKET).remove([storage_path])

    # supabase-py は失敗しても例外じゃなく、resに入ることがある
    if isinstance(res, dict) and res.get("error"):
        raise RuntimeError(f"Supabase remove error: {res['error']}")