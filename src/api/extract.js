import api from './index'

export const extractApi = {
  // 从文件中抽取知识
  extractFromFile: (fileId) => {
    return api.post('/extract/', { fileId })
  },
  // 获取抽取进度
  getExtractProgress: (fileId) => {
    return api.get(`/extract/progress/${fileId}`)
  },
  // 获取抽取结果
  getExtractResult: (fileId) => {
    return api.get(`/extract/result/${fileId}`)
  },
  // 实体识别
  recognizeEntities: (text) => {
    return api.post('/extract/entities', { text })
  },
  // 关系抽取
  extractRelations: (text) => {
    return api.post('/extract/relations', { text })
  },
  // 表格数据解析
  parseTable: (fileId, tableIndex) => {
    return api.post('/extract/table', { fileId, tableIndex })
  }
}