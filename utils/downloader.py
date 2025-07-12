import os
import uuid
import zipfile
import shutil
import tempfile
import logging
from fastapi.responses import StreamingResponse
from yt_dlp import YoutubeDL, DownloadError

# Optional: Enable logs during development
logging.basicConfig(level=logging.INFO)


def sanitize_filename(name):
    return "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).rstrip()


def download_video(url: str, format_choice: str) -> StreamingResponse:
    temp_dir = tempfile.mkdtemp()
    audio_only = format_choice == "mp3"

    # Configure yt_dlp options
    ydl_opts = {
        "outtmpl": os.path.join(temp_dir, "%(title).100s.%(ext)s"),
        "noplaylist": False,
        "format": "bestaudio/best" if audio_only else "bestvideo+bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [lambda d: logging.info(f"{d.get('status')}: {d.get('_percent_str')}")],
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }] if audio_only else []
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if "entries" in info:
                entries = info["entries"]
                filenames = [ydl.prepare_filename(e) for e in entries]
            else:
                filenames = [ydl.prepare_filename(info)]
                if audio_only:
                    filenames[0] = os.path.splitext(filenames[0])[0] + ".mp3"

        # Playlist? => ZIP
        if len(filenames) > 1:
            zip_name = sanitize_filename(
                info.get("title", f"playlist_{uuid.uuid4()}")) + ".zip"
            zip_path = os.path.join(temp_dir, zip_name)
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for f in filenames:
                    zipf.write(f, arcname=os.path.basename(f))
            final_path = zip_path
            download_name = zip_name
        else:
            final_path = filenames[0]
            download_name = os.path.basename(final_path)

        # Return file as StreamingResponse
        def file_stream():
            with open(final_path, "rb") as f:
                yield from f
            shutil.rmtree(temp_dir)

        return StreamingResponse(
            file_stream(),
            media_type="application/zip" if final_path.endswith(
                ".zip") else "application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{download_name}"'}
        )

    except DownloadError as e:
        shutil.rmtree(temp_dir)
        raise Exception(f"Download failed: {str(e)}")
    except Exception as e:
        shutil.rmtree(temp_dir)
        raise e
