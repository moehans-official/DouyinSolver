"""工具函数"""

import re
from typing import Optional
from urllib.parse import urlparse

import requests

from .models import ParseError

# 正则表达式模式
PURE_ID_PATTERN = re.compile(r"^\d{15,20}$")
LONG_LINK_PATTERN = re.compile(r"/video/(\d+)")
SHORT_LINK_PATTERN = re.compile(r"v\.douyin\.com/([\w-]+)")

# 移动端 User-Agent (关键)
MOBILE_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 "
    "Mobile/15E148 Safari/604.1"
)


def extract_video_id(url: str) -> Optional[str]:
    """
    从各种格式的链接中提取视频ID
    
    Args:
        url: 抖音链接 (短链/长链/分享页)
        
    Returns:
        视频ID或None
        
    Examples:
        >>> extract_video_id("https://www.douyin.com/video/123456")
        '123456'
        >>> extract_video_id("https://v.douyin.com/xxxxx")
        '123456'  # 会跟随重定向
    """
    url = url.strip()
    
    # 纯ID
    if PURE_ID_PATTERN.match(url):
        return url
    
    # 补全协议
    if "://" not in url:
        url = "https://" + url
    
    parsed = urlparse(url)
    path = parsed.path or ""
    
    # 长链: /video/xxxx
    m = LONG_LINK_PATTERN.search(path)
    if m:
        return m.group(1)
    
    # 分享页: /share/video/xxxx
    m = re.search(r"/share/video/(\d+)", path)
    if m:
        return m.group(1)
    
    return None


def normalize_url(raw: str) -> str:
    """
    将各种输入格式统一转换为 aweme_id
    
    Args:
        raw: 短链/长链/纯ID
        
    Returns:
        aweme_id
        
    Raises:
        ParseError: 无法识别的格式
    """
    # 纯ID
    if PURE_ID_PATTERN.match(raw.strip()):
        return raw.strip()
    
    # 从链接提取
    video_id = extract_video_id(raw)
    if video_id:
        return video_id
    
    # 短链重定向
    if "v.douyin.com" in raw or "iesdouyin.com" in raw:
        return _resolve_short_link(raw)
    
    raise ParseError(f"无法识别的输入格式: {raw}")


def _resolve_short_link(url: str) -> str:
    """跟随短链重定向获取视频ID"""
    url = url.strip()
    if "://" not in url:
        url = "https://" + url
    
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": MOBILE_USER_AGENT},
            allow_redirects=True,
            timeout=15,
        )
        video_id = extract_video_id(resp.url)
        if video_id:
            return video_id
    except requests.RequestException as e:
        raise ParseError(f"短链解析失败: {e}")
    
    raise ParseError(f"无法从短链提取视频ID")


def get_mobile_headers() -> dict:
    """获取移动端请求头"""
    return {
        "User-Agent": MOBILE_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
