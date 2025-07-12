import yt_dlp
import os
import logging
import base64
from fastapi.responses import StreamingResponse
from fastapi import BackgroundTasks

# Configure logging
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)


def write_cookiefile():
    """
    Write YouTube cookies from environment variable to cookies.txt file.
    """
    b64 = os.getenv("YOUTUBE_COOKIES_B64")
    if b64:
        with open("cookies.txt", "wb") as f:
            f.write(base64.b64decode(b64))


def progress_hook(d):
    """
    Display download progress information.
    """
    if d.get('status') == 'downloading':
        percent = d.get('_percent_str', '').strip()
        logging.info(f"Downloading: {percent} complete")
    elif d.get('status') == 'finished':
        logging.info("Download finished; starting post-processing...")


def download_video(url, format_choice, background_tasks: BackgroundTasks):
    """
    Download a video or extract audio from a URL using yt-dlp and stream it to user.

    Parameters:
        url (str): YouTube video URL
        format_choice (str): 'mp4' or 'mp3'
        background_tasks (BackgroundTasks): FastAPI task handler

    Returns:
        StreamingResponse: File streamed to user's browser
    """
    write_cookiefile()
    os.makedirs("downloads", exist_ok=True)

    ydl_opts = {
        'outtmpl': os.path.join("downloads", '%(title)s.%(ext)s'),
        'cookiefile': 'cookies.txt',
        'progress_hooks': [progress_hook],
        'noplaylist': True
    }

    if format_choice == 'mp3':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }]
    else:
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logging.info(f"Starting extraction for URL: {url}")
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if format_choice == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'
            logging.info(f"File saved as: {filename}")

        download_name = os.path.basename(filename)

        def file_stream():
            with open(filename, "rb") as f:
                yield from f

        # Schedule file cleanup after response
        background_tasks.add_task(os.remove, filename)

        return StreamingResponse(
            file_stream(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename=\"{download_name}\""
            }
        )

    except Exception as e:
        logging.error(f"Download failed: {e}")
        raise e
