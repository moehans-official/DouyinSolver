# DouyinSolver

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/PyPI-v1.0.0-brightgreen?style=flat-square&logo=pypi" alt="PyPI">
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="MIT License">
</p>

<p align="center">
  <b>抖音视频无水印下载工具</b><br>
  无需登录 · 无需 Cookie · 支持视频和图集
</p>

---

## 安装

```bash
pip install DouyinSolver
```

---

## 快速开始

### 命令行

```bash
# 解析视频信息
douyin-dl "https://www.douyin.com/video/xxxxxxxxxx"

# JSON 输出
douyin-dl "xxxxxxxxxx" --json

# 下载视频到指定目录
douyin-dl "xxxxxxxxxx" --download --output ./downloads
```

### Python API

```python
from douyin_downloader import DouyinDownloader

# 创建下载器
dl = DouyinDownloader()

# 解析视频
info = dl.parse("https://v.douyin.com/xxxxx")

print(f"标题: {info.title}")
print(f"作者: {info.author}")
print(f"无水印地址: {info.play_url}")

# 下载视频
dl.download_video(info, "./downloads")
```

---

## 支持的链接格式

- 短链接: `https://v.douyin.com/xxxxx`
- 长链接: `https://www.douyin.com/video/xxxxxxxxxx`
- 纯视频 ID: `xxxxxxxxxx`

---

## API 参考

### DouyinDownloader

```python
class DouyinDownloader(
    timeout: int = 15,
    session: Optional[requests.Session] = None
)
```

| 方法 | 说明 |
|------|------|
| `parse(url: str) -> VideoInfo` | 解析视频/图集信息 |
| `download_video(info: VideoInfo, output_dir=".", filename=None) -> Path` | 下载视频 |
| `download_gallery(info: VideoInfo, output_dir=".") -> list[Path]` | 下载图集 |
| `download(url: str, output_path: Path, progress_callback=None) -> Path` | 下载任意 URL |

### VideoInfo

```python
@dataclass
class VideoInfo:
    aweme_id: str                # 视频 ID
    title: str                   # 标题/描述
    author: str                  # 作者昵称
    author_id: str               # 作者抖音号
    avatar: str                  # 作者头像 URL
    duration: int               # 时长（毫秒）
    cover: str                   # 封面 URL
    play_url: str                # 无水印视频地址
    play_url_watermark: str     # 带水印视频地址
    images: list[str]            # 图集图片列表
    music: Optional[dict]        # 音乐信息
    
    @property
    def is_gallery: bool         # 是否为图集
    @property
    def is_video: bool           # 是否为视频
    
    def to_dict() -> dict        # 转为字典
```

---

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
def on_progress(progress):
    print(f"{progress.percentage:.1f}%")

info = dl.parse("https://...")
dl.download(info.play_url, "video.mp4", progress_callback=on_progress)
```

### 批量下载

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

---

## 免责声明

本工具仅供学习研究使用，请遵守相关法律法规和平台使用条款。使用者应确保已获得必要授权，产生的任何后果均由使用者自行承担。

---

## License

MIT License - 详见 [LICENSE](LICENSE)

---

**GitHub**: https://github.com/moehans-official/DouyinSolver  
**PyPI**: https://pypi.org/project/DouyinSolver/
