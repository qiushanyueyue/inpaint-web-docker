"""
MI-GAN ONNX Runtime Inpaint 模型
使用 ONNX Runtime 在后端运行,支持 GPU (CUDA) 和 CPU
"""
import onnxruntime as ort
import numpy as np
from PIL import Image
from typing import Tuple


class MIGANONNXModel:
    """MI-GAN Inpaint 模型(ONNX Runtime 实现)"""
    
    def __init__(self, model_path: str, device: str = "cuda"):
        """
        初始化 ONNX 模型
        
        Args:
            model_path: ONNX 模型文件路径
            device: 'cuda' 或 'cpu'
        """
        # 配置 execution providers
        providers = []
        if device == "cuda":
            available_providers = ort.get_available_providers()
            if "CUDAExecutionProvider" in available_providers:
                providers.append("CUDAExecutionProvider")
                print("✓ 使用 CUDA 加速")
            else:
                print("⚠️  CUDA 不可用,降级到 CPU")
        
        providers.append("CPUExecutionProvider")
        
        # 加载模型
        self.session = ort.InferenceSession(model_path, providers=providers)
        self.actual_device = "cuda" if "CUDAExecutionProvider" in self.session.get_providers() else "cpu"
        
        print(f"✓ MI-GAN ONNX 模型加载成功 (设备: {self.actual_device})")
        
    def get_info(self) -> dict:
        """获取模型信息"""
        return {
            "name": "MI-GAN (ONNX)",
            "device": self.actual_device,
            "providers": self.session.get_providers()
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
            mask: 遮罩图片(PIL Image, L/灰度,白色=需要修复的区域)
            
        Returns:
            修复后的图片(PIL Image)
        """
        # 获取原始尺寸
        orig_width, orig_height = image.size
        
        # 1. 预处理图片
        img_array = self._preprocess_image(image)
        
        # 2. 预处理遮罩
        mask_array = self._preprocess_mask(mask, image.size)
        
        # 3. ONNX 推理
        input_names = [inp.name for inp in self.session.get_inputs()]
        outputs = self.session.run(
            None,
            {
                input_names[0]: img_array,
                input_names[1]: mask_array
            }
        )
        
        # 4. 后处理
        result_image = self._postprocess(outputs[0], orig_width, orig_height)
        
        return result_image
    
    def _preprocess_image(self, image: Image.Image) -> np.ndarray:
        """
        预处理图片
        转换为 ONNX 模型需要的格式: [1, 3, H, W], uint8
        """
        # 确保是 RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 转换为 numpy 数组: [H, W, 3]
        img_np = np.array(image, dtype=np.uint8)
        
        # 转置为 [3, H, W]
        img_np = img_np.transpose(2, 0, 1)
        
        # 添加 batch 维度: [1, 3, H, W]
        img_np = np.expand_dims(img_np, axis=0)
        
        return img_np
    
    def _preprocess_mask(
        self, 
        mask: Image.Image, 
        target_size: Tuple[int, int]
    ) -> np.ndarray:
        """
        预处理遮罩
        转换为 ONNX 模型需要的格式: [1, 1, H, W], uint8
        """
        # 调整大小到与图片相同
        if mask.size != target_size:
            mask = mask.resize(target_size, Image.LANCZOS)
        
        # 确保是灰度图
        if mask.mode != 'L':
            mask = mask.convert('L')
        
        # 转换为 numpy 数组: [H, W]
        mask_np = np.array(mask, dtype=np.uint8)
        
        # 添加 channel 和 batch 维度: [1, 1, H, W]
        mask_np = np.expand_dims(mask_np, axis=0)
        mask_np = np.expand_dims(mask_np, axis=0)
        
        return mask_np
    
    def _postprocess(
        self, 
        output: np.ndarray, 
        width: int, 
        height: int
    ) -> Image.Image:
        """
        后处理输出
        将 ONNX 输出转换为 PIL Image
        
        Args:
            output: ONNX 输出 [1, 3, H, W], uint8
            width: 目标宽度
            height: 目标高度
        """
        # 移除 batch 维度: [3, H, W]
        img_np = output.squeeze(0)
        
        # 转置回 [H, W, 3]
        img_np = img_np.transpose(1, 2, 0)
        
        # 确保是 uint8
        img_np = np.clip(img_np, 0, 255).astype(np.uint8)
        
        # 转换为 PIL Image
        result = Image.fromarray(img_np, mode='RGB')
        
        # 确保尺寸正确
        if result.size != (width, height):
            result = result.resize((width, height), Image.LANCZOS)
        
        return result
