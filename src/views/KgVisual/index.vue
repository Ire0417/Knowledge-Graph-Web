<template>
  <div class="kg-visual-container">
    <div class="page-header">
      <h1 class="page-title">知识图谱可视化</h1>
      <p class="page-description">交互式图谱展示，支持多种布局方式和路径查询</p>
    </div>
    
    <div class="card">
      <div class="card-header">
        <div class="control-group">
          <label class="control-label">选择文件</label>
          <el-select v-model="selectedFileId" placeholder="请选择已解析的文件" class="form-control" @change="loadGraphData">
            <el-option
              v-for="file in availableFiles"
              :key="file.id"
              :label="file.name"
              :value="file.id"
            />
          </el-select>
        </div>
        <div class="control-group">
          <label class="control-label">布局方式</label>
          <el-select v-model="layoutType" @change="safeUpdateChart" class="form-control">
            <el-option label="力导向图" value="force" />
            <el-option label="环形布局" value="circle" />
          </el-select>
        </div>
        <div class="control-group">
          <label class="control-label">搜索实体</label>
          <el-input
            v-model="searchKeyword"
            placeholder="输入实体名称"
            @keyup.enter="searchEntity"
            class="form-control"
          />
        </div>
        <el-button type="primary" @click="resetView">重置视图</el-button>
      </div>
      <div class="card-body">
        <div class="graph-container">
          <div ref="graphRef" class="graph-canvas"></div>
        </div>
      </div>
    </div>
    
    <div v-if="kgStore.selectedNode" class="card">
      <div class="card-header">
        <h3 class="card-title">实体详情</h3>
      </div>
      <div class="card-body">
        <div class="entity-details">
          <div class="detail-item">
            <span class="detail-label">实体名称:</span>
            <span class="detail-value">{{ kgStore.selectedNode.name }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">实体类型:</span>
            <span class="detail-value">{{ formatEntityType(kgStore.selectedNode.type) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useKgStore } from '../../store/kgStore'
import { useFileStore } from '../../store/fileStore'
import { graphApi } from '../../api/graph'
import { formatEntityType } from '../../utils/format'
import * as echarts from 'echarts'

const kgStore = useKgStore()
const fileStore = useFileStore()
const graphRef = ref(null)
let chart = null
const layoutType = ref('force')
const searchKeyword = ref('')
const selectedFileId = ref('')
const availableFiles = ref([])

const loadAvailableFiles = async () => {
  try {
    const response = await graphApi.getGraphFiles()
    if (response.data && response.data.success) {
      availableFiles.value = response.data.files || []
    }
    if (fileStore.uploadedFiles.length > 0 && availableFiles.value.length === 0) {
      availableFiles.value = fileStore.uploadedFiles.map(file => ({
        id: file.id,
        name: file.name,
        status: file.status || '解析完成',
        hasGraph: file.status === '已构建'
      })).filter(file => ['已构建', '已提取', '解析完成'].includes(file.status))
    }
  } catch (error) {
    console.error('Load files error:', error)
  }
}

const loadGraphData = async () => {
  if (!selectedFileId.value) return
  
  try {
    const response = await graphApi.getGraphData(selectedFileId.value)
    if (response.data && response.data.success && response.data.data) {
      const data = response.data.data
      const schema = data.schema || {}
      
      const nodes = data.entities.map(ent => ({
        id: ent.id,
        name: ent.label,
        type: ent.type,
        itemStyle: {
          color: ent.color || '#409eff'
        }
      }))
      const links = data.relationships.map(rel => ({
        source: rel.source,
        target: rel.target,
        label: rel.label,
        lineStyle: {
          color: '#b388ff'
        },
        relationName: rel.label
      }))
      
      kgStore.setGraphData({ nodes, links })
      
      nextTick(() => {
        nextTick(() => {
          initOrUpdateChart()
        })
      })
    } else {
      ElMessage.error({ message: response.data?.message || '加载图谱数据失败', duration: 3000 })
    }
  } catch (error) {
    console.error('Load graph error:', error)
    ElMessage.error({ message: '加载图谱数据失败', duration: 3000 })
  }
}

const initOrUpdateChart = () => {
  if (!graphRef.value) {
    setTimeout(() => {
      initOrUpdateChart()
    }, 100)
    return
  }

  try {
    if (!chart) {
      chart = echarts.init(graphRef.value)
      window.addEventListener('resize', handleResize)
      chart.on('click', function(params) {
        if (params.dataType === 'node') {
          kgStore.selectNode(params.data)
        }
      })
    }
    updateChartContent()
  } catch (e) {
    console.error('Chart initialization error:', e)
  }
}

const updateChartContent = () => {
  if (!chart || !graphRef.value) return

  const isCircleLayout = layoutType.value === 'circle'
  const layoutName = isCircleLayout ? 'none' : layoutType.value
  
  const nodes = kgStore.graphData.nodes.map(function(node) {
    return {
      id: node.id,
      name: node.name,
      type: node.type,
      symbolSize: 30,
      itemStyle: node.itemStyle || { color: getNodeColor(node.type) },
      label: {
        show: true,
        position: isCircleLayout ? 'outside' : 'right',
        formatter: '{b}',
        color: '#333'
      }
    }
  })
  
  const links = kgStore.graphData.links.map(function(link) {
    return {
      source: link.source,
      target: link.target,
      label: {
        show: true,
        formatter: link.label,
        color: '#666'
      },
      lineStyle: link.lineStyle || {
        width: 2,
        curveness: isCircleLayout ? 0.2 : 0.3,
        color: '#b388ff'
      },
      relationName: link.relationName || link.label
    }
  })
  
  if (isCircleLayout && nodes.length > 0) {
    const containerWidth = graphRef.value.clientWidth || 1000
    const containerHeight = graphRef.value.clientHeight || 600
    const centerX = containerWidth / 2
    const centerY = containerHeight / 2
    const radius = Math.min(Math.min(containerWidth, containerHeight) * 0.35, nodes.length * 30)
    
    nodes.forEach((node, index) => {
      const angle = (2 * Math.PI * index) / nodes.length - Math.PI / 2
      node.x = centerX + radius * Math.cos(angle)
      node.y = centerY + radius * Math.sin(angle)
    })
  }
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: function(params) {
        if (params.dataType === 'node') {
          return '实体: ' + params.data.name + '<br/>类型: ' + formatEntityType(params.data.type)
        } else {
          return '关系: ' + (params.data.relationName || '未知')
        }
      }
    },
    animationDurationUpdate: 1500,
    animationEasingUpdate: 'quinticInOut',
    series: [
      {
        type: 'graph',
        layout: layoutName,
        data: nodes,
        links: links,
        roam: true,
        label: {
          show: true,
          position: isCircleLayout ? 'outside' : 'right',
          formatter: '{b}',
          color: '#333'
        },
        lineStyle: {
          color: '#b388ff',
          curveness: isCircleLayout ? 0.2 : 0.3
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 4,
            color: '#7b2cbf'
          },
          itemStyle: {
            shadowBlur: 10,
            shadowColor: '#b388ff'
          }
        },
        force: {
          repulsion: 200,
          edgeLength: 100
        }
      }
    ]
  }
  
  try {
    chart.setOption(option, true)
  } catch (e) {
    console.error('Update chart error:', e)
  }
}

const safeUpdateChart = () => {
  initOrUpdateChart()
}

const getNodeColor = function(type) {
  const colorMap = {
    'PERSON': '#409eff',
    'ORG': '#67c23a',
    'LOCATION': '#e6a23c',
    'TIME': '#f56c6c',
    'EVENT': '#909399',
    'CONCEPT': '#909399',
    'OBJECT': '#d9a966'
  }
  return colorMap[type] || '#409eff'
}

const searchEntity = function() {
  if (!searchKeyword.value) return
  
  const node = kgStore.graphData.nodes.find(function(n) {
    return n.name.toLowerCase().includes(searchKeyword.value.toLowerCase())
  })
  
  if (node) {
    kgStore.selectNode(node)
    ElMessage.success({ message: '找到实体: ' + node.name, duration: 3000 })
  } else {
    ElMessage.warning({ message: '未找到匹配的实体', duration: 3000 })
  }
}

const resetView = function() {
  kgStore.clearGraph()
  initOrUpdateChart()
}

const handleResize = function() {
  if (chart) {
    try {
      chart.resize()
    } catch (e) {
      console.error('Resize error:', e)
    }
  }
}

let unwatch = watch(function() {
  return kgStore.graphData
}, function() {
  nextTick(() => {
    initOrUpdateChart()
  })
}, { deep: true })

onMounted(function() {
  loadAvailableFiles()
  nextTick(() => {
    nextTick(() => {
      nextTick(() => {
        initOrUpdateChart()
      })
    })
  })
})

onUnmounted(function() {
  if (unwatch) {
    unwatch()
  }
  
  if (chart) {
    try {
      chart.dispose()
    } catch (e) {
    }
  }
  chart = null
  
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.kg-visual-container {
  min-height: 80vh;
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
}

.page-header {
  text-align: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
}

.page-description {
  font-size: 14px;
  color: #666;
}

.card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 24px;
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: center;
  margin-bottom: 20px;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.card-body {
  padding-top: 8px;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.control-label {
  font-size: 14px;
  font-weight: 500;
  color: #666;
  white-space: nowrap;
}

.form-control {
  width: 200px;
}

.graph-container {
  width: 100%;
  height: 600px;
  background: #fafafa;
  border-radius: 8px;
  overflow: hidden;
}

.graph-canvas {
  width: 100%;
  height: 100%;
}

.entity-details {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-item {
  display: flex;
  align-items: center;
}

.detail-label {
  font-weight: 600;
  color: #666;
  margin-right: 12px;
  min-width: 100px;
}

.detail-value {
  color: #333;
}
</style>
