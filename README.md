# Douyin Downloader

抖音视频无水印下载 Python 库

使用移动端 User-Agent 解析分享页 SSR 数据，无需 Cookie 和 X-Bogus 签名。

## 安装

```bash
pip install douyin-downloader
```

## 快速开始

### Python API

```python
from douyin_downloader import DouyinDownloader

# 创建下载器实例
dl = DouyinDownloader()

# 解析视频
info = dl.parse("https://www.douyin.com/video/xxxxxxxxxx")

print(f"标题: {info.title}")
print(f"作者: {info.author}")
print(f"无水印地址: {info.play_url}")

# 下载视频
dl.download_video(info, output_dir="./downloads")
```

### 命令行

```bash
# 查看视频信息
douyin-dl "https://v.douyin.com/xxxxx"

# JSON 输出
douyin-dl "xxxxxx" --json

# 下载视频
douyin-dl "xxxxxx" --download --output ./downloads
```

## API 文档

### DouyinDownloader

```python
class DouyinDownloader(
    timeout: int = 15,
    session: Optional[Session] = None,
)
```

**方法**

- `parse(url: str) -> VideoInfo` - 解析视频信息
- `download_video(info: VideoInfo, output_dir=".", filename=None) -> Path` - 下载视频
- `download_gallery(info: VideoInfo, output_dir=".") -> list[Path]` - 下载图集

### VideoInfo

```python
@dataclass
class VideoInfo:
    aweme_id: str           # 视频ID
    title: str            # 标题
    author: str           # 作者昵称
    author_id: str        # 作者ID
    play_url: str         # 无水印地址
    play_url_watermark: str  # 带水印地址
    images: list[str]     # 图集图片列表
    music: Optional[dict]  # 音乐信息
    
    @property
    def is_gallery: bool  # 是否为图集
    @property
    def is_video: bool    # 是否为视频
```

## 高级用法

### 自定义 Session

```python
import requests
from douyin_downloader import DouyinDownloader

session = requests.Session()
session.headers.update({"User-Agent": "Custom/1.0"})

dl = DouyinDownloader(session=session)
```

### 下载进度回调

```python
def on_progress(p):
    print(f"{p.percentage:.1f}% ({p.downloaded}/{p.total})")

info = dl.parse("https://...")
dl.download(info.play_url, "video.mp4", progress_callback=on_progress)
```

### 批量处理

```python
urls = ["url1", "url2", "url3"]

for url in urls:
    try:
        info = dl.parse(url)
        dl.download_video(info, "./downloads")
        print(f"✓ {info.aweme_id}")
    except Exception as e:
        print(f"✗ {url}: {e}")
```

## 技术原理

1. **移动端 User-Agent** - iPhone Safari，避免反爬虫
2. **SSR 数据提取** - 从 `window._ROUTER_DATA` 解析
3. **无水印转换** - `playwm` → `play`

## License

MIT
