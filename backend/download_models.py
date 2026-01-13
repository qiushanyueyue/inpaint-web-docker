import os
import urllib.request
import urllib.error
from pathlib import Path
import time

def download_file(url: str, dest_path: Path, max_retries: int = 3):
    """
    下载文件，支持重试和超时设置
    
    Args:
        url: 下载链接
        dest_path: 保存路径
        max_retries: 最大重试次数
    """
    if dest_path.exists():
        print(f"✓ {dest_path.name} already exists")
        return

    print(f"Downloading {dest_path.name}...")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    for attempt in range(max_retries):
        try:
            # 设置超时和 User-Agent
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            # 下载文件
            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                chunk_size = 8192
                
                with open(dest_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            percent = int(downloaded * 100 / total_size)
                            print(f"\rDownloading {dest_path.name}: {percent}%", end='')
            
            print(f"\n✓ Downloaded {dest_path.name}")
            return  # 下载成功，退出
            
        except (urllib.error.URLError, urllib.error.HTTPError, ConnectionError, TimeoutError) as e:
            print(f"\n⚠️  Attempt {attempt + 1}/{max_retries} failed: {e}")
            
            # 删除不完整的文件
            if dest_path.exists():
                os.remove(dest_path)
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # 递增等待时间: 2s, 4s, 6s
                print(f"   Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                print(f"\n❌ Failed to download {dest_path.name} after {max_retries} attempts")
                raise
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            if dest_path.exists():
                os.remove(dest_path)
            raise

def main():
    # Define model URLs and paths
    models = [
        {
            "name": "RealESRGAN_x4plus.pth",
            "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
            "target_dir": "weights"  # 放到 backend/weights/
        },
        {
            "name": "RealESRGAN_x4plus_anime_6B.pth",
            "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth",
            "target_dir": "weights"  # 放到 backend/weights/
        }
        # LaMa 模型由 simple-lama-inpainting 库自动下载,无需手动下载
    ]

    print("=" * 60)
    print("下载模型文件...")
    print("=" * 60)

    for model in models:
        # 确定目标目录(相对于此脚本)
        target_dir = Path(__file__).parent / model["target_dir"]
        target_dir.mkdir(exist_ok=True, parents=True)
        
        dest_path = target_dir / model["name"]
        download_file(model["url"], dest_path)

    print("\n" + "=" * 60)
    print("✓ 所有模型下载完成!")
    print("=" * 60)
    print("\n注意: LaMa Inpaint 模型由 simple-lama-inpainting 库自动管理")

if __name__ == "__main__":
    main()
