"""
OpenCV Inpainting 实现
使用 OpenCV 内置的 inpainting 算法进行图像修复
"""
import cv2
import numpy as np
from PIL import Image
from typing import Tuple


class OpenCVInpaint:
    """OpenCV Inpainting 模型"""
    
    def __init__(self, device: str = "cpu"):
        """
        初始化 OpenCV Inpaint
        
        Args:
            device: 设备类型(OpenCV 仅支持 CPU,此参数仅为接口兼容)
        """
        self.actual_device = "cpu"
        print("✓ OpenCV Inpaint 初始化成功 (CPU)")
    
    def get_info(self) -> dict:
        """获取模型信息"""
        return {
            "name": "OpenCV Inpainting",
            "algorithm": "Telea",
            "device": "cpu"
        }
    
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
        # 转换为 numpy 数组
        img_array = np.array(image)
        mask_array = np.array(mask.convert('L'))
        
        # 确保是 RGB 格式
        if len(img_array.shape) == 2:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
        elif img_array.shape[2] == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        
        # OpenCV 使用 BGR 格式
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        print(f"   OpenCV Inpaint 处理: {img_bgr.shape}")
        print(f"   mask 非零像素: {np.count_nonzero(mask_array)}/{mask_array.size}")
        
        # 使用 Telea 算法进行修复
        # inpaintRadius: 修复半径,越大修复范围越广但速度越慢
        result_bgr = cv2.inpaint(
            img_bgr,
            mask_array,
            inpaintRadius=5,  # 修复半径
            flags=cv2.INPAINT_TELEA  # 使用 Telea 算法
        )
        
        # 转回 RGB
        result_rgb = cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB)
        
        # 转换为 PIL Image
        result_image = Image.fromarray(result_rgb)
        
        print(f"   OpenCV Inpaint 完成")
        
        return result_image
