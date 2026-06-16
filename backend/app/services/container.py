"""全局服务单例工厂，避免 api 层循环依赖。"""

import os
import shutil

from app.core.config import get_settings
from app.services.ai.subtitles import SubtitleFetcher
from app.services.ai.summarizer import VideoAnalyzer
from app.services.ai.transcriber import Transcriber
from app.services.upload.local_upload import LocalUploadHandler, upload_store
from app.services.video.bilibili import BilibiliParser
from app.services.video.douyin import DouyinParser
from app.services.video.downloader import VideoDownloader

_settings = get_settings()

_downloader: VideoDownloader | None = None
_douyin_parser: DouyinParser | None = None
_bilibili_parser: BilibiliParser | None = None
_subtitle_fetcher: SubtitleFetcher | None = None
_transcriber: Transcriber | None = None
_video_analyzer: VideoAnalyzer | None = None
_local_upload_handler: LocalUploadHandler | None = None


def get_downloader() -> VideoDownloader:
    global _downloader
    if _downloader is None:
        _downloader = VideoDownloader()
    return _downloader


def get_douyin_parser() -> DouyinParser:
    global _douyin_parser
    if _douyin_parser is None:
        _douyin_parser = DouyinParser(download_dir=get_downloader().DOWNLOAD_DIR)
    return _douyin_parser


def get_bilibili_parser() -> BilibiliParser:
    global _bilibili_parser
    if _bilibili_parser is None:
        _bilibili_parser = BilibiliParser(download_dir=get_downloader().DOWNLOAD_DIR)
    return _bilibili_parser


def get_subtitle_fetcher() -> SubtitleFetcher:
    global _subtitle_fetcher
    if _subtitle_fetcher is None:
        _subtitle_fetcher = SubtitleFetcher(
            get_downloader().DOWNLOAD_DIR,
            get_bilibili_parser(),
        )
    return _subtitle_fetcher


def get_transcriber() -> Transcriber:
    global _transcriber
    if _transcriber is None:
        downloader = get_downloader()
        _transcriber = Transcriber(
            download_dir=downloader.DOWNLOAD_DIR,
            bilibili_parser=get_bilibili_parser(),
            douyin_parser=get_douyin_parser(),
            ffmpeg_path=downloader.ffmpeg_path,
            model_size=_settings.whisper_model,
            max_duration=_settings.whisper_max_duration,
            beam_size=_settings.whisper_beam_size,
        )
    return _transcriber


def get_video_analyzer() -> VideoAnalyzer:
    global _video_analyzer
    if _video_analyzer is None:
        _video_analyzer = VideoAnalyzer(get_subtitle_fetcher(), get_transcriber())
    return _video_analyzer


def get_local_upload_handler() -> LocalUploadHandler:
    global _local_upload_handler
    if _local_upload_handler is None:
        downloader = get_downloader()
        _local_upload_handler = LocalUploadHandler(
            download_dir=downloader.DOWNLOAD_DIR,
            ffmpeg_path=downloader.ffmpeg_path,
            max_size_mb=_settings.upload_max_size_mb,
            max_duration=_settings.upload_max_duration,
        )
    return _local_upload_handler


def cleanup_on_shutdown() -> None:
    upload_store.cleanup_all()
    download_dir = get_downloader().DOWNLOAD_DIR
    if os.path.exists(download_dir):
        for name in os.listdir(download_dir):
            path = os.path.join(download_dir, name)
            try:
                if os.path.isdir(path) and name.startswith("upload_"):
                    shutil.rmtree(path, ignore_errors=True)
                elif os.path.isfile(path):
                    os.remove(path)
            except OSError:
                pass
