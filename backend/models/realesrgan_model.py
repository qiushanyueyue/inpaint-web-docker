import os
import torch
from pathlib import Path
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer
from .device import DeviceDetector

class RealESRGANModel:
    def __init__(self, model_name="RealESRGAN_x4plus", device=None):
        self.model_name = model_name
        self.device = device if device else self._get_default_device()
        self.model = self._load_model()

    def _get_default_device(self):
        info = DeviceDetector.get_device_info()
        return torch.device(info["type"])

    def _load_model(self):
        # 模型路径
        weights_dir = Path(__file__).parent.parent / "weights"
        model_path = weights_dir / f"{self.model_name}.pth"
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found at: {model_path}")

        # RealESRGAN_x4plus配置
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        
        upsampler = RealESRGANer(
            scale=4,
            model_path=str(model_path),
            model=model,
            tile=0,  # 0 为不使用 tile，显存不足时可调大
            tile_pad=10,
            pre_pad=0,
            half=True if self.device.type != 'cpu' else False, # CPU 不支持 half
            device=self.device,
        )
        return upsampler

    def enhance(self, img, outscale=4):
        """
        执行超分辨率处理
        """
        try:
            output, _ = self.model.enhance(img, outscale=outscale)
            return output
        except RuntimeError as e:
            if "CUDA out of memory" in str(e):
                # 如果显存不够，尝试使用 tile 模式
                print("CUDA OOM, trying with tile...")
                self.model.tile = 512
                output, _ = self.model.enhance(img, outscale=outscale)
                self.model.tile = 0  # 恢复默认
                return output
            raise e

    def get_info(self):
        return {
            "name": self.model_name,
            "device": str(self.device)
        }

def get_model():
    return RealESRGANModel()
