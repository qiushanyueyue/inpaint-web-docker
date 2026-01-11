/**
 * 超分辨率服务器端适配器
 * 调用后端 GPU API 进行图像放大
 */

// 配置：API 基础 URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * 检查后端服务是否可用
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`)
    const data = await response.json()
    return data.status === 'healthy' && data.model_loaded
  } catch (error) {
    console.error('后端服务健康检查失败:', error)
    return false
  }
}

/**
 * 获取后端信息
 */
export async function getBackendInfo(): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/info`)
  return response.json()
}

/**
 * 服务器端超分辨率（GPU 加速）
 */
export async function serverSuperResolution(
  imageFile: File | HTMLImageElement,
  callback: (progress: number) => void
): Promise<string> {
  // 并不是所有 File 都能被 PIL 直接识别，为了稳妥起见，
  // 我们统一将所有图片（无论是 File 还是 HTMLImageElement）
  // 都先绘制到 Canvas 上再转为标准 PNG File
  let file: File

  if (imageFile instanceof HTMLImageElement) {
    file = await htmlImageToFile(imageFile)
  } else {
    // 如果是 File，先转为 Image 元素加载，再转回 PNG File
    // 这样可以确保格式统一为 PNG，解决兼容性问题
    const img = await fileToImage(imageFile)
    file = await htmlImageToFile(img)
  }

  // 创建 FormData
  const formData = new FormData()
  formData.append('file', file)

  // 模拟进度（因为后端不支持实时进度）
  let progress = 0
  const progressInterval = setInterval(() => {
    if (progress < 90) {
      progress += 10
      callback(progress)
    }
  }, 500)

  try {
    console.log('🚀 调用服务器 GPU 进行超分辨率处理...')

    const response = await fetch(`${API_BASE_URL}/api/upscale`, {
      method: 'POST',
      body: formData,
    })

    clearInterval(progressInterval)

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '服务器处理失败')
    }

    // 获取处理信息
    const processTime = response.headers.get('X-Process-Time')
    const device = response.headers.get('X-Device')

    console.log(`✓ 处理完成 (${processTime}秒, 设备: ${device})`)

    // 设置进度为 100%
    callback(100)

    // 将响应转换为 Blob 然后创建 URL
    const blob = await response.blob()
    return URL.createObjectURL(blob)
  } catch (error) {
    clearInterval(progressInterval)
    console.error('服务器超分辨率失败:', error)
    throw error
  }
}

/**
 * 将 HTMLImageElement 转换为 File
 */
async function htmlImageToFile(image: HTMLImageElement): Promise<File> {
  return new Promise((resolve, reject) => {
    const canvas = document.createElement('canvas')
    canvas.width = image.naturalWidth || image.width
    canvas.height = image.naturalHeight || image.height

    const ctx = canvas.getContext('2d')
    if (!ctx) {
      reject(new Error('无法创建 canvas context'))
      return
    }

    ctx.drawImage(image, 0, 0)

    canvas.toBlob(blob => {
      if (!blob) {
        reject(new Error('无法转换图片为 blob'))
        return
      }

      const file = new File([blob], 'image.png', { type: 'image/png' })
      resolve(file)
    }, 'image/png')
  })
}

/**
 * 将 File 转换为 HTMLImageElement
 */
function fileToImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('无法加载图片文件'))
    img.src = URL.createObjectURL(file)
  })
}
