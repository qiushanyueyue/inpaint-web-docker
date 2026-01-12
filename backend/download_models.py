import os
import urllib.request
import urllib.error
from pathlib import Path

def download_file(url: str, dest_path: Path):
    if dest_path.exists():
        print(f"✓ {dest_path.name} already exists")
        return

    print(f"Downloading {dest_path.name}...")
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Download with progress indicator
        def progress(count, block_size, total_size):
            percent = int(count * block_size * 100 / total_size)
            print(f"\rDownloading {dest_path.name}: {percent}%", end='')
            
        urllib.request.urlretrieve(url, dest_path, reporthook=progress)
        print(f"\n✓ Downloaded {dest_path.name}")
        
    except Exception as e:
        print(f"\n❌ Failed to download {dest_path.name}: {e}")
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
        },
        {
            "name": "migan.onnx",
            "url": "https://huggingface.co/lxfater/inpaint-web/resolve/main/migan.onnx",
            "target_dir": "weights"  # 放到 backend/weights/ 与其他模型统一
        }
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

if __name__ == "__main__":
    main()
