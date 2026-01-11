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
        
        Args:
            img: PIL Image 或 numpy 数组（BGR 格式）
            outscale: 放大倍数
            
        Returns:
            PIL Image: 放大后的图像
        """
        import numpy as np
        from PIL import Image
        
        # 如果是 PIL Image，转换为 numpy 数组（BGR 格式）
        if hasattr(img, 'mode'):  # PIL Image
            # PIL Image 是 RGB 格式，需要转换为 BGR（OpenCV 格式）
            img_np = np.array(img)
            if len(img_np.shape) == 3 and img_np.shape[2] == 3:
                img_np = img_np[:, :, ::-1]  # RGB -> BGR
        else:
            img_np = img
        
        try:
            output, _ = self.model.enhance(img_np, outscale=outscale)
            
            # 将输出从 BGR 转换回 RGB，然后转为 PIL Image
            if len(output.shape) == 3 and output.shape[2] == 3:
                output = output[:, :, ::-1]  # BGR -> RGB
            
            return Image.fromarray(output)
        except RuntimeError as e:
            if "CUDA out of memory" in str(e):
                # 如果显存不够，尝试使用 tile 模式
                print("CUDA OOM, trying with tile...")
                self.model.tile = 512
                output, _ = self.model.enhance(img_np, outscale=outscale)
                self.model.tile = 0  # 恢复默认
                
                # 转换回 RGB 和 PIL Image
                if len(output.shape) == 3 and output.shape[2] == 3:
                    output = output[:, :, ::-1]
                return Image.fromarray(output)
            raise e

    def get_info(self):
        return {
            "name": self.model_name,
            "device": str(self.device)
        }

def get_model():
    return RealESRGANModel()
