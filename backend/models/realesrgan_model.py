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
        
        # IMPORTANT: 默认使用 tile 模式以避免显存不足
        # GTX 1070 8GB 建议使用 tile=400，可根据实际显存调整
        # tile=0 表示不使用 tile，适合大显存 GPU
        upsampler = RealESRGANer(
            scale=4,
            model_path=str(model_path),
            model=model,
            tile=400,  # 默认使用 tile 模式，避免大图像导致 OOM
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
            # 处理前清理 CUDA 缓存
            if self.device.type == 'cuda':
                torch.cuda.empty_cache()
                import gc
                gc.collect()
            
            output, _ = self.model.enhance(img_np, outscale=outscale)
            
            # 将输出从 BGR 转换回 RGB，然后转为 PIL Image
            if len(output.shape) == 3 and output.shape[2] == 3:
                output = output[:, :, ::-1]  # BGR -> RGB
            
            return Image.fromarray(output)
        except RuntimeError as e:
            if "CUDA out of memory" in str(e) or "out of memory" in str(e).lower():
                # 如果显存不够，尝试使用更小的 tile
                print(f"\u26a0\ufe0f CUDA OOM，尝试减小 tile 大小...")
                
                # 清理显存
                if self.device.type == 'cuda':
                    torch.cuda.empty_cache()
                    import gc
                    gc.collect()
                
                # 尝试更小的 tile
                original_tile = self.model.tile
                for tile_size in [256, 192, 128]:
                    try:
                        print(f"   尝试 tile={tile_size}...")
                        self.model.tile = tile_size
                        output, _ = self.model.enhance(img_np, outscale=outscale)
                        
                        # 恢复原始设置
                        self.model.tile = original_tile
                        
                        # 转换回 RGB 和 PIL Image
                        if len(output.shape) == 3 and output.shape[2] == 3:
                            output = output[:, :, ::-1]
                        return Image.fromarray(output)
                    except RuntimeError:
                        # 继续尝试更小的 tile
                        if self.device.type == 'cuda':
                            torch.cuda.empty_cache()
                        continue
                
                # 所有 tile 大小都失败
                self.model.tile = original_tile
                raise RuntimeError(
                    f"\u663e\u5b58\u4e0d\u8db3: \u56fe\u7247\u5c3a\u5bf8 {img_np.shape[1]}x{img_np.shape[0]} \u592a\u5927\uff0c\u8bf7\u5c1d\u8bd5\u7f29\u5c0f\u56fe\u7247\u540e\u91cd\u8bd5"
                )
            raise e

    def get_info(self):
        return {
            "name": self.model_name,
            "device": str(self.device)
        }

def get_model():
    return RealESRGANModel()
