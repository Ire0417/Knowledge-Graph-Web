<template>
  <div class="kg-build-container">
    <div class="page-header">
      <h1 class="page-title">知识图谱构建</h1>
    </div>
    
    <div class="card">
      <div class="card-header">
        <span class="card-title">选择文件</span>
      </div>
      <div class="card-body">
        <el-select v-model="selectedFileId" placeholder="请选择已解析的文件" class="form-control">
          <el-option
            v-for="file in fileStore.uploadedFiles"
            :key="file.id"
            :label="file.name + (file.extract_result ? ' (已提取)' : '')"
            :value="file.id"
            :disabled="file.status !== '解析完成' && file.status !== '已提取' && file.status !== 'graph_built'"
          />
        </el-select>
        <p class="form-hint">请选择状态为"解析完成"或"已提取"的文件</p>
      </div>
    </div>
    
    <div v-if="selectedFileId" class="card">
      <div class="card-header">
        <span class="card-title">构建操作</span>
      </div>
      <div class="card-body">
        <div class="action-buttons">
          <el-button type="primary" @click="buildGraph" :disabled="isBuilding" :loading="isBuilding">
            开始构建图谱
          </el-button>
          <el-button @click="alignEntities" :disabled="isBuilding">
            实体对齐
          </el-button>
          <el-button @click="mergeRelations" :disabled="isBuilding">
            关系合并
          </el-button>
          <el-button @click="optimizeGraph" :disabled="isBuilding">
            图谱优化
          </el-button>
        </div>
      </div>
    </div>
    
    <div v-if="kgStore.buildStatus" class="card">
      <div class="card-header">
        <span class="card-title">构建状态</span>
      </div>
      <div class="card-body">
        <div class="progress">
          <div class="progress-bar" :style="{ width: kgStore.buildProgress + '%' }"></div>
        </div>
        <p class="status-text">{{ kgStore.buildStatus }}</p>
      </div>
    </div>
    
    <div v-if="kgStore.hasGraphData" class="card">
      <div class="card-header">
        <span class="card-title">图谱统计信息</span>
      </div>
      <div class="card-body">
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-value">{{ kgStore.graphData.nodes.length }}</div>
            <div class="stat-label">实体数量</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ kgStore.graphData.links.length }}</div>
            <div class="stat-label">关系数量</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ getEntityTypesCount() }}</div>
            <div class="stat-label">实体类型</div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="kgStore.hasGraphData" class="card">
      <div class="card-header">
        <span class="card-title">构建结果</span>
      </div>
      <div class="card-body">
        <div class="result-buttons">
          <el-button type="primary" @click="navigateToVisual">
            查看图谱可视化
          </el-button>
          <el-button @click="exportGraph">
            导出图谱数据
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useFileStore } from '../../store/fileStore'
import { useKgStore } from '../../store/kgStore'
import { graphApi } from '../../api/graph'
import { uploadApi } from '../../api/upload'
import { useRouter } from 'vue-router'

const fileStore = useFileStore()
const kgStore = useKgStore()
const router = useRouter()
const selectedFileId = ref('')
const isBuilding = ref(false)

// 加载文件列表
const loadFileList = async () => {
  try {
    const response = await uploadApi.getFileList()
    if (response.success && response.files) {
      response.files.forEach(file => {
        const existingIndex = fileStore.uploadedFiles.findIndex(f => f.id === file.id)
        if (existingIndex >= 0) {
          fileStore.uploadedFiles[existingIndex] = {
            ...fileStore.uploadedFiles[existingIndex],
            ...file
          }
        } else {
          fileStore.addFile(file)
        }
      })
    }
  } catch (error) {
    console.error('加载文件列表失败:', error)
  }
}

onMounted(() => {
  loadFileList()
})

const getEntityTypesCount = () => {
  const types = new Set()
  kgStore.graphData.nodes.forEach(node => {
    if (node.type) {
      types.add(node.type)
    }
  })
  return types.size
}

const buildGraph = async () => {
  if (!selectedFileId.value) {
    ElMessage.warning({ message: '请选择一个已解析的文件', duration: 3000 })
    return
  }
  
  try {
    isBuilding.value = true
    kgStore.setBuildStatus('构建图谱中...')
    kgStore.setBuildProgress(10)
    
    // 直接构建图谱，不再重新抽取
    const buildResponse = await graphApi.buildGraph(selectedFileId.value)
    if (buildResponse.success) {
      if (buildResponse.already_built) {
        // 图谱已经构建过，直接获取数据
        ElMessage.success({ message: '图谱已构建完成', duration: 3000 })
        kgStore.setBuildProgress(100)
        await fetchGraphData(selectedFileId.value)
      } else {
        // 开始轮询构建进度
        kgStore.setBuildProgress(30)
        startBuildProgressPolling(selectedFileId.value)
      }
    } else if (buildResponse.need_extraction) {
      // 需要先抽取
      ElMessage.warning({ message: '请先在知识抽取页面完成抽取', duration: 3000 })
      kgStore.setBuildStatus('等待抽取')
      isBuilding.value = false
    } else {
      ElMessage.error({ message: '构建失败: ' + buildResponse.message, duration: 3000 })
      kgStore.setBuildStatus('构建失败')
      isBuilding.value = false
    }
  } catch (error) {
    ElMessage.error({ message: '构建请求失败', duration: 3000 })
    kgStore.setBuildStatus('构建失败')
    isBuilding.value = false
  }
}

const startBuildProgressPolling = (fileId) => {
  const interval = setInterval(async () => {
    try {
      const response = await graphApi.getBuildProgress(fileId)
      if (response.success) {
        const progress = response.progress
        kgStore.setBuildProgress(progress)
        
        if (progress === 100) {
          clearInterval(interval)
          kgStore.setBuildStatus('构建完成')
          ElMessage.success({ message: '图谱构建成功', duration: 3000 })
          
          // 获取图谱数据
          await fetchGraphData(fileId)
          isBuilding.value = false
        }
      } else {
        clearInterval(interval)
        kgStore.setBuildStatus('构建失败')
        ElMessage.error({ message: '构建失败: ' + response.message, duration: 3000 })
        isBuilding.value = false
      }
    } catch (error) {
      clearInterval(interval)
      kgStore.setBuildStatus('构建失败')
      ElMessage.error({ message: '获取构建进度失败', duration: 3000 })
      isBuilding.value = false
    }
  }, 1000)
}

const fetchGraphData = async (fileId) => {
  try {
    const response = await graphApi.getGraphData(fileId)
    if (response.success) {
      // 将后端返回的数据转换为前端需要的格式
      const entities = response.data.entities || []
      const relationships = response.data.relationships || []
      const nodes = entities.map(ent => ({
        id: ent.id,
        name: ent.label,
        type: ent.type,
        itemStyle: {
          color: ent.color || '#409eff'
        }
      }))
      const links = relationships.map(rel => ({
        source: rel.source,
        target: rel.target,
        label: rel.label,
        lineStyle: {
          color: '#b388ff'
        }
      }))
      kgStore.setGraphData({ nodes, links })
    } else {
      ElMessage.error({ message: '获取图谱数据失败: ' + response.message, duration: 3000 })
    }
  } catch (error) {
    ElMessage.error({ message: '获取图谱数据失败', duration: 3000 })
  }
}

const alignEntities = async () => {
  if (!selectedFileId.value) {
    ElMessage.warning({ message: '请选择一个已解析的文件', duration: 3000 })
    return
  }
  
  try {
    isBuilding.value = true
    kgStore.setBuildStatus('实体对齐中...')
    
    const response = await graphApi.alignEntities(selectedFileId.value)
    if (response.success) {
      ElMessage.success({ message: '实体对齐成功', duration: 3000 })
      kgStore.setBuildStatus('实体对齐完成')
      
      // 重新获取图谱数据
      await fetchGraphData(selectedFileId.value)
    } else {
      ElMessage.error({ message: '实体对齐失败: ' + response.message, duration: 3000 })
      kgStore.setBuildStatus('实体对齐失败')
    }
    isBuilding.value = false
  } catch (error) {
    ElMessage.error({ message: '实体对齐请求失败', duration: 3000 })
    kgStore.setBuildStatus('实体对齐失败')
    isBuilding.value = false
  }
}

const mergeRelations = async () => {
  if (!selectedFileId.value) {
    ElMessage.warning({ message: '请选择一个已解析的文件', duration: 3000 })
    return
  }
  
  try {
    isBuilding.value = true
    kgStore.setBuildStatus('关系合并中...')
    
    const response = await graphApi.mergeRelations(selectedFileId.value)
    if (response.success) {
      ElMessage.success({ message: '关系合并成功', duration: 3000 })
      kgStore.setBuildStatus('关系合并完成')
      
      // 重新获取图谱数据
      await fetchGraphData(selectedFileId.value)
    } else {
      ElMessage.error({ message: '关系合并失败: ' + response.message, duration: 3000 })
      kgStore.setBuildStatus('关系合并失败')
    }
    isBuilding.value = false
  } catch (error) {
    ElMessage.error({ message: '关系合并请求失败', duration: 3000 })
    kgStore.setBuildStatus('关系合并失败')
    isBuilding.value = false
  }
}

const optimizeGraph = async () => {
  if (!selectedFileId.value) {
    ElMessage.warning({ message: '请选择一个已解析的文件', duration: 3000 })
    return
  }
  
  try {
    isBuilding.value = true
    kgStore.setBuildStatus('图谱优化中...')
    
    const response = await graphApi.optimizeGraph(selectedFileId.value)
    if (response.success) {
      ElMessage.success({ message: '图谱优化成功', duration: 3000 })
      kgStore.setBuildStatus('图谱优化完成')
      
      // 重新获取图谱数据
      await fetchGraphData(selectedFileId.value)
    } else {
      ElMessage.error({ message: '图谱优化失败: ' + response.message, duration: 3000 })
      kgStore.setBuildStatus('图谱优化失败')
    }
    isBuilding.value = false
  } catch (error) {
    ElMessage.error({ message: '图谱优化请求失败', duration: 3000 })
    kgStore.setBuildStatus('图谱优化失败')
    isBuilding.value = false
  }
}

const navigateToVisual = () => {
  router.push('/kg-visual')
}

const exportGraph = async () => {
  if (!selectedFileId.value) {
    ElMessage.warning({ message: '请选择一个已解析的文件', duration: 3000 })
    return
  }
  
  try {
    const response = await graphApi.exportGraph(selectedFileId.value, 'json')
    
    // 创建下载链接
    const blob = new Blob([response], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `graph_${selectedFileId.value}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    ElMessage.success('图谱数据导出成功')
  } catch (error) {
    ElMessage.error('图谱数据导出失败')
  }
}
</script>

<style scoped>
.kg-build-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 16px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.card {
  background: white;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  margin-bottom: 16px;
}

.card-header {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f2f5;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.card-body {
  padding: 16px;
}

.form-control {
  width: 100%;
}

.form-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.progress {
  height: 6px;
  background: #f0f2f5;
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: #409eff;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.status-text {
  text-align: center;
  margin-top: 12px;
  font-size: 14px;
  color: #606266;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.result-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .action-buttons {
    flex-direction: column;
  }
  
  .result-buttons {
    flex-direction: column;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
