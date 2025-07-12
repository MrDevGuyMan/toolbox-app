import os
import base64
import logging
from fastapi.responses import StreamingResponse
from yt_dlp import YoutubeDL
from typing import Literal

# Configure logging
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)


def write_cookiefile():
    b64 = os.getenv("YOUTUBE_COOKIES_B64")
    if b64:
        with open("cookies.txt", "wb") as f:
            f.write(base64.b64decode(b64))
            logging.info("cookies.txt written from environment variable.")


def progress_hook(d):
    if d.get('status') == 'downloading':
        percent = d.get('_percent_str', '').strip()
        logging.info(f"Downloading: {percent} complete")
    elif d.get('status') == 'finished':
        logging.info(
            "Download finished; starting post-processing if required...")


def download_video(url: str, format_choice: Literal["mp3", "mp4"]) -> str:
    write_cookiefile()
    os.makedirs("downloads", exist_ok=True)

    ydl_opts = {
        'outtmpl': os.path.join("downloads", '%(title)s.%(ext)s'),
        'cookiefile': 'cookies.txt',
        'progress_hooks': [progress_hook],
        'noplaylist': True,
    }

    if format_choice == 'mp3':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4'

    try:
        with YoutubeDL(ydl_opts) as ydl:
            logging.info(f"Starting extraction for URL: {url}")
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if format_choice == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'

            logging.info(f"File saved as: {filename}")

            if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                raise Exception("Download failed or file incomplete")

            return filename
    except Exception as e:
        logging.error(f"Download failed: {e}")
        raise e


def stream_file(file_path: str) -> StreamingResponse:
    file = open(file_path, "rb")
    return StreamingResponse(
        file,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={os.path.basename(file_path)}"
        }
    )
