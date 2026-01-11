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
            "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
        },
        {
            "name": "RealESRGAN_x4plus_anime_6B.pth",
            "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth"
        }
    ]

    # Models directory (relative to this script)
    models_dir = Path(__file__).parent / "weights"
    models_dir.mkdir(exist_ok=True, parents=True)

    print("=" * 40)
    print("Downloading Real-ESRGAN models...")
    print("=" * 40)

    for model in models:
        dest_path = models_dir / model["name"]
        download_file(model["url"], dest_path)

    print("\nAll models downloaded successfully!")

if __name__ == "__main__":
    main()
