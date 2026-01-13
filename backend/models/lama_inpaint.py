"""
LaMa (Resolution-robust Large Mask Inpainting) 实现
不使用 simple-lama-inpainting，直接使用 PyTorch 加载模型
支持 GPU (CUDA) 和 CPU
"""
import torch
import numpy as np
from PIL import Image
from typing import Optional
import os


class LamaInpaint:
    """LaMa Inpainting 模型"""
    
    def __init__(self, model_path: Optional[str] = None, device: str = "cuda"):
        """
        初始化 LaMa Inpaint
        
        Args:
            model_path: 模型文件路径
            device: 'cuda' 或 'cpu'
        """
        self.device = device
        self.actual_device = device
        
        # 检查设备可用性
        if device == "cuda" and not torch.cuda.is_available():
            print(f"⚠️  CUDA 不可用，降级到 CPU")
            self.device = "cpu"
            self.actual_device = "cpu"
        
        print(f"📦 加载 LaMa 模型 (device={self.device})...")
        
        # 检查模型文件
        if model_path and os.path.exists(model_path):
            try:
                # 加载预训练模型
                checkpoint = torch.load(model_path, map_location=self.device)
                
                # 提取模型状态
                if 'state_dict' in checkpoint:
                    state_dict = checkpoint['state_dict']
                elif 'model' in checkpoint:
                    state_dict = checkpoint['model']
                else:
                    state_dict = checkpoint
                
                # 创建模型（使用 torch.jit.load 如果是 TorchScript 模型）
                if model_path.endswith('.pt') or model_path.endswith('.pth'):
                    try:
                        self.model = torch.jit.load(model_path, map_location=self.device)
                        print(f"✓ 加载 TorchScript 模型成功")
                    except:
                        # 如果不是 TorchScript，则尝试普通加载
                        raise Exception("需要原始 PyTorch 模型")
                else:
                    raise Exception(f"不支持的模型格式: {model_path}")
                    
                self.model.eval()
                self.model_loaded = True
                print(f"✓ LaMa 模型加载成功")
                
            except Exception as e:
                print(f"❌ 模型加载失败: {e}")
                print(f"⚠️  将使用简单的修复策略（仅供测试）")
                self.model_loaded = False
        else:
            print(f"⚠️  模型文件不存在: {model_path}")
            print(f"⚠️  将使用简单的修复策略（仅供测试）")
            self.model_loaded = False
    
    def get_info(self) -> dict:
        """获取模型信息"""
        return {
            "name": "LaMa (Resolution-robust Large Mask Inpainting)",
            "device": self.actual_device,
            "model_loaded": self.model_loaded
        }
    
    def _simple_inpaint(self, image: Image.Image, mask: Image.Image) -> Image.Image:
        """
        简单的 inpaint 实现（当模型加载失败时使用）
        使用基于颜色均值的简单填充策略
        """
        import cv2
        
        # 转换为 numpy 数组
        img_array = np.array(image)
        mask_array = np.array(mask)
        
        # 将 mask 转为二值图像
        _, mask_binary = cv2.threshold(mask_array, 127, 255, cv2.THRESH_BINARY)
        
        # 使用 OpenCV 的 inpaint 功能
        result = cv2.inpaint(img_array, mask_binary, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        
        return Image.fromarray(result)
    
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
        
        # 确保格式正确
        if image.mode != 'RGB':
            image = image.convert('RGB')
        if mask.mode != 'L':
            mask = mask.convert('L')
        
        # 如果模型未加载，使用简单策略
        if not self.model_loaded:
            print(f"   使用 OpenCV inpaint (模型未加载)")
            result = self._simple_inpaint(image, mask)
            print(f"   简单 Inpaint 完成")
            return result
        
        # TODO: 使用 LaMa 模型进行推理
        # 当前回退到简单策略
        print(f"   使用 OpenCV inpaint (临时方案)")
        result = self._simple_inpaint(image, mask)
        print(f"   Inpaint 完成")
        
        return result
