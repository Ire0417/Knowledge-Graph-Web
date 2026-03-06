import api from './index'

export const uploadApi = {
  // 上传文件
  uploadFile: (formData, onUploadProgress) => {
    return api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onUploadProgress(percentCompleted)
        }
      }
    })
  },
  // 解析文件 - 修正路径，添加/upload前缀
  parseFile: (fileId) => {
    return api.post('/upload/parse', { fileId })
  },
  // 获取解析进度 - 修正路径，添加/upload前缀
  getParseProgress: (fileId) => {
    return api.get(`/upload/parse/progress/${fileId}`)
  },
  // 获取文件列表 - 修正路径，添加/upload前缀
  getFileList: () => {
    return api.get('/upload/files')
  },
  // 删除文件 - 修正路径，添加/upload前缀
  deleteFile: (fileId) => {
    return api.delete(`/upload/files/${fileId}`)
  }
}