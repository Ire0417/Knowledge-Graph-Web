import api from './index'

export const graphApi = {
  // 获取所有可构建图谱的文件
  getGraphFiles: () => {
    return api.get('/graph/files')
  },
  // 构建知识图谱
  buildGraph: (fileId) => {
    return api.post('/graph/build', { fileId })
  },
  // 获取构建进度
  getBuildProgress: (fileId) => {
    return api.get(`/graph/build/progress/${fileId}`)
  },
  // 获取图谱数据
  getGraphData: (fileId) => {
    return api.get(`/graph/data/${fileId}`)
  },
  // 实体对齐
  alignEntities: (fileId) => {
    return api.post('/graph/align', { fileId })
  },
  // 关系合并
  mergeRelations: (fileId) => {
    return api.post('/graph/merge', { fileId })
  },
  // 图谱优化
  optimizeGraph: (fileId) => {
    return api.post('/graph/optimize', { fileId })
  },
  // 导出图谱数据
  exportGraph: (fileId, format) => {
    return api.get(`/graph/export/${fileId}?format=${format}`, {
      responseType: 'blob'
    })
  }
}