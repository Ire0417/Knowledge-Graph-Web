<template>
  <div class="kg-build-container">
    <div class="page-header">
      <h1 class="page-title">知识图谱构建</h1>
      <p class="page-description">从解析的文件中构建知识图谱，支持实体对齐、关系合并和图谱优化</p>
    </div>
    
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">选择文件</h3>
      </div>
      <div class="card-body">
        <div class="form-item">
          <el-select v-model="selectedFileId" placeholder="请选择已解析的文件" class="form-control">
            <el-option
              v-for="file in fileStore.uploadedFiles"
              :key="file.id"
              :label="file.name"
              :value="file.id"
              :disabled="file.status !== '解析完成'"
            />
          </el-select>
          <p class="form-hint">请选择状态为"解析完成"的文件</p>
        </div>
      </div>
    </div>
    
    <div v-if="selectedFileId" class="card">
      <div class="card-header">
        <h3 class="card-title">构建操作</h3>
      </div>
      <div class="card-body">
        <div class="action-buttons">
          <button class="btn btn-primary" @click="buildGraph" :disabled="isBuilding">
            开始构建图谱
          </button>
          <button class="btn btn-secondary" @click="alignEntities" :disabled="isBuilding">
            实体对齐
          </button>
          <button class="btn btn-secondary" @click="mergeRelations" :disabled="isBuilding">
            关系合并
          </button>
          <button class="btn btn-secondary" @click="optimizeGraph" :disabled="isBuilding">
            图谱优化
          </button>
        </div>
      </div>
    </div>
    
    <div v-if="kgStore.buildStatus" class="card">
      <div class="card-header">
        <h3 class="card-title">构建状态</h3>
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
        <h3 class="card-title">图谱统计信息</h3>
      </div>
      <div class="card-body">
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-icon">🔍</div>
            <div class="stat-content">
              <div class="stat-value">{{ kgStore.graphData.nodes.length }}</div>
              <div class="stat-label">实体数量</div>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon">🔗</div>
            <div class="stat-content">
              <div class="stat-value">{{ kgStore.graphData.links.length }}</div>
              <div class="stat-label">关系数量</div>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon">📊</div>
            <div class="stat-content">
              <div class="stat-value">{{ getEntityTypesCount() }}</div>
              <div class="stat-label">实体类型</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="kgStore.hasGraphData" class="card">
      <div class="card-header">
        <h3 class="card-title">构建结果</h3>
      </div>
      <div class="card-body">
        <div class="result-buttons">
          <button class="btn btn-primary" @click="navigateToVisual">
            查看图谱可视化
          </button>
          <button class="btn btn-secondary" @click="exportGraph">
            导出图谱数据
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useFileStore } from '../../store/fileStore'
import { useKgStore } from '../../store/kgStore'
import { graphApi } from '../../api/graph'
import { extractApi } from '../../api/extract'
import { useRouter } from 'vue-router'

const fileStore = useFileStore()
const kgStore = useKgStore()
const router = useRouter()
const selectedFileId = ref('')
const isBuilding = ref(false)

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
    ElMessage.warning('请选择一个已解析的文件')
    return
  }
  
  try {
    isBuilding.value = true
    kgStore.setBuildStatus('提取知识中...')
    kgStore.setBuildProgress(0)
    
    // 先提取知识
    const extractResponse = await extractApi.extractFromFile(selectedFileId.value)
    if (!extractResponse.success) {
      ElMessage.error('知识提取失败: ' + extractResponse.message)
      kgStore.setBuildStatus('提取失败')
      isBuilding.value = false
      return
    }
    
    // 开始轮询提取进度
    await startExtractProgressPolling(selectedFileId.value)
    
    // 提取完成后构建图谱
    kgStore.setBuildStatus('构建中...')
    const buildResponse = await graphApi.buildGraph(selectedFileId.value)
    if (buildResponse.success) {
      // 开始轮询构建进度
      startBuildProgressPolling(selectedFileId.value)
    } else {
      ElMessage.error('构建失败: ' + buildResponse.message)
      kgStore.setBuildStatus('构建失败')
      isBuilding.value = false
    }
  } catch (error) {
    ElMessage.error('构建请求失败')
    kgStore.setBuildStatus('构建失败')
    isBuilding.value = false
  }
}

const startExtractProgressPolling = (fileId) => {
  return new Promise((resolve, reject) => {
    const interval = setInterval(async () => {
      try {
        const response = await extractApi.getExtractProgress(fileId)
        if (response.success) {
          const progress = response.progress
          kgStore.setBuildProgress(progress)
          
          if (progress === 100) {
            clearInterval(interval)
            kgStore.setBuildStatus('提取完成')
            ElMessage.success('知识提取成功')
            resolve()
          }
        } else {
          clearInterval(interval)
          kgStore.setBuildStatus('提取失败')
          ElMessage.error('提取失败: ' + response.message)
          reject(new Error('提取失败'))
        }
      } catch (error) {
        clearInterval(interval)
        kgStore.setBuildStatus('提取失败')
        ElMessage.error('获取提取进度失败')
        reject(error)
      }
    }, 1000)
  })
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
          ElMessage.success('图谱构建成功')
          
          // 获取图谱数据
          await fetchGraphData(fileId)
          isBuilding.value = false
        }
      } else {
        clearInterval(interval)
        kgStore.setBuildStatus('构建失败')
        ElMessage.error('构建失败: ' + response.message)
        isBuilding.value = false
      }
    } catch (error) {
      clearInterval(interval)
      kgStore.setBuildStatus('构建失败')
      ElMessage.error('获取构建进度失败')
      isBuilding.value = false
    }
  }, 1000)
}

const fetchGraphData = async (fileId) => {
  try {
    const response = await graphApi.getGraphData(fileId)
    if (response.success) {
      kgStore.setGraphData(response.data)
    } else {
      ElMessage.error('获取图谱数据失败: ' + response.message)
    }
  } catch (error) {
    ElMessage.error('获取图谱数据失败')
  }
}

const alignEntities = async () => {
  if (!selectedFileId.value) {
    ElMessage.warning('请选择一个已解析的文件')
    return
  }
  
  try {
    isBuilding.value = true
    kgStore.setBuildStatus('实体对齐中...')
    
    const response = await graphApi.alignEntities(selectedFileId.value)
    if (response.success) {
      ElMessage.success('实体对齐成功')
      kgStore.setBuildStatus('实体对齐完成')
      
      // 重新获取图谱数据
      await fetchGraphData(selectedFileId.value)
    } else {
      ElMessage.error('实体对齐失败: ' + response.message)
      kgStore.setBuildStatus('实体对齐失败')
    }
    isBuilding.value = false
  } catch (error) {
    ElMessage.error('实体对齐请求失败')
    kgStore.setBuildStatus('实体对齐失败')
    isBuilding.value = false
  }
}

const mergeRelations = async () => {
  if (!selectedFileId.value) {
    ElMessage.warning('请选择一个已解析的文件')
    return
  }
  
  try {
    isBuilding.value = true
    kgStore.setBuildStatus('关系合并中...')
    
    const response = await graphApi.mergeRelations(selectedFileId.value)
    if (response.success) {
      ElMessage.success('关系合并成功')
      kgStore.setBuildStatus('关系合并完成')
      
      // 重新获取图谱数据
      await fetchGraphData(selectedFileId.value)
    } else {
      ElMessage.error('关系合并失败: ' + response.message)
      kgStore.setBuildStatus('关系合并失败')
    }
    isBuilding.value = false
  } catch (error) {
    ElMessage.error('关系合并请求失败')
    kgStore.setBuildStatus('关系合并失败')
    isBuilding.value = false
  }
}

const optimizeGraph = async () => {
  if (!selectedFileId.value) {
    ElMessage.warning('请选择一个已解析的文件')
    return
  }
  
  try {
    isBuilding.value = true
    kgStore.setBuildStatus('图谱优化中...')
    
    const response = await graphApi.optimizeGraph(selectedFileId.value)
    if (response.success) {
      ElMessage.success('图谱优化成功')
      kgStore.setBuildStatus('图谱优化完成')
      
      // 重新获取图谱数据
      await fetchGraphData(selectedFileId.value)
    } else {
      ElMessage.error('图谱优化失败: ' + response.message)
      kgStore.setBuildStatus('图谱优化失败')
    }
    isBuilding.value = false
  } catch (error) {
    ElMessage.error('图谱优化请求失败')
    kgStore.setBuildStatus('图谱优化失败')
    isBuilding.value = false
  }
}

const navigateToVisual = () => {
  router.push('/kg-visual')
}

const exportGraph = async () => {
  if (!selectedFileId.value) {
    ElMessage.warning('请选择一个已解析的文件')
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
  background: linear-gradient(135deg, var(--text-primary), var(--text-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-description {
  font-size: 16px;
  color: var(--text-secondary);
  max-width: 800px;
  margin: 0 auto;
}

.card {
  background: var(--card-background);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-md);
  padding: 24px;
  margin-bottom: 24px;
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.card-body {
  padding-top: 8px;
}

.form-item {
  margin-bottom: 24px;
}

.form-control {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-md);
  color: var(--text-primary);
  transition: all 0.3s ease;
}

.form-control:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(123, 44, 191, 0.2);
}

.form-hint {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 8px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.status-text {
  text-align: center;
  margin-top: 12px;
  font-size: 14px;
  color: var(--text-secondary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
}

.stat-item {
  background: rgba(255, 255, 255, 0.05);
  border-radius: var(--border-radius-md);
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.stat-icon {
  font-size: 24px;
  color: var(--primary-light);
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(123, 44, 191, 0.1);
  border-radius: var(--border-radius-md);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.result-buttons {
  display: flex;
  gap: 12px;
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