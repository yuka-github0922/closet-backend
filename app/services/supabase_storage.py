import os
from uuid import uuid4
from supabase import create_client


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
