// 格式化时间
export const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 格式化文件大小
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 格式化图谱数据
export const formatGraphData = (data) => {
  if (!data || !data.nodes || !data.links) {
    return { nodes: [], links: [] }
  }
  
  // 确保节点和边的数据格式正确
  const nodes = data.nodes.map(node => ({
    id: node.id || node.node_id,
    name: node.name || node.label,
    type: node.type || node.category,
    value: node.value || 1,
    ...node
  }))
  
  const links = data.links.map(link => ({
    source: link.source,
    target: link.target,
    relationship: link.relationship || link.type,
    ...link
  }))
  
  return { nodes, links }
}

// 格式化实体类型
export const formatEntityType = (type) => {
  const typeMap = {
    'PERSON': '人物',
    'ORG': '组织',
    'LOCATION': '地点',
    'TIME': '时间',
    'EVENT': '事件',
    'CONCEPT': '概念',
    'OBJECT': '物体'
  }
  return typeMap[type] || type
}

// 格式化关系类型
export const formatRelationType = (type) => {
  const typeMap = {
    'HAS_PART': '包含',
    'PART_OF': '属于',
    'IS_A': '是',
    'RELATED_TO': '相关',
    'LOCATED_IN': '位于',
    'OCCURRED_AT': '发生于',
    'CREATED_BY': '由...创建',
    'USED_BY': '被...使用'
  }
  return typeMap[type] || type
}