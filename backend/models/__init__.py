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
    
    当前使用 OpenCV Inpainting (简单快速,无需模型文件)
    
    Args:
        device_type: 设备类型(OpenCV 仅支持 CPU,此参数仅为接口兼容)
        model_path: 模型路径(OpenCV 不需要,此参数仅为接口兼容)
    
    Returns:
        OpenCVInpaint 实例
    """
    from .opencv_inpaint import OpenCVInpaint
    
    # OpenCV inpaint 不需要模型文件,直接返回实例
    return OpenCVInpaint(device='cpu')

