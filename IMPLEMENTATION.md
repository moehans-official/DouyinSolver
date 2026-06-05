# DouyinSolver 实现文档

> 记录从零开始开发抖音视频下载工具的完整历程

---

## 目录

1. [需求分析](#需求分析)
2. [技术调研](#技术调研)
3. [开发历程](#开发历程)
4. [遇到的问题](#遇到的问题)
5. [解决方案](#解决方案)
6. [优化迭代](#优化迭代)
7. [最终架构](#最终架构)

---

## 需求分析

### 初始需求

用户希望实现一个抖音视频直链解析工具，要求：
- 支持短链、长链、纯视频 ID 三种输入
- 无需登录态（无 Cookie）
- 获取无水印视频地址
- 支持画质选择（1080p/720p/540p/360p）

### 参考方案

用户提供了一份技术文档，描述了通过分享页 SSR 数据获取视频地址的方案：
1. 获取 `ttwid` 匿名设备标识
2. 访问分享页 `https://www.iesdouyin.com/share/video/{id}/`
3. 提取 HTML 中的 `window._ROUTER_DATA`
4. 从 `video.play_addr.url_list` 获取播放地址
5. 画质探测和 CDN 直链获取

---

## 技术调研

### 第一阶段：验证分享页方案

**尝试 1：桌面端 User-Agent**

```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0"
}
```

**结果**：返回混淆 JavaScript（`_$jsvmprt`），无法提取 SSR 数据。

**尝试 2：移动端 User-Agent**

```python
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15"
}
```

**结果**：成功返回 SSR 数据！

### 关键发现

| 平台 | User-Agent | 返回内容 |
|------|-----------|---------|
| 桌面端 | Chrome/Windows | 混淆 JavaScript |
| 移动端 | iPhone Safari | SSR JSON 数据 |

---

## 开发历程

### Day 1：基础实现

**实现内容：**
1. 输入格式归一化（短链/长链/纯 ID → aweme_id）
2. ttwid 获取（通过 `ttwid.bytedance.com` 注册）
3. 分享页请求和 SSR 数据提取
4. 播放地址解析

**代码结构：**
```
src/parser.py
├── normalize_input()   # 输入处理
├── get_ttwid()         # 设备标识
├── fetch_share_page()  # 获取分享页
├── extract_ssr_data()  # 提取 SSR 数据
└── extract_play_urls() # 获取播放地址
```

### Day 2：遇到第一个问题

**问题**：桌面端请求返回混淆 JavaScript，无法解析。

**错误信息：**
```
HTML 中包含: var glb;(glb="undefined"==typeof window?global:window)._$jsvmprt(...)
```

**分析**：抖音对桌面端启用了反爬虫机制，返回混淆代码而非 SSR 数据。

**解决**：改用移动端 User-Agent。

### Day 3：参考开源项目

在 GitHub 上找到参考项目 [jiuhunwl/short_videos](https://github.com/jiuhunwl/short_videos)。

**关键发现**：
该项目 `api/douyin/No Cookie/douyin.php` 使用了移动端 User-Agent，无需 Cookie 即可工作。

**验证：**
```bash
curl -H "User-Agent: Mozilla/5.0 (iPhone...)" \
     https://www.iesdouyin.com/share/video/{id}/
```

**结果**：成功返回包含 `_ROUTER_DATA` 的 HTML！

### Day 4：重构代码

**优化点：**
1. 移除 ttwid 获取逻辑（移动端不需要）
2. 简化代码结构
3. 添加无水印转换（`playwm` → `play`）
4. 支持图集模式

**新的代码结构：**
```
src/douyin_downloader/
├── __init__.py       # 包入口
├── models.py         # VideoInfo, ParseError
├── utils.py          # normalize_url, extract_video_id
├── downloader.py     # DouyinDownloader 类
└── cli.py            # 命令行接口
```

### Day 5：打包为 Python 库

**添加文件：**
- `pyproject.toml` - 标准包配置
- `README.md` - 文档
- `main.py` - CLI 入口

**配置：**
```toml
[project]
name = "douyin-downloader"
version = "1.0.0"
description = "抖音视频无水印下载库"

[project.scripts]
douyin-dl = "douyin_downloader.cli:main"
```

### Day 6：测试和发布

**测试：**
```bash
pip install -e .
douyin-dl --help
```

**发布到 GitHub：**
```bash
git remote add origin https://github.com/moehans-official/DouyinSolver.git
git push -u origin main
```

---

## 遇到的问题

### 问题 1：桌面端返回混淆 JavaScript

**现象：**
请求分享页返回的不是 SSR 数据，而是混淆的 JavaScript 代码：

```html
<script>
var glb;(glb="undefined"==typeof window?global:window)._$jsvmprt=function(b,e,f){...}
</script>
```

**原因：**
抖音对桌面端 User-Agent 启用了反爬虫机制，返回混淆代码执行后才会渲染页面。

**解决：**
使用移动端 User-Agent（iPhone Safari）。

### 问题 2：短链重定向处理

**现象：**
短链 `v.douyin.com/xxxxx` 重定向后的 URL 包含 `aweme://` 协议，不是标准的 HTTP URL。

**解决：**
使用 `requests.get()` 的 `allow_redirects=True` 自动跟随重定向，然后从最终 URL 提取视频 ID。

### 问题 3：SSR 数据结构路径

**现象：**
视频数据在 SSR JSON 中的路径复杂：
```python
data['loaderData']['video_(id)/page']['videoInfoRes']['item_list'][0]
```

**解决：**
使用 `.get()` 方法逐级访问，每层都检查是否存在，避免 KeyError。

### 问题 4：图集模式识别

**现象：**
有些抖音链接是图集而非视频，需要不同的处理方式。

**解决：**
通过 `item.get('images')` 判断是否为图集：
```python
@property
def is_gallery(self) -> bool:
    return len(self.images) > 0
```

### 问题 5：无水印地址获取

**现象：**
SSR 数据中返回的播放地址是带水印的（包含 `playwm`）。

**解决：**
字符串替换 `playwm` 为 `play`：
```python
play_url = play_url_wm.replace("playwm", "play")
```

---

## 解决方案总结

### 核心技术点

1. **移动端 User-Agent 绕过反爬虫**
   ```python
   MOBILE_USER_AGENT = (
       "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
       "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 "
       "Mobile/15E148 Safari/604.1"
   )
   ```

2. **SSR 数据正则提取**
   ```python
   pattern = r'window\._ROUTER_DATA\s*=\s*(.*?)</script>'
   matches = re.search(pattern, html, re.DOTALL)
   data = json.loads(matches.group(1).strip())
   ```

3. **无水印地址转换**
   ```python
   # 带水印: https://.../playwm/?...
   # 无水印: https://.../play/?...
   play_url = play_url_wm.replace("playwm", "play")
   ```

### 架构设计

```
┌─────────────────────────────────────────┐
│           DouyinDownloader              │
├─────────────────────────────────────────┤
│  - parse(url) -> VideoInfo              │
│  - download_video(info) -> Path           │
│  - download_gallery(info) -> list[Path]   │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│              VideoInfo                  │
├─────────────────────────────────────────┤
│  - aweme_id, title, author              │
│  - play_url (no watermark)               │
│  - images (gallery mode)                 │
│  - is_video / is_gallery                │
└─────────────────────────────────────────┘
```

---

## 优化迭代

### 版本 1.0

**功能：**
- 基础解析（视频 + 图集）
- 命令行工具
- Python API
- 下载进度回调

**改进空间：**
- 异步下载
- 批量下载
- 重试机制
- 代理支持

### 未来规划

1. **v1.1** - 添加异步支持（asyncio + aiohttp）
2. **v1.2** - 添加批量下载和并发控制
3. **v1.3** - 添加代理和重试机制
4. **v1.4** - 发布到 PyPI

---

## 最终架构

```
DouyinSolver/
├── src/douyin_downloader/        # 核心包
│   ├── __init__.py               # 导出 API
│   ├── models.py                 # 数据模型
│   ├── utils.py                  # 工具函数
│   ├── downloader.py             # 下载器类
│   └── cli.py                    # 命令行
├── pyproject.toml                # 包配置
├── README.md                     # 使用文档
├── IMPLEMENTATION.md             # 实现文档
└── main.py                       # CLI 入口
```

### 使用方式

**命令行：**
```bash
douyin-dl "url" --download --output ./downloads
```

**Python：**
```python
from douyin_downloader import DouyinDownloader

dl = DouyinDownloader()
info = dl.parse("url")
dl.download_video(info, "./downloads")
```

---

## 总结

### 开发时间线

| 日期 | 内容 |
|------|------|
| Day 1 | 基础实现，遇到桌面端反爬虫 |
| Day 2 | 发现移动端方案 |
| Day 3 | 参考开源项目，验证可行性 |
| Day 4 | 重构代码，移除 ttwid，添加图集支持 |
| Day 5 | 打包为 Python 库 |
| Day 6 | 测试，发布到 GitHub |

### 核心经验

1. **User-Agent 是关键** - 移动端 UA 可以绕过大部分反爬虫
2. **参考开源项目** - jiuhunwl/short_videos 提供了重要思路
3. **简化比复杂好** - 移除不必要的 ttwid 逻辑，代码更简洁
4. **错误处理** - 每层都检查，避免 KeyError

### 技术栈

- Python 3.8+
- requests
- dataclasses
- pathlib
- pyproject.toml (PEP 621)

---

**作者**: ksduqiao@gmail.com  
**仓库**: https://github.com/moehans-official/DouyinSolver  
**许可证**: MIT
