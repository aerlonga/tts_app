from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response, StreamingResponse

from app.schemas.media import (
    AssembleJobResponse,
    AssembleStatusResponse,
    AssetSearchRequest,
    AssetSearchResponse,
    EnhanceRequest,
    EnhanceResponse,
    GenerateScriptRequest,
    GenerateScriptResponse,
    GenerateShortRequest,
    GenerateShortResponse,
    GenerateTTSRequest,
    GenerateTTSStreamRequest,
)
from app.services.audio_service import audio_service
from app.services.media_service import media_service
from app.services.script_service import script_service
from app.services.short_service import short_service
from app.services.video_service import video_service


router = APIRouter(prefix="/media", tags=["media"])


@router.post("/enhance", response_model=EnhanceResponse)
def enhance(request: EnhanceRequest) -> EnhanceResponse:
    try:
        result = script_service.enhance_script(text=request.text, api_key=request.api_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return EnhanceResponse(enhanced_text=result["enhanced_text"])


@router.post("/generate-tts")
def generate_tts(request: GenerateTTSRequest) -> Response:
    try:
        result = audio_service.generate_tts_wav_bytes(text=request.text, voice=request.voice, api_key=request.api_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    headers = {"Content-Disposition": 'inline; filename="audio.wav"'}
    return Response(content=result["wav_bytes"], media_type="audio/wav", headers=headers)


@router.post("/generate-tts-stream")
def generate_tts_stream(request: GenerateTTSStreamRequest) -> StreamingResponse:
    try:
        generator = audio_service.stream_tts_events(
            text=request.text,
            voice=request.voice,
            api_key=request.api_key,
            session_id=request.session_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/generate-script", response_model=GenerateScriptResponse)
def generate_script(request: GenerateScriptRequest) -> GenerateScriptResponse:
    try:
        result = script_service.generate_script_from_url(url=str(request.url), api_key=request.api_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return GenerateScriptResponse(
        script=result["script"],
        image_prompts=result["image_prompts"],
        source_chars=result["source_chars"],
    )


@router.post("/generate-short", response_model=GenerateShortResponse)
def generate_short(request: GenerateShortRequest) -> GenerateShortResponse:
    try:
        result = short_service.generate_shorts(
            script=request.script,
            count=request.count,
            duration_seconds=request.duration_seconds,
            api_key=request.api_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return GenerateShortResponse(**result)


@router.post("/search-assets", response_model=AssetSearchResponse)
def search_assets(request: AssetSearchRequest) -> AssetSearchResponse:
    try:
        result = media_service.search_assets(keywords=request.keywords, collection=request.collection)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return AssetSearchResponse(**result)


@router.post("/assemble", response_model=AssembleJobResponse, status_code=202)
def assemble(
    audio: Annotated[UploadFile, File(...)],
    images: Annotated[list[UploadFile] | None, File()] = None,
    format: Annotated[str, Form()] = "long",
    manifest: Annotated[str | None, Form()] = None,
) -> AssembleJobResponse:
    try:
        job_id = video_service.create_assembly_job(
            audio_upload=audio,
            asset_uploads=images or [],
            manifest_str=manifest,
            video_format=format,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return AssembleJobResponse(job_id=job_id)


@router.get("/assemble/status/{job_id}", response_model=AssembleStatusResponse)
def assemble_status(job_id: str) -> AssembleStatusResponse:
    result = video_service.get_job_status(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Job nao encontrado.")
    return AssembleStatusResponse(**result)


@router.get("/assemble/download/{job_id}")
def assemble_download(job_id: str) -> FileResponse:
    result = video_service.get_download_path(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Arquivo de video nao encontrado ou job nao concluido.")
    path, filename = result
    return FileResponse(path=path, media_type="video/mp4", filename=filename)


@router.post("/generate-video", response_model=AssembleJobResponse, status_code=202)
def generate_video(
    api_key: Annotated[str | None, Form()] = None,
    script: Annotated[str, Form()] = "",
    voice: Annotated[str, Form()] = "Charon",
    format: Annotated[str, Form()] = "long",
    manifest: Annotated[str | None, Form()] = None,
    images: Annotated[list[UploadFile] | None, File()] = None,
) -> AssembleJobResponse:
    if not script.strip():
        raise HTTPException(status_code=400, detail="Roteiro aprovado e obrigatorio.")

    try:
        job_id = media_service.generate_video_job(
            script=script,
            voice=voice,
            api_key=api_key,
            asset_uploads=images or [],
            manifest_str=manifest,
            video_format=format,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return AssembleJobResponse(job_id=job_id)
