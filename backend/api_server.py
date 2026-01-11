"""
Inpaint-Web 后端 API 服务
提供图像超分辨率（4x 放大）功能
支持 NVIDIA GPU (CUDA)、Mac M 芯片 (MPS) 和 CPU
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
import time
from pathlib import Path
import uvicorn

from models import get_model, DeviceDetector

# 创建 FastAPI 应用
app = FastAPI(
    title="Inpaint-Web GPU Backend",
    description="图像超分辨率 API 服务（GPU 加速）",
    version="1.0.0"
)

# 配置 CORS（允许前端跨域调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
model = None
device_info = None


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    global model, device_info
    
    print("=" * 60)
    print("🚀 Inpaint-Web GPU Backend 启动中...")
    print("=" * 60)
    
    # 检测设备
    device_info = DeviceDetector.get_device_info()
    print(f"\n📊 设备信息:")
    for key, value in device_info.items():
        print(f"   {key}: {value}")
    
    # 加载模型
    print(f"\n📦 加载 Real-ESRGAN 模型...")
    try:
        model = get_model()
        print(f"✓ 模型加载成功！")
    except FileNotFoundError as e:
        print(f"\n⚠️  错误: {e}")
        print(f"\n请先运行: python backend/download_models.py")
        raise
    except Exception as e:
        print(f"\n❌ 模型加载失败: {e}")
        raise
    
    print("\n" + "=" * 60)
    print("✓ 服务启动完成，API 文档: http://localhost:8000/docs")
    print("=" * 60 + "\n")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Inpaint-Web GPU Backend",
        "version": "1.0.0",
        "status": "running",
        "device": device_info,
        "endpoints": {
            "upscale": "/api/upscale",
            "info": "/api/info",
            "health": "/api/health"
        }
    }


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "device": device_info
    }


@app.get("/api/info")
async def get_info():
    """获取模型和设备信息"""
    if model is None:
        raise HTTPException(status_code=503, detail="模型未加载")
    
    return {
        "device": device_info,
        "model": model.get_info()
    }


@app.post("/api/upscale")
async def upscale_image(
    file: UploadFile = File(..., description="要放大的图片文件"),
    scale: int = 4
):
    """
    图像超分辨率（4x 放大）
    
    Args:
        file: 上传的图片文件（支持 PNG, JPG, WEBP 等格式）
        scale: 放大倍数（默认 4，当前仅支持 4）
    
    Returns:
        放大后的图片（PNG 格式）
    """
    if model is None:
        raise HTTPException(status_code=503, detail="模型未加载")
    
    # 验证文件类型
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="文件类型必须是图片")
    
    try:
        # 读取图片
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # 转换为 RGB（如果是 RGBA 或其他格式）
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        original_size = image.size
        print(f"📥 收到图片: {original_size[0]}x{original_size[1]}")
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行超分辨率
        print(f"🔄 开始处理...")
        output_image = model.enhance(image, outscale=scale)
        
        # 计算处理时间
        process_time = time.time() - start_time
        output_size = output_image.size
        
        print(f"✓ 处理完成: {output_size[0]}x{output_size[1]} (耗时 {process_time:.2f}秒)")
        
        # 转换为字节流
        output_buffer = io.BytesIO()
        output_image.save(output_buffer, format='PNG', optimize=True)
        output_buffer.seek(0)
        
        # 返回图片
        return Response(
            content=output_buffer.getvalue(),
            media_type="image/png",
            headers={
                "X-Process-Time": f"{process_time:.2f}",
                "X-Original-Size": f"{original_size[0]}x{original_size[1]}",
                "X-Output-Size": f"{output_size[0]}x{output_size[1]}",
                "X-Device": device_info['type']
            }
        )
    
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@app.post("/api/upscale-info")
async def upscale_with_info(file: UploadFile = File(...)):
    """
    图像超分辨率（带详细信息）
    返回 JSON 格式，包含 base64 编码的图片和处理信息
    """
    if model is None:
        raise HTTPException(status_code=503, detail="模型未加载")
    
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        original_size = image.size
        start_time = time.time()
        
        output_image = model.enhance(image, outscale=4)
        process_time = time.time() - start_time
        
        # 转换为 base64
        output_buffer = io.BytesIO()
        output_image.save(output_buffer, format='PNG')
        
        import base64
        img_base64 = base64.b64encode(output_buffer.getvalue()).decode()
        
        return JSONResponse({
            "success": True,
            "image": f"data:image/png;base64,{img_base64}",
            "info": {
                "original_size": original_size,
                "output_size": output_image.size,
                "process_time": round(process_time, 2),
                "device": device_info['type']
            }
        })
    
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


if __name__ == "__main__":
    # 直接运行服务
    # 默认端口改为 8888（避免与其他服务冲突）
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8888,  # 改为 8888，可通过环境变量覆盖
        reload=False,  # 生产环境设为 False
        log_level="info"
    )
