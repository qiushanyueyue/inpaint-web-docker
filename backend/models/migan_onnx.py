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
        input_types = [inp.type for inp in self.session.get_inputs()]
        
        print(f"📊 ONNX 模型输入信息: {len(input_names)} 个输入")
        for i, (name, shape, dtype) in enumerate(zip(input_names, input_shapes, input_types)):
            print(f"   输入 {i}: name='{name}', shape={shape}, type={dtype}")
        
        # 5. ONNX 推理 - 根据模型输入数量处理
        if len(input_names) >= 2:
            # 双输入模型: 分别传入 image 和 mask
            # NOTE: 根据模型期望的数据类型自动转换
            print(f"   使用双输入模式: {input_names[0]}=image, {input_names[1]}=mask")
            
            # 检查第一个输入的期望类型
            expected_type = input_types[0]
            print(f"   模型期望的数据类型: {expected_type}")
            
            # DEBUG: 显示原始 mask 信息
            print(f"   原始 mask 范围: [{mask_array.min()}, {mask_array.max()}]")
            mask_nonzero = np.count_nonzero(mask_array)
            mask_total = mask_array.size
            mask_ratio = mask_nonzero / mask_total * 100
            print(f"   mask 非零像素: {mask_nonzero}/{mask_total} ({mask_ratio:.1f}%)")
            
            # CRITICAL: 反转 mask
            # 前端: 白色(255)=用户标记的修复区域
            # 模型: 黑色(0)=需要修复的区域
            # 因此需要反转: 255 -> 0, 0 -> 255
            print(f"   🔧 反转 mask (白色->黑色)")
            mask_to_use = 255 - mask_array
            print(f"   反转后 mask 范围: [{mask_to_use.min()}, {mask_to_use.max()}]")
            
            # 根据期望类型转换数据
            if 'float' in expected_type.lower():
                # 模型期望 float32,归一化到 [0, 1]
                img_input = img_array.astype(np.float32) / 255.0
                mask_input = mask_to_use.astype(np.float32) / 255.0
                print(f"   → 转换为 float32: image 范围 [{img_input.min():.3f}, {img_input.max():.3f}]")
                print(f"   → 转换为 float32: mask 范围 [{mask_input.min():.3f}, {mask_input.max():.3f}]")
            else:
                # 模型期望 uint8,保持原样
                img_input = img_array
                mask_input = mask_to_use
                print(f"   → 保持 uint8: image 范围 [{img_input.min()}, {img_input.max()}]")
                print(f"   → 保持 uint8: mask 范围 [{mask_input.min()}, {mask_input.max()}]")
            
            print(f"   image 形状: {img_input.shape}, dtype: {img_input.dtype}")
            print(f"   mask 形状: {mask_input.shape}, dtype: {mask_input.dtype}")
            
            outputs = self.session.run(
                None,
                {
                    input_names[0]: img_input,
                    input_names[1]: mask_input
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
        print(f"   模型输出形状: {output.shape}, dtype: {output.dtype}")
        print(f"   模型输出范围: [{output.min():.3f}, {output.max():.3f}]")
        print(f"   模型输出均值: {output.mean():.3f}, 标准差: {output.std():.3f}")
        
        # DEBUG: 保存中间结果用于诊断
        import os
        debug_dir = "/tmp/inpaint_debug"
        os.makedirs(debug_dir, exist_ok=True)
        
        # 保存输入图像
        image.save(f"{debug_dir}/input_image.png")
        mask.save(f"{debug_dir}/input_mask.png")
        print(f"   💾 已保存输入: {debug_dir}/input_image.png, input_mask.png")
        
        # 检查输出范围并相应处理
        if output.max() <= 1.0 and output.min() >= 0.0:
            # 输出已经在 [0, 1] 范围内
            print(f"   → 输出在 [0, 1] 范围,直接缩放到 [0, 255]")
            output = output * 255.0
        elif output.max() <= 255.0 and output.min() >= 0.0:
            # 输出已经在 [0, 255] 范围内
            print(f"   → 输出在 [0, 255] 范围,保持不变")
            pass
        else:
            # 输出范围不标准,需要归一化
            print(f"   → 输出范围异常,进行归一化处理")
            output = np.clip(output, 0.0, 1.0) * 255.0
        
        print(f"   处理后范围: [{output.min():.1f}, {output.max():.1f}]")
        
        result_image = self._postprocess(output, MODEL_SIZE, MODEL_SIZE)
        
        # 7. Resize 回原始尺寸
        result_image = result_image.resize((orig_width, orig_height), Image.LANCZOS)
        print(f"   输出尺寸: {result_image.size}")
        
        # DEBUG: 保存输出图像
        result_image.save(f"{debug_dir}/output_image.png")
        print(f"   💾 已保存输出: {debug_dir}/output_image.png")
        
        # DEBUG: 计算差异
        input_array = np.array(image.resize((orig_width, orig_height), Image.LANCZOS))
        output_array = np.array(result_image)
        diff = np.abs(input_array.astype(float) - output_array.astype(float))
        diff_mean = diff.mean()
        diff_max = diff.max()
        print(f"   📊 输入输出差异: 均值={diff_mean:.2f}, 最大={diff_max:.2f}")
        
        if diff_mean < 1.0:
            print(f"   ⚠️  警告: 输入输出几乎相同,模型可能没有实际修复!")
        
        return result_image
    
    def _preprocess_image(self, image: Image.Image) -> np.ndarray:
        """
        预处理图片
        转换为 numpy 数组: [1, 3, H, W], uint8
        (在推理前会转换为 float32 并归一化)
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
        转换为 numpy 数组: [1, 1, H, W], uint8
        (在推理前会转换为 float32 并归一化)
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
            output: ONNX 输出 [1, 3, H, W], float [0, 255]
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
