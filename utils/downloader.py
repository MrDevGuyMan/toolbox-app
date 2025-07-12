import os
import base64
import logging
from fastapi.responses import StreamingResponse
from yt_dlp import YoutubeDL
from fastapi import BackgroundTasks
from typing import Literal

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
        logging.info(f"Downloading: {percent}")
    elif d.get('status') == 'finished':
        logging.info("Download finished. Starting post-processing...")


def download_video(url: str, format_choice: Literal["mp3", "mp4"], background_tasks: BackgroundTasks):
    write_cookiefile()
    os.makedirs("downloads", exist_ok=True)

    ydl_opts = {
        'outtmpl': os.path.join("downloads", '%(title)s.%(ext)s'),
        'cookiefile': 'cookies.txt',
        'progress_hooks': [progress_hook],
        'noplaylist': True
    }

    if format_choice == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }]
        })
    else:
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4'

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if format_choice == 'mp3':
                file_path = os.path.splitext(file_path)[0] + '.mp3'

        logging.info(f"Download complete: {file_path}")

        def cleanup():
            try:
                os.remove(file_path)
                logging.info(f"Deleted file: {file_path}")
            except Exception as e:
                logging.warning(f"Cleanup failed: {e}")

        background_tasks.add_task(cleanup)

        return StreamingResponse(
            open(file_path, "rb"),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={os.path.basename(file_path)}"
            }
        )

    except Exception as e:
        logging.error(f"Download failed: {e}")
        raise e
