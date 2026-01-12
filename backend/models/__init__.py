from .realesrgan_model import get_model as get_realesrgan_model
from .migan_onnx import MIGANONNXModel
from .device import DeviceDetector

__all__ = ['get_realesrgan_model', 'MIGANONNXModel', 'DeviceDetector', 'get_model', 'get_inpaint_model']


def get_model(device_type: str = None):
    """
    获取 Real-ESRGAN 超分辨率模型实例
    (兼容函数,调用 realesrgan_model 的 get_model)
    """
    return get_realesrgan_model(device_type)


def get_inpaint_model(device_type: str = None, model_path: str = None):
    """
    获取 MI-GAN Inpaint 模型实例(ONNX Runtime)
    
    Args:
        device_type: 设备类型 ('cuda' 或 'cpu')。如果为 None,自动检测
        model_path: ONNX 模型文件路径。如果为 None,使用默认路径
    
    Returns:
        MIGANONNXModel 实例
    """
    from pathlib import Path
    
    # 自动检测设备
    if device_type is None:
        device_info = DeviceDetector.get_device_info()
        # ONNX Runtime 只支持 CUDA 和 CPU,不支持 MPS
        device_type = 'cuda' if device_info['type'] == 'cuda' else 'cpu'
    
    # 默认模型路径
    if model_path is None:
        # 假设模型在项目根目录的 public/models/ 下
        current_dir = Path(__file__).parent.parent
        model_path = current_dir / ".." / "public" / "models" / "migan_pipeline_v2.onnx"
        model_path = str(model_path.resolve())
    
    return MIGANONNXModel(model_path=model_path, device=device_type)

