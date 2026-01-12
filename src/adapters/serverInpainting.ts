/**
 * 服务器端 Inpaint (GPU 加速)
 * 使用后端 ONNX Runtime 进行 Inpaint 处理
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

/**
 * 使用服务器端 GPU 执行 Inpaint
 * 
 * @param imageFile 原始图片文件
 * @param maskDataUrl 遮罩 Data URL (白色=需要修复的区域)
 * @returns 修复后的图片 Data URL
 */
export async function serverInpaint(
    imageFile: File,
    maskDataUrl: string
): Promise<string> {
    try {
        console.log('🚀 调用服务器 GPU 进行 Inpaint...')

        // 将 mask dataURL 转换为 Blob
        const maskBlob = await dataURLToBlob(maskDataUrl)

        // 构建 FormData
        const formData = new FormData()
        formData.append('image', imageFile)
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

        console.log(`✓ Inpaint 完成 (${processTime}秒, 设备: ${device}, 尺寸: ${imageSize})`)

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
 * Data URL 转 Blob
 */
async function dataURLToBlob(dataURL: string): Promise<Blob> {
    const res = await fetch(dataURL)
    return await res.blob()
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
