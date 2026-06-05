"""数据模型定义"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VideoInfo:
    """
    抖音视频/图集信息
    
    Attributes:
        aweme_id: 视频唯一ID
        title: 视频标题/描述
        author: 作者昵称
        author_id: 作者抖音号
        avatar: 作者头像URL
        duration: 视频时长(毫秒)
        cover: 封面图URL
        play_url: 无水印视频地址
        play_url_watermark: 带水印视频地址
        music: 背景音乐信息
        images: 图集图片URL列表(仅图集模式)
    """
    
    aweme_id: str
    title: str = ""
    author: str = ""
    author_id: str = ""
    avatar: str = ""
    duration: int = 0
    cover: str = ""
    play_url: str = ""  # 无水印视频地址
    play_url_watermark: str = ""  # 带水印地址
    music: Optional[dict] = None
    images: list[str] = field(default_factory=list)
    
    @property
    def is_gallery(self) -> bool:
        """是否为图集模式"""
        return len(self.images) > 0
    
    @property
    def is_video(self) -> bool:
        """是否为视频模式"""
        return not self.is_gallery and bool(self.play_url)
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "aweme_id": self.aweme_id,
            "title": self.title,
            "author": self.author,
            "author_id": self.author_id,
            "avatar": self.avatar,
            "duration": self.duration,
            "cover": self.cover,
            "play_url": self.play_url,
            "play_url_watermark": self.play_url_watermark,
            "music": self.music,
            "images": self.images,
            "is_gallery": self.is_gallery,
            "is_video": self.is_video,
        }


class ParseError(Exception):
    """解析错误"""
    
    def __init__(self, message: str, code: int = 0):
        self.message = message
        self.code = code
        super().__init__(self.message)
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}" if self.code else self.message


@dataclass
class DownloadProgress:
    """下载进度信息"""
    
    downloaded: int = 0
    total: int = 0
    percentage: float = 0.0
    speed: str = "0 B/s"
    
    @property
    def completed(self) -> bool:
        return self.total > 0 and self.downloaded >= self.total
