/**
 * 服务器端 Inpaint (GPU 加速)
 * 使用后端 ONNX Runtime 进行 Inpaint 处理
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

/**
 * HTMLImageElement 转 Blob
 * 将图片元素绘制到 canvas 并转换为 Blob
 * 增强版本：支持跨域图片和错误处理
 */
async function imageToBlob(img: HTMLImageElement): Promise<Blob> {
  return new Promise((resolve, reject) => {
    try {
      const canvas = document.createElement('canvas')
      const width = img.naturalWidth || img.width
      const height = img.naturalHeight || img.height

      // 验证图片尺寸
      if (width === 0 || height === 0) {
        reject(new Error('图片尺寸无效（宽度或高度为0）'))
        return
      }

      canvas.width = width
      canvas.height = height

      const ctx = canvas.getContext('2d')
      if (!ctx) {
        reject(new Error('无法获取 Canvas 上下文'))
        return
      }

      // 绘制图片到 canvas
      ctx.drawImage(img, 0, 0, width, height)

      // 验证 canvas 是否有有效数据
      try {
        // 尝试读取像素数据，检测跨域问题
        ctx.getImageData(0, 0, 1, 1)
      } catch (e) {
        console.warn('⚠️ Canvas 可能受跨域限制，尝试继续处理...')
      }

      // 尝试转换为 PNG，如果失败则尝试 JPEG
      canvas.toBlob(blob => {
        if (blob && blob.size > 0) {
          console.log(
            `   Canvas 转 Blob 成功: ${blob.size} bytes, type: ${blob.type}`
          )
          resolve(blob)
        } else {
          // PNG 失败，尝试 JPEG
          console.warn('   PNG 转换失败，尝试 JPEG...')
          canvas.toBlob(
            jpegBlob => {
              if (jpegBlob && jpegBlob.size > 0) {
                console.log(`   JPEG 转换成功: ${jpegBlob.size} bytes`)
                resolve(jpegBlob)
              } else {
                reject(new Error('Canvas 转 Blob 失败：输出为空'))
              }
            },
            'image/jpeg',
            0.95
          )
        }
      }, 'image/png')
    } catch (error) {
      reject(new Error(`图片转换失败: ${error}`))
    }
  })
}

/**
 * 使用服务器端 GPU 执行 Inpaint
 *
 * @param imageFile 原始图片 (File 或 HTMLImageElement)
 * @param maskDataUrl 遮罩 Data URL (白色=需要修复的区域)
 * @returns 修复后的图片 Data URL
 */
export async function serverInpaint(
  imageFile: File | HTMLImageElement,
  maskDataUrl: string
): Promise<string> {
  try {
    console.log('🚀 调用服务器 GPU 进行 Inpaint...')

    // 处理不同类型的输入
    let imageBlob: Blob
    if (imageFile instanceof HTMLImageElement) {
      console.log('  转换 HTMLImageElement 为 Blob...')
      imageBlob = await imageToBlob(imageFile)
    } else {
      imageBlob = imageFile
    }

    // 将 mask dataURL 转换为 Blob
    const maskBlob = await dataURLToBlob(maskDataUrl)

    // 构建 FormData
    const formData = new FormData()
    formData.append('image', imageBlob, 'image.png')
    formData.append('mask', maskBlob, 'mask.png')

    // 调用后端 API
    const response = await fetch(`${API_BASE_URL}/api/inpaint`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`HTTP ${response.status}: ${errorText}`)
    }

    // 获取性能信息
    const processTime = response.headers.get('X-Process-Time')
    const device = response.headers.get('X-Device')
    const imageSize = response.headers.get('X-Image-Size')

    console.log(
      `✓ Inpaint 完成 (${processTime}秒, 设备: ${device}, 尺寸: ${imageSize})`
    )

    // 转换为 dataURL
    const blob = await response.blob()
    const dataUrl = await blobToDataURL(blob)

    return dataUrl
  } catch (error) {
    console.error('❌ 服务器 Inpaint 失败:', error)
    throw error
  }
}

/**
 * Data URL 转 Blob (改进版本)
 * 使用 base64 解码而不是 fetch，更可靠
 */
async function dataURLToBlob(dataURL: string): Promise<Blob> {
  // 分离 data URL 的 header 和 base64 数据
  const parts = dataURL.split(',')
  if (parts.length < 2) {
    throw new Error('Invalid data URL format')
  }

  const mimeMatch = parts[0].match(/:(.*?);/)
  const mime = mimeMatch ? mimeMatch[1] : 'image/png'
  const base64Data = parts[1]

  // 解码 base64
  const binaryString = atob(base64Data)
  const bytes = new Uint8Array(binaryString.length)

  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i)
  }

  return new Blob([bytes], { type: mime })
}

/**
 * Blob 转 Data URL
 */
async function blobToDataURL(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}
