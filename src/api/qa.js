import api from './index'

export const qaApi = {
  // RAG健康检查
  checkHealth: (fileId) => {
    return api.get('/qa/health', {
      params: fileId ? { fileId } : {}
    })
  },
  // 智能问答
  askQuestion: (question, fileId) => {
    return api.post('/qa/ask', { question, fileId })
  },
  // 获取问答历史
  getQaHistory: (fileId) => {
    return api.get(`/qa/history/${fileId}`)
  },
  // 清除问答历史
  clearQaHistory: (fileId) => {
    return api.delete(`/qa/history/${fileId}`)
  },
  // 保存问答结果
  saveQaResult: (question, answer, fileId) => {
    return api.post('/qa/save', { question, answer, fileId })
  },
  // 相关问题推荐
  getRelatedQuestions: (question, fileId) => {
    return api.post('/qa/related', { question, fileId })
  }
}