"""命令行接口"""

import argparse
import json
import sys
from pathlib import Path

from .downloader import DouyinDownloader
from .models import ParseError, VideoInfo


def format_output(info: VideoInfo, output_json: bool = False) -> str:
    """格式化输出"""
    if output_json:
        return json.dumps(info.to_dict(), ensure_ascii=False, indent=2)
    
    lines = [
        f"视频 ID: {info.aweme_id}",
        f"标题: {info.title[:60]}{'...' if len(info.title) > 60 else ''}",
        f"作者: {info.author} (@{info.author_id})",
    ]
    
    if info.is_gallery:
        lines.append(f"类型: 图集 ({len(info.images)} 张)")
        for i, img in enumerate(info.images[:5], 1):
            lines.append(f"  [{i}] {img}")
        if len(info.images) > 5:
            lines.append(f"  ... 还有 {len(info.images) - 5} 张")
    else:
        lines.extend([
            f"类型: 视频",
            f"无水印地址: {info.play_url}",
        ])
    
    if info.music:
        lines.append(f"背景音乐: {info.music['title']}")
    
    return "\n".join(lines)


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        prog="douyin-dl",
        description="抖音视频无水印下载工具",
    )
    parser.add_argument("input", help="视频链接或ID")
    parser.add_argument("-j", "--json", action="store_true", help="JSON 输出")
    parser.add_argument("-d", "--download", action="store_true", help="下载视频/图集")
    parser.add_argument("-o", "--output", default=".", help="输出目录")
    
    args = parser.parse_args()
    
    dl = DouyinDownloader()
    
    try:
        info = dl.parse(args.input)
        print(format_output(info, args.json))
        
        if args.download and not args.json:
            print(f"\n开始下载...")
            if info.is_gallery:
                paths = dl.download_gallery(info, args.output)
                print(f"图集已下载到: {paths[0].parent}")
            else:
                path = dl.download_video(info, args.output)
                print(f"视频已下载到: {path}")
                
    except ParseError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
