from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.services.container import get_local_upload_handler
from app.services.upload.local_upload import upload_store

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("")
async def upload_local_file(
    media: UploadFile = File(...),
    subtitle: Optional[UploadFile] = File(None),
):
    handler = get_local_upload_handler()
    try:
        data = await handler.save_upload(media, subtitle)
        return {"success": True, "data": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"success": False, "error": str(e)})
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": f"上传失败: {str(e)}"},
        )


@router.get("/{file_id}/stream")
async def stream_uploaded_file(file_id: str):
    record = upload_store.get(file_id)
    handler = get_local_upload_handler()
    if not record or not record.media_path.exists():
        raise HTTPException(status_code=404, detail={"success": False, "error": "文件不存在或已过期"})
    return FileResponse(
        path=str(record.media_path),
        media_type=handler.get_media_type(record),
        filename=f"{record.title}.{record.ext}",
    )
