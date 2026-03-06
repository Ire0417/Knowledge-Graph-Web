<template>
  <div class="kg-visual-container">
    <div class="page-header">
      <h1 class="page-title">知识图谱可视化</h1>
      <p class="page-description">交互式图谱展示，支持多种布局方式和路径查询</p>
    </div>
    
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">控制选项</h3>
      </div>
      <div class="card-body">
        <div class="visual-controls">
          <div class="control-group">
            <label class="control-label">布局方式</label>
            <el-select v-model="layoutType" @change="changeLayout" class="form-control">
              <el-option label="力导向图" value="force" />
              <el-option label="环形布局" value="circle" />
              <el-option label="辐射布局" value="radial" />
              <el-option label="树形布局" value="tree" />
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
          
          <div class="control-buttons">
            <button class="btn btn-secondary" @click="resetView">重置视图</button>
            <button class="btn btn-secondary" @click="expandAll">展开全部</button>
            <button class="btn btn-secondary" @click="collapseAll">收起全部</button>
          </div>
        </div>
      </div>
    </div>
    
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">图谱展示</h3>
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
          <div class="detail-item">
            <span class="detail-label">相关关系:</span>
            <div class="relation-tags">
              <span 
                v-for="(link, index) in getRelatedLinks(kgStore.selectedNode.id)" 
                :key="index"
                class="relation-tag"
              >
                {{ link.relationship }} → {{ getNodeName(link.target) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">路径查询</h3>
      </div>
      <div class="card-body">
        <div class="path-query-form">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">起始实体</label>
              <el-select v-model="sourceNodeId" placeholder="选择起始实体" class="form-control">
                <el-option
                  v-for="node in kgStore.graphData.nodes"
                  :key="node.id"
                  :label="node.name"
                  :value="node.id"
                />
              </el-select>
            </div>
            <div class="form-group">
              <label class="form-label">目标实体</label>
              <el-select v-model="targetNodeId" placeholder="选择目标实体" class="form-control">
                <el-option
                  v-for="node in kgStore.graphData.nodes"
                  :key="node.id"
                  :label="node.name"
                  :value="node.id"
                />
              </el-select>
            </div>
            <div class="form-group form-group-button">
              <button class="btn btn-primary" @click="queryPath">查询路径</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useKgStore } from '../../store/kgStore'
import { visualApi } from '../../api/visual'
import { formatEntityType, formatRelationType } from '../../utils/format'
import * as echarts from 'echarts'

const kgStore = useKgStore()
const graphRef = ref(null)
let chart = null
const layoutType = ref('force')
const searchKeyword = ref('')
const sourceNodeId = ref('')
const targetNodeId = ref('')

const initChart = function() {
  if (chart) {
    chart.dispose()
  }
  chart = echarts.init(graphRef.value)
  updateChart()
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
  
  // 监听节点点击事件
  chart.on('click', function(params) {
    if (params.dataType === 'node') {
      kgStore.selectNode(params.data)
      // 切换节点展开/折叠状态
      kgStore.toggleNodeExpansion(params.data.id)
      updateChart()
    }
  })
}

const updateChart = function() {
  if (!chart) return
  
  const nodes = kgStore.graphData.nodes.map(function(node) {
    return {
      id: node.id,
      name: node.name,
      type: node.type,
      symbolSize: 30,
      itemStyle: {
        color: getNodeColor(node.type)
      },
      label: {
        show: true,
        position: 'right',
        formatter: '{b}',
        color: '#ffffff'
      }
    }
  })
  
  const links = kgStore.graphData.links.map(function(link) {
    return {
      source: link.source,
      target: link.target,
      label: {
        show: true,
        formatter: link.relationship,
        color: 'rgba(255, 255, 255, 0.7)'
      },
      lineStyle: {
        width: 2,
        curveness: 0.3,
        color: '#b388ff'
      }
    }
  })
  
  const option = {
    title: {
      text: '知识图谱',
      left: 'center',
      textStyle: {
        color: '#ffffff'
      }
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(15, 15, 26, 0.9)',
      borderColor: 'rgba(255, 255, 255, 0.2)',
      textStyle: {
        color: '#ffffff'
      },
      formatter: function(params) {
        if (params.dataType === 'node') {
          return '实体: ' + params.data.name + '<br/>类型: ' + formatEntityType(params.data.type)
        } else {
          return '关系: ' + params.data.label.formatter
        }
      }
    },
    animationDurationUpdate: 1500,
    animationEasingUpdate: 'quinticInOut',
    series: [
      {
        type: 'graph',
        layout: layoutType.value,
        data: nodes,
        links: links,
        roam: true,
        label: {
          show: true,
          position: 'right',
          formatter: '{b}',
          color: '#ffffff'
        },
        lineStyle: {
          color: '#b388ff',
          curveness: 0.3
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
        }
      }
    ]
  }
  
  chart.setOption(option)
}

const getNodeColor = function(type) {
  const colorMap = {
    'PERSON': '#409eff',
    'ORG': '#67c23a',
    'LOCATION': '#e6a23c',
    'TIME': '#f56c6c',
    'EVENT': '#909399',
    'CONCEPT': '#c0c4cc',
    'OBJECT': '#d9a966'
  }
  return colorMap[type] || '#909399'
}

const getRelatedLinks = function(nodeId) {
  return kgStore.graphData.links.filter(function(link) {
    return link.source === nodeId
  })
}

const getNodeName = function(nodeId) {
  const node = kgStore.graphData.nodes.find(function(n) {
    return n.id === nodeId
  })
  return node ? node.name : '未知实体'
}

const changeLayout = function() {
  updateChart()
}

const searchEntity = function() {
  if (!searchKeyword.value) return
  
  const node = kgStore.graphData.nodes.find(function(n) {
    return n.name.toLowerCase().includes(searchKeyword.value.toLowerCase())
  })
  
  if (node) {
    kgStore.selectNode(node)
    // 高亮显示该节点
    chart.dispatchAction({
      type: 'showTip',
      seriesIndex: 0,
      dataIndex: kgStore.graphData.nodes.indexOf(node)
    })
  } else {
    ElMessage.warning('未找到匹配的实体')
  }
}

const resetView = function() {
  chart.dispatchAction({ type: 'restore' })
  kgStore.clearGraph()
}

const expandAll = function() {
  // 展开所有节点
  kgStore.graphData.nodes.forEach(function(node) {
    if (kgStore.expandedNodes.indexOf(node.id) === -1) {
      kgStore.expandedNodes.push(node.id)
    }
  })
  updateChart()
}

const collapseAll = function() {
  // 收起所有节点
  kgStore.expandedNodes = []
  updateChart()
}

const queryPath = async function() {
  if (!sourceNodeId.value || !targetNodeId.value) {
    ElMessage.warning('请选择起始实体和目标实体')
    return
  }
  
  try {
    const response = await visualApi.queryPath('current', sourceNodeId.value, targetNodeId.value)
    if (response.success) {
      // 高亮显示路径
      const pathNodes = response.data.nodes
      const pathLinks = response.data.links
      
      // 更新图表显示路径
      const option = chart.getOption()
      option.series[0].data = pathNodes.map(function(node) {
        return {
          ...node,
          symbolSize: 40,
          itemStyle: {
            color: getNodeColor(node.type),
            borderColor: '#fff',
            borderWidth: 2
          }
        }
      })
      option.series[0].links = pathLinks.map(function(link) {
        return {
          ...link,
          lineStyle: {
            width: 4,
            color: '#f56c6c',
            curveness: 0.3
          }
        }
      })
      chart.setOption(option)
      
      ElMessage.success('路径查询成功')
    } else {
      ElMessage.error('路径查询失败: ' + response.message)
    }
  } catch (error) {
    ElMessage.error('路径查询请求失败')
  }
}

const handleResize = function() {
  chart.resize()
}

// 监听图谱数据变化
watch(function() {
  return kgStore.graphData
}, function() {
  updateChart()
}, { deep: true })

onMounted(function() {
  initChart()
})

onUnmounted(function() {
  if (chart) {
    chart.dispose()
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.kg-visual-container {
  min-height: 80vh;
  padding: 40px 0;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #ffffff, rgba(255, 255, 255, 0.7));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-description {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7);
  max-width: 800px;
  margin: 0 auto;
}

.card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  padding: 24px;
  margin-bottom: 24px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
}

.card-body {
  padding-top: 8px;
}

.visual-controls {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  align-items: flex-end;
}

.control-group {
  flex: 1;
  min-width: 200px;
}

.control-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
}

.form-control {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: #ffffff;
  transition: all 0.3s ease;
}

.form-control:focus {
  outline: none;
  border-color: #7b2cbf;
  box-shadow: 0 0 0 3px rgba(123, 44, 191, 0.2);
}

.control-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.graph-container {
  width: 100%;
  height: 600px;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(15, 15, 26, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.2);
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
  flex-direction: column;
  gap: 8px;
}

.detail-label {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
}

.detail-value {
  font-size: 16px;
  color: #ffffff;
}

.relation-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.relation-tag {
  display: inline-block;
  padding: 4px 12px;
  background: rgba(123, 44, 191, 0.2);
  border: 1px solid #7b2cbf;
  border-radius: 16px;
  font-size: 12px;
  color: #b388ff;
}

.path-query-form {
  width: 100%;
}

.form-row {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  align-items: flex-end;
}

.form-group {
  flex: 1;
  min-width: 200px;
}

.form-group-button {
  flex: 0 0 auto;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
}

@media (max-width: 768px) {
  .visual-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .control-group {
    width: 100%;
  }
  
  .control-buttons {
    flex-direction: column;
  }
  
  .form-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .form-group {
    width: 100%;
  }
  
  .graph-container {
    height: 400px;
  }
}
</style>