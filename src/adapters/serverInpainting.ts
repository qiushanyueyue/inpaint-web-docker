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
      console.log('  处理 HTMLImageElement...')
      console.log(`    src 类型: ${imageFile.src.substring(0, 50)}...`)

      // 检查 src 是否是 data URL，如果是，直接转换为 Blob（更可靠）
      if (imageFile.src.startsWith('data:')) {
        console.log('    src 是 data URL，直接转换为 Blob...')
        try {
          imageBlob = await dataURLToBlob(imageFile.src)
          console.log(`    data URL 转换成功: ${imageBlob.size} bytes`)
        } catch (e) {
          console.warn('    data URL 转换失败，尝试 canvas 方式...')
          imageBlob = await imageToBlob(imageFile)
        }
      } else if (imageFile.src.startsWith('blob:')) {
        // blob URL，需要先 fetch 获取数据
        console.log('    src 是 blob URL，尝试 fetch...')
        try {
          const response = await fetch(imageFile.src)
          imageBlob = await response.blob()
          console.log(`    blob URL fetch 成功: ${imageBlob.size} bytes`)
        } catch (e) {
          console.warn('    blob URL fetch 失败，尝试 canvas 方式...')
          imageBlob = await imageToBlob(imageFile)
        }
      } else {
        // 其他 URL（http/https），使用 canvas 方式
        console.log('    使用 canvas 转换...')
        imageBlob = await imageToBlob(imageFile)
      }
    } else {
      // File 对象直接使用
      imageBlob = imageFile
      console.log(`  File 对象: ${imageBlob.size} bytes`)
    }

    // 验证 imageBlob 是否有效
    if (!imageBlob || imageBlob.size === 0) {
      throw new Error('图片数据无效（大小为 0）')
    }
    console.log(
      `  最终图片 Blob: ${imageBlob.size} bytes, type: ${imageBlob.type}`
    )

    // 如果图片不是 PNG 格式，需要转换为 PNG 以确保后端兼容性
    // 某些 JPEG 文件可能有特殊编码导致 PIL 无法识别
    let finalImageBlob: Blob = imageBlob
    if (imageBlob.type !== 'image/png') {
      console.log('  图片非 PNG 格式，进行格式转换...')
      try {
        finalImageBlob = await convertToPng(imageBlob)
        console.log(
          `  转换后 Blob: ${finalImageBlob.size} bytes, type: ${finalImageBlob.type}`
        )
      } catch (e) {
        console.warn('  PNG 转换失败，使用原始数据:', e)
        finalImageBlob = imageBlob
      }
    }

    // 将 mask dataURL 转换为 Blob
    const maskBlob = await dataURLToBlob(maskDataUrl)

    // 构建 FormData
    // 根据实际类型设置正确的文件扩展名
    const imageExt = finalImageBlob.type === 'image/png' ? 'png' : 'jpg'
    const formData = new FormData()
    formData.append('image', finalImageBlob, `image.${imageExt}`)
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
 * 将 Blob 转换为 PNG 格式
 * 通过 Image + Canvas 重新编码图片，确保格式兼容性
 */
async function convertToPng(blob: Blob): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const url = URL.createObjectURL(blob)

    img.onload = () => {
      URL.revokeObjectURL(url)

      const canvas = document.createElement('canvas')
      canvas.width = img.naturalWidth || img.width
      canvas.height = img.naturalHeight || img.height

      const ctx = canvas.getContext('2d')
      if (!ctx) {
        reject(new Error('无法获取 Canvas 上下文'))
        return
      }

      ctx.drawImage(img, 0, 0)

      canvas.toBlob(pngBlob => {
        if (pngBlob && pngBlob.size > 0) {
          resolve(pngBlob)
        } else {
          reject(new Error('PNG 转换失败'))
        }
      }, 'image/png')
    }

    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('无法加载图片进行格式转换'))
    }

    img.src = url
  })
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
