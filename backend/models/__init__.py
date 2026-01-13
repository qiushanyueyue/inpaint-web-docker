from .realesrgan_model import get_model as get_realesrgan_model
from .migan_onnx import MIGANONNXModel
from .device import DeviceDetector

__all__ = ['get_realesrgan_model', 'MIGANONNXModel', 'DeviceDetector', 'get_model', 'get_inpaint_model']


def get_model(device_type: str = None):
    """
    获取 Real-ESRGAN 超分辨率模型实例
    (兼容函数,调用 realesrgan_model 的 get_model)
    
    注意: 原始 get_model() 不接受参数,会自动检测设备
    """
    return get_realesrgan_model()  # 不传递参数


def get_inpaint_model(device_type: str = None, model_path: str = None):
    """
    获取 Inpaint 模型实例
    
    当前使用 LaMa (Resolution-robust Large Mask Inpainting)
    支持 GPU (CUDA) 和 CPU
    
    Args:
        device_type: 设备类型 ('cuda' 或 'cpu')。如果为 None,自动检测
        model_path: 模型路径。如果为 None,使用默认路径
    
    Returns:
        LamaInpaint 实例
    """
    from .lama_inpaint import LamaInpaint
    from pathlib import Path
    
    # 自动检测设备
    if device_type is None:
        device_info = DeviceDetector.get_device_info()
        # LaMa 使用 PyTorch,支持 CUDA 和 CPU
        device_type = 'cuda' if device_info['type'] == 'cuda' else 'cpu'
    
    # 默认模型路径
    if model_path is None:
        current_dir = Path(__file__).parent.parent
        model_path = current_dir / "weights" / "big-lama.pt"
        model_path = str(model_path.resolve())
    
    return LamaInpaint(model_path=model_path, device=device_type)

