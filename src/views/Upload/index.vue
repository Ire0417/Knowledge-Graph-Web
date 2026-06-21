<template>
  <div class="upload-container">
    <div class="upload-header">
      <h1 class="upload-title">文件上传</h1>
    </div>
    
    <div class="upload-main">
      <div class="upload-left">
        <div class="upload-card">
          <el-upload
            drag
            :http-request="customUpload"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :before-upload="beforeUpload"
            multiple
            :limit="5"
            :file-list="fileList"
          >
            <div class="upload-text">拖放文件到此处，或<em>点击上传</em></div>
            <div class="upload-tip">
              支持PDF、Word、Excel、TXT、Markdown等格式，单个文件不超过100MB
            </div>
          </el-upload>
        </div>

        <div v-if="uploadProgress > 0 && uploadProgress < 100" class="upload-progress">
          <div class="progress">
            <div class="progress-bar" :style="{ width: uploadProgress + '%' }"></div>
          </div>
          <span class="progress-text">{{ uploadProgress }}%</span>
        </div>
        
        <div v-if="fileStore.parseStatus" class="parse-status">
          <div class="status-header">解析状态</div>
          <div class="progress">
            <div class="progress-bar" :style="{ width: fileStore.parseProgress + '%' }"></div>
          </div>
          <span class="status-text">{{ fileStore.parseStatus }}</span>
        </div>
      </div>
      
      <div class="upload-right">
        <div class="file-list-section">
          <div class="file-list-header">
            <span class="file-list-title">已上传文件</span>
          </div>
          <div v-if="fileStore.uploadedFiles.length > 0" class="file-table">
            <div v-for="file in fileStore.uploadedFiles" :key="file.id" class="file-row">
              <div class="file-name">{{ file.name }}</div>
              <div class="file-meta">
                <span>{{ formatFileSize(file.size) }}</span>
                <span>{{ formatTime(file.uploadTime) }}</span>
                <span :class="['file-status', getStatusClass(file.status)]">{{ file.status }}</span>
              </div>
              <div class="file-actions">
                <el-button size="mini" @click="parseFile(file.id)" :disabled="file.status === '解析中'">
                  解析
                </el-button>
                <el-button size="mini" type="danger" @click="deleteFile(file.id)">
                  删除
                </el-button>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <p>暂无上传文件，请点击上方区域上传</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useFileStore } from '../../store/fileStore'
import { uploadApi } from '../../api/upload'
import { validateFile } from '../../utils/validate'
import { formatFileSize, formatTime } from '../../utils/format'

const fileStore = useFileStore()
const fileList = ref([])
const uploadProgress = ref(0)

// 加载文件列表
const loadFileList = async () => {
  try {
    const response = await uploadApi.getFileList()
    if (response.success && response.files) {
      response.files.forEach(file => {
        // 如果文件还没在 store 里，添加进去
        const existingIndex = fileStore.uploadedFiles.findIndex(f => f.id === file.id)
        if (existingIndex >= 0) {
          // 更新现有文件的信息
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

const handleFileChange = (file, fileList) => {
  // 文件选择变化时的处理
}

const handleFileRemove = (file, fileList) => {
  // 文件移除时的处理
}

const beforeUpload = (file) => {
  const validation = validateFile(file)
  if (!validation.valid) {
    ElMessage.error(validation.message)
    return false
  }
  return true
}

onMounted(() => {
  loadFileList()
})

const customUpload = async (options) => {
  const { file } = options
  const formData = new FormData()
  formData.append('file', file)

  try {
    uploadProgress.value = 0
    fileStore.setUploadProgress(0)

    const response = await uploadApi.uploadFile(formData, (percent) => {
      uploadProgress.value = percent
      fileStore.setUploadProgress(percent)
    })

    if (response.success) {
      ElMessage.success('文件上传成功')
      fileStore.addFile({
        id: response.fileId,
        name: file.name,
        size: file.size,
        uploadTime: new Date(),
        status: '待解析'
      })
    } else {
      ElMessage.error('文件上传失败: ' + response.message)
    }
  } catch (error) {
    let errorMessage = '文件上传失败'
    if (error.response) {
      if (error.response.status === 500) {
        errorMessage = '服务器内部错误，请稍后重试'
      } else if (error.response.status === 400) {
        errorMessage = '请求参数错误'
      } else if (error.response.status === 401) {
        errorMessage = '未授权访问'
      } else if (error.response.status === 403) {
        errorMessage = '禁止访问'
      } else if (error.response.status === 404) {
        errorMessage = '接口不存在'
      }
    } else if (error.request) {
      errorMessage = '网络连接失败，请检查网络'
    }
    ElMessage.error(errorMessage)
  } finally {
    uploadProgress.value = 0
    fileStore.setUploadProgress(0)
  }
}

const parseFile = async (fileId) => {
  try {
    fileStore.setParseStatus('解析中...')
    fileStore.setParseProgress(0)
    
    const response = await uploadApi.parseFile(fileId)
    if (response.success) {
      if (response.warning) {
        ElMessage.warning('文件已解析，但知识问答索引构建失败：' + response.warning)
      }
      startParseProgressPolling(fileId)
    } else {
      ElMessage.error('解析失败: ' + response.message)
      fileStore.setParseStatus('解析失败')
    }
  } catch (error) {
    ElMessage.error('解析请求失败')
    fileStore.setParseStatus('解析失败')
  }
}

const startParseProgressPolling = (fileId) => {
  const interval = setInterval(async () => {
    try {
      const response = await uploadApi.getParseProgress(fileId)
      if (response.success) {
        const progress = response.progress
        fileStore.setParseProgress(progress)
        
        if (progress === 100) {
          clearInterval(interval)
          fileStore.setParseStatus('解析完成')
          ElMessage.success('文件解析成功')
          
          // 重新加载文件列表，获取完整的解析结果
          await loadFileList()
        }
      } else {
        clearInterval(interval)
        fileStore.setParseStatus('解析失败')
        ElMessage.error('解析失败: ' + response.message)
      }
    } catch (error) {
      clearInterval(interval)
      fileStore.setParseStatus('解析失败')
      ElMessage.error('获取解析进度失败')
    }
  }, 1000)
}

const deleteFile = async (fileId) => {
  try {
    const response = await uploadApi.deleteFile(fileId)
    if (response.success) {
      fileStore.removeFile(fileId)
      ElMessage.success('文件删除成功')
    } else {
      ElMessage.error('文件删除失败: ' + response.message)
    }
  } catch (error) {
    ElMessage.error('文件删除失败')
  }
}

const getStatusClass = (status) => {
  switch (status) {
    case '待解析':
      return 'status-pending'
    case '解析中':
      return 'status-processing'
    case '解析完成':
      return 'status-success'
    case '解析失败':
      return 'status-error'
    default:
      return ''
  }
}
</script>

<style scoped>
.upload-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.upload-header {
  margin-bottom: 16px;
}

.upload-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.upload-main {
  display: flex;
  gap: 20px;
}

.upload-left {
  flex: 0 0 400px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.upload-right {
  flex: 1;
  min-width: 0;
}

.upload-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e4e7ed;
}

.upload-demo :deep(.el-upload-dragger) {
  background: transparent;
  border: none;
  border-radius: 8px;
  min-height: 100px;
  padding: 16px;
}

.upload-demo :deep(.el-upload-dragger:hover) {
  border: none;
}

.upload-text {
  font-size: 14px;
  color: #606266;
  margin-bottom: 6px;
}

.upload-text em {
  color: #409eff;
  font-style: normal;
  font-weight: 500;
  cursor: pointer;
}

.upload-tip {
  font-size: 12px;
  color: #909399;
  text-align: center;
  margin-top: 8px;
}

.upload-progress {
  background: white;
  border-radius: 8px;
  padding: 12px 16px;
  border: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  gap: 12px;
}

.upload-progress .progress {
  flex: 1;
  height: 6px;
  background: #f0f2f5;
  border-radius: 3px;
  overflow: hidden;
}

.upload-progress .progress-bar {
  height: 100%;
  background: #409eff;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: #606266;
  min-width: 40px;
}

.file-list-section {
  background: white;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.file-list-header {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f2f5;
}

.file-list-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.file-table {
  padding: 0;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.file-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #f0f2f5;
}

.file-row:last-child {
  border-bottom: none;
}

.file-name {
  flex: 1;
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 12px;
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #909399;
  padding-right: 12px;
}

.file-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-pending {
  background: #fdf6ec;
  color: #e6a23c;
}

.status-processing {
  background: #ecf5ff;
  color: #409eff;
}

.status-success {
  background: #f0f9ff;
  color: #67c23a;
}

.status-error {
  background: #fef0f0;
  color: #f56c6c;
}

.file-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.file-actions :deep(.el-button) {
  padding: 4px 8px;
  height: 24px;
  font-size: 12px;
}

.empty-state {
  padding: 40px 16px;
  text-align: center;
  color: #909399;
  font-size: 14px;
}

.parse-status {
  background: white;
  border-radius: 8px;
  padding: 12px 16px;
  border: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-header {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
}

.parse-status .progress {
  flex: 1;
  height: 6px;
  background: #f0f2f5;
  border-radius: 3px;
  overflow: hidden;
}

.parse-status .progress-bar {
  height: 100%;
  background: #409eff;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.status-text {
  font-size: 12px;
  color: #606266;
  white-space: nowrap;
}

@media (max-width: 1000px) {
  .upload-main {
    flex-direction: column;
  }
  
  .upload-left {
    flex: none;
    width: 100%;
  }
}
</style>