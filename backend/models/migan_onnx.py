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
        
        # 模型需要固定 512x512 输入
        MODEL_SIZE = 512
        
        # 1. Resize 图片和遮罩到 512x512
        image_resized = image.resize((MODEL_SIZE, MODEL_SIZE), Image.LANCZOS)
        mask_resized = mask.resize((MODEL_SIZE, MODEL_SIZE), Image.LANCZOS)
        print(f"   原始尺寸: {orig_width}x{orig_height} -> 缩放到: {MODEL_SIZE}x{MODEL_SIZE}")
        
        # 2. 预处理图片
        img_array = self._preprocess_image(image_resized)
        
        # 3. 预处理遮罩
        mask_array = self._preprocess_mask(mask_resized, (MODEL_SIZE, MODEL_SIZE))
        
        # 4. 检查模型输入格式
        input_names = [inp.name for inp in self.session.get_inputs()]
        input_shapes = [inp.shape for inp in self.session.get_inputs()]
        print(f"📊 ONNX 模型输入信息: {len(input_names)} 个输入")
        for i, (name, shape) in enumerate(zip(input_names, input_shapes)):
            print(f"   输入 {i}: name='{name}', shape={shape}")
        
        # 5. ONNX 推理 - 根据模型输入数量处理
        if len(input_names) >= 2:
            # 双输入模型: 分别传入 image 和 mask
            print(f"   使用双输入模式: {input_names[0]}=image, {input_names[1]}=mask")
            outputs = self.session.run(
                None,
                {
                    input_names[0]: img_array,
                    input_names[1]: mask_array
                }
            )
        else:
            # 单输入模型: 将 image 和 mask 沿通道拼接
            # MI-GAN 原始模型期望 [1, 4, 512, 512] 输入 (RGB + mask)
            print(f"   使用单输入模式: 将 image 和 mask 沿通道拼接")
            
            # 将 image 转为 float [0, 1]
            img_float = img_array.astype(np.float32) / 255.0
            
            # mask_array 形状是 [1, 1, H, W]
            # 注意：mask 中白色(255)=需要修复的区域，转为 1.0
            # 不反转，直接归一化
            mask_channel = mask_array.astype(np.float32) / 255.0
            
            # 拼接
            combined = np.concatenate([img_float, mask_channel], axis=1)
            print(f"   拼接后形状: {combined.shape}")
            print(f"   image 范围: [{img_float.min():.2f}, {img_float.max():.2f}]")
            print(f"   mask 范围: [{mask_channel.min():.2f}, {mask_channel.max():.2f}]")
            
            outputs = self.session.run(
                None,
                {input_names[0]: combined}
            )
        
        # 6. 后处理
        output = outputs[0]
        print(f"   模型输出形状: {output.shape}, 范围: [{output.min():.3f}, {output.max():.3f}]")
        
        # 检查输出是否是 float [0,1] 格式
        if output.max() <= 1.0:
            print(f"   输出格式: float [0,1]，乘以 255")
            output = output * 255.0
        
        result_image = self._postprocess(output, MODEL_SIZE, MODEL_SIZE)
        
        # 7. Resize 回原始尺寸
        result_image = result_image.resize((orig_width, orig_height), Image.LANCZOS)
        print(f"   输出尺寸: {result_image.size}")
        
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
