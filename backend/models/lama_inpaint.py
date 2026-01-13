"""
LaMa (Resolution-robust Large Mask Inpainting) 实现
基于官方 advimman/lama 实现
支持 GPU (CUDA) 和 CPU
"""
import torch
import numpy as np
from PIL import Image
import os
from typing import Optional
import urllib.request
from pathlib import Path


class LamaInpaint:
    """LaMa Inpainting 模型"""
    
    MODEL_URL = "https://github.com/enesmsahin/simple-lama-inpainting/releases/download/v0.1.0/big-lama.pt"
    
    def __init__(self, model_path: Optional[str] = None, device: str = "cuda"):
        """
        初始化 LaMa Inpaint
        
        Args:
            model_path: 模型文件路径。如果为 None,使用默认路径
            device: 'cuda' 或 'cpu'
        """
        # 设置设备
        if device == "cuda" and torch.cuda.is_available():
            self.device = torch.device("cuda")
            self.actual_device = "cuda"
            print(f"✓ 使用 CUDA 加速 (GPU: {torch.cuda.get_device_name(0)})")
        else:
            self.device = torch.device("cpu")
            self.actual_device = "cpu"
            print("✓ 使用 CPU 模式")
        
        # 确定模型路径
        if model_path is None:
            current_dir = Path(__file__).parent.parent
            model_path = current_dir / "weights" / "big-lama.pt"
            model_path = str(model_path.resolve())
        
        self.model_path = model_path
        
        # 检查模型文件是否存在
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"LaMa 模型文件不存在: {model_path}\n"
                f"请运行: python backend/download_models.py"
            )
        
        # 加载模型
        print(f"📦 加载 LaMa 模型: {os.path.basename(model_path)}")
        try:
            self.model = torch.jit.load(model_path, map_location=self.device)
            self.model.eval()
            print("✓ LaMa 模型加载成功")
        except Exception as e:
            raise RuntimeError(f"LaMa 模型加载失败: {e}")
    
    def get_info(self) -> dict:
        """获取模型信息"""
        return {
            "name": "LaMa (Resolution-robust Large Mask Inpainting)",
            "device": self.actual_device,
            "model_path": self.model_path
        }
    
    @staticmethod
    def download_model(save_path: str) -> None:
        """
        下载 LaMa 预训练模型
        
        Args:
            save_path: 保存路径
        """
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        print(f"📥 下载 LaMa 模型...")
        print(f"   URL: {LamaInpaint.MODEL_URL}")
        print(f"   保存到: {save_path}")
        
        try:
            urllib.request.urlretrieve(
                LamaInpaint.MODEL_URL,
                save_path,
                reporthook=lambda count, block_size, total_size: print(
                    f"\r   进度: {count * block_size / total_size * 100:.1f}%",
                    end=""
                ) if total_size > 0 else None
            )
            print("\n✓ 模型下载完成")
        except Exception as e:
            raise RuntimeError(f"模型下载失败: {e}")
    
    def inpaint(
        self, 
        image: Image.Image, 
        mask: Image.Image
    ) -> Image.Image:
        """
        执行 Inpaint 修复
        
        Args:
            image: 原始图片(PIL Image, RGB)
            mask: 遮罩图片(PIL Image, L/灰度, 白色=需要修复的区域)
            
        Returns:
            修复后的图片(PIL Image)
        """
        # 获取原始尺寸
        orig_width, orig_height = image.size
        print(f"   LaMa Inpaint 处理: {orig_width}x{orig_height}")
        
        # 转换为 RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        if mask.mode != 'L':
            mask = mask.convert('L')
        
        # 转换为 numpy 数组
        img_array = np.array(image).astype(np.float32) / 255.0
        mask_array = np.array(mask).astype(np.float32) / 255.0
        
        # 转换为 torch tensor [1, 3, H, W]
        img_tensor = torch.from_numpy(img_array).permute(2, 0, 1).unsqueeze(0)
        mask_tensor = torch.from_numpy(mask_array).unsqueeze(0).unsqueeze(0)
        
        # 移动到设备
        img_tensor = img_tensor.to(self.device)
        mask_tensor = mask_tensor.to(self.device)
        
        print(f"   mask 非零像素: {(mask_array > 0.5).sum()}/{mask_array.size}")
        
        # 推理
        with torch.no_grad():
            # LaMa 模型输入: image 和 mask
            output = self.model(img_tensor, mask_tensor)
        
        # 转换回 numpy
        output_np = output.squeeze(0).permute(1, 2, 0).cpu().numpy()
        
        # 转换回 [0, 255]
        output_np = np.clip(output_np * 255.0, 0, 255).astype(np.uint8)
        
        # 转换为 PIL Image
        result_image = Image.fromarray(output_np, mode='RGB')
        
        # 确保尺寸正确
        if result_image.size != (orig_width, orig_height):
            result_image = result_image.resize((orig_width, orig_height), Image.LANCZOS)
        
        print(f"   LaMa Inpaint 完成")
        
        return result_image
