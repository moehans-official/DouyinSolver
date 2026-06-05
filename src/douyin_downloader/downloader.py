"""抖音下载器核心类"""

import json
import re
from pathlib import Path
from typing import Callable, Optional, Union

import requests

from .models import DownloadProgress, ParseError, VideoInfo
from .utils import get_mobile_headers, normalize_url


class DouyinDownloader:
    """
    抖音视频/图集下载器
    
    使用移动端 User-Agent 访问分享页，无需 Cookie 即可获取无水印视频。
    
    Examples:
        >>> dl = DouyinDownloader()
        >>> info = dl.parse("https://www.douyin.com/video/xxxx")
        >>> print(info.play_url)
        >>> dl.download(info.play_url, "video.mp4")
    """
    
    BASE_URL = "https://www.iesdouyin.com/share/video/{aweme_id}/"
    
    def __init__(
        self,
        timeout: int = 15,
        session: Optional[requests.Session] = None,
    ):
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update(get_mobile_headers())
    
    def parse(self, url: str) -> VideoInfo:
        """解析抖音视频/图集信息"""
        aweme_id = normalize_url(url)
        data = self._fetch_share_page(aweme_id)
        return self._parse_video_info(data, aweme_id)
    
    def _fetch_share_page(self, aweme_id: str) -> dict:
        """获取分享页 SSR 数据"""
        url = self.BASE_URL.format(aweme_id=aweme_id)
        
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise ParseError(f"分享页请求失败: {e}", code=500)
        
        pattern = r'window\._ROUTER_DATA\s*=\s*(.*?)</script>'
        matches = re.search(pattern, resp.text, re.DOTALL)
        
        if not matches:
            raise ParseError("未找到 SSR 数据", code=404)
        
        try:
            data = json.loads(matches.group(1).strip())
        except json.JSONDecodeError as e:
            raise ParseError(f"JSON 解析失败: {e}", code=500)
        
        return data
    
    def _parse_video_info(self, data: dict, aweme_id: str) -> VideoInfo:
        """从 SSR 数据解析视频信息"""
        loader_data = data.get("loaderData", {})
        video_page = loader_data.get("video_(id)/page", {})
        
        if not video_page:
            raise ParseError("未找到视频页面数据", code=404)
        
        video_info_res = video_page.get("videoInfoRes", {})
        item_list = video_info_res.get("item_list", [])
        
        if not item_list:
            raise ParseError("视频不存在或已删除", code=404)
        
        item = item_list[0]
        
        # 作者信息
        author_info = item.get("author", {})
        author = author_info.get("nickname", "")
        author_id = author_info.get("unique_id", "")
        avatar = author_info.get("avatar_medium", {}).get("url_list", [""])[0]
        
        # 视频信息
        video_data = item.get("video", {})
        play_addr = video_data.get("play_addr", {})
        url_list = play_addr.get("url_list", [])
        
        play_url_wm = url_list[0] if url_list else ""
        play_url = play_url_wm.replace("playwm", "play") if play_url_wm else ""
        cover = video_data.get("cover", {}).get("url_list", [""])[0]
        
        # 图集模式
        images = []
        img_list = item.get("images", [])
        for img in img_list:
            urls = img.get("url_list", [])
            if urls:
                images.append(urls[0])
        
        # 音乐信息
        music_info = item.get("music")
        music = None
        if music_info:
            music = {
                "title": music_info.get("title", ""),
                "author": music_info.get("author", ""),
                "url": music_info.get("play_url", {}).get("url_list", [""])[0],
                "cover": music_info.get("cover_large", {}).get("url_list", [""])[0],
            }
        
        return VideoInfo(
            aweme_id=aweme_id,
            title=item.get("desc", ""),
            author=author,
            author_id=author_id,
            avatar=avatar,
            duration=video_data.get("duration", 0),
            cover=cover,
            play_url=play_url,
            play_url_watermark=play_url_wm,
            images=images,
            music=music,
        )
    
    def download(
        self,
        url: str,
        output_path: Union[str, Path],
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> Path:
        """下载视频/图片"""
        output_path = Path(output_path)
        
        resp = self.session.get(url, stream=True, timeout=self.timeout)
        resp.raise_for_status()
        
        total_size = int(resp.headers.get("content-length", 0))
        downloaded = 0
        
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress = DownloadProgress(
                            downloaded=downloaded,
                            total=total_size,
                            percentage=(downloaded / total_size) * 100,
                        )
                        progress_callback(progress)
        
        return output_path
    
    def download_video(
        self,
        info: VideoInfo,
        output_dir: Union[str, Path] = ".",
        filename: Optional[str] = None,
    ) -> Path:
        """下载视频"""
        if info.is_gallery:
            raise ParseError("该链接为图集")
        
        if not info.play_url:
            raise ParseError("无水印视频地址为空")
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not filename:
            filename = f"{info.aweme_id}_{info.author}"
        
        output_path = output_dir / f"{filename}.mp4"
        return self.download(info.play_url, output_path)
    
    def download_gallery(
        self,
        info: VideoInfo,
        output_dir: Union[str, Path] = ".",
    ) -> list[Path]:
        """下载图集"""
        if not info.is_gallery:
            raise ParseError("该链接不是图集")
        
        output_dir = Path(output_dir) / info.aweme_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        paths = []
        for i, url in enumerate(info.images, 1):
            ext = url.split("?")[0].split(".")[-1] or "jpg"
            output_path = output_dir / f"{i:02d}.{ext}"
            self.download(url, output_path)
            paths.append(output_path)
        
        return paths
