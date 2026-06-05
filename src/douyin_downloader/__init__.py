"""
抖音视频无水印下载库

使用移动端 User-Agent 解析抖音分享页 SSR 数据，
无需 Cookie 和 X-Bogus 签名即可获取无水印视频地址。

示例:
    >>> from douyin_downloader import DouyinDownloader
    >>> dl = DouyinDownloader()
    >>> info = dl.parse("https://www.douyin.com/video/xxxxxx")
    >>> print(info.play_url)

作者: OpenCode
许可证: MIT
"""

from .downloader import DouyinDownloader
from .models import VideoInfo, ParseError
from .utils import normalize_url, extract_video_id

__version__ = "1.0.0"
__all__ = [
    "DouyinDownloader",
    "VideoInfo",
    "ParseError",
    "normalize_url",
    "extract_video_id",
]
