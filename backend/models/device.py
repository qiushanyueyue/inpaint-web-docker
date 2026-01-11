import torch

class DeviceDetector:
    @staticmethod
    def get_device_info():
        """
        检测可用的计算设备 (CUDA, MPS, CPU)
        """
        device_type = "cpu"
        device_name = "CPU"
        
        if torch.cuda.is_available():
            device_type = "cuda"
            device_name = torch.cuda.get_device_name(0)
        elif torch.backends.mps.is_available():
            device_type = "mps"
            device_name = "Apple Silicon (MPS)"
            
        return {
            "type": device_type,
            "name": device_name,
            "torch_version": torch.__version__
        }
