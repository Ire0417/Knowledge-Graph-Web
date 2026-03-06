import api from './index'

export const visualApi = {
  // 获取图谱布局数据
  getGraphLayout: (fileId, layoutType) => {
    return api.get(`/visual/layout/${fileId}?type=${layoutType}`)
  },
  // 节点展开/折叠
  toggleNode: (fileId, nodeId) => {
    return api.post('/visual/toggle-node', { fileId, nodeId })
  },
  // 路径查询
  queryPath: (fileId, sourceNodeId, targetNodeId) => {
    return api.post('/visual/query-path', { fileId, sourceNodeId, targetNodeId })
  },
  // 邻居查询
  queryNeighbors: (fileId, nodeId, depth) => {
    return api.get(`/visual/neighbors/${fileId}/${nodeId}?depth=${depth}`)
  },
  // 子图查询
  querySubgraph: (fileId, nodeIds) => {
    return api.post('/visual/subgraph', { fileId, nodeIds })
  },
  // 图谱统计信息
  getGraphStats: (fileId) => {
    return api.get(`/visual/stats/${fileId}`)
  }
}