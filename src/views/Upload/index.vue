<template>
  <div class="upload-container">
    <div class="upload-header">
      <h1 class="upload-title">文件上传与解析</h1>
      <p class="upload-description">上传PDF、Word、Excel等多模态文件，系统将自动解析并提取知识</p>
    </div>
    
    <div class="upload-card">
      <el-upload
        class="upload-demo"
        drag
        :action="uploadUrl"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        :before-upload="beforeUpload"
        :on-progress="handleUploadProgress"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        multiple
        :limit="5"
        :file-list="fileList"
      >
        <div class="upload-icon">📁</div>
        <div class="upload-text">拖放文件到此处，或<em>点击上传</em></div>
        <div class="upload-tip">
          支持上传PDF、Word、Excel、TXT、Markdown等格式文件，单个文件大小不超过100MB
        </div>
      </el-upload>
    </div>
    
    <div v-if="uploadProgress > 0 && uploadProgress < 100" class="upload-progress">
      <h3>上传进度</h3>
      <div class="progress">
        <div class="progress-bar" :style="{ width: uploadProgress + '%' }"></div>
      </div>
      <p class="progress-text">{{ uploadProgress }}%</p>
    </div>
    
    <div class="file-list-section">
      <div class="file-list-header">
        <h2 class="file-list-title">已上传文件</h2>
      </div>
      <div v-if="fileStore.uploadedFiles.length > 0" class="file-grid">
        <div class="file-card" v-for="file in fileStore.uploadedFiles" :key="file.id">
          <div class="file-header">
            <div class="file-info">
              <div class="file-name">
                <span class="file-icon">📄</span>
                <span>{{ file.name }}</span>
              </div>
              <div class="file-meta">
                <span class="file-size">{{ formatFileSize(file.size) }}</span>
                <span class="file-time">{{ formatTime(file.uploadTime) }}</span>
                <span :class="['file-status', getStatusClass(file.status)]">{{ file.status }}</span>
              </div>
            </div>
            <div class="file-actions">
              <button class="btn btn-sm btn-primary" @click="parseFile(file.id)" :disabled="file.status === '解析中'">
                解析
              </button>
              <button class="btn btn-sm btn-secondary" @click="deleteFile(file.id)">
                删除
              </button>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">
        <div class="empty-icon">📁</div>
        <h3>暂无上传文件</h3>
        <p>请点击上方区域上传文件</p>
      </div>
    </div>
    
    <div v-if="fileStore.parseStatus" class="parse-status">
      <h3>解析状态</h3>
      <div class="progress">
        <div class="progress-bar" :style="{ width: fileStore.parseProgress + '%' }"></div>
      </div>
      <p class="status-text">{{ fileStore.parseStatus }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useFileStore } from '../../store/fileStore'
import { uploadApi } from '../../api/upload'
import { validateFile } from '../../utils/validate'
import { formatFileSize, formatTime } from '../../utils/format'

const fileStore = useFileStore()
const fileList = ref([])
const uploadProgress = ref(0)
// 使用前端代理路径，确保请求经过Vite代理转发到后端
const uploadUrl = '/api/upload'

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

const handleUploadProgress = (event, file, fileList) => {
  const percent = Math.round((event.loaded * 100) / event.total)
  uploadProgress.value = percent
  fileStore.setUploadProgress(percent)
}

const handleUploadSuccess = (response, file, fileList) => {
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
  uploadProgress.value = 0
  fileStore.setUploadProgress(0)
}

const handleUploadError = (error, file, fileList) => {
  // 详细的错误处理
  let errorMessage = '文件上传失败'
  if (error.response) {
    // 服务器返回错误
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
    // 请求已发出但没有收到响应
    errorMessage = '网络连接失败，请检查网络'
  } else {
    // 请求配置出错
    errorMessage = '请求配置错误'
  }
  ElMessage.error(errorMessage)
  uploadProgress.value = 0
  fileStore.setUploadProgress(0)
}

const parseFile = async (fileId) => {
  try {
    fileStore.setParseStatus('解析中...')
    fileStore.setParseProgress(0)
    
    const response = await uploadApi.parseFile(fileId)
    if (response.success) {
      // 开始轮询解析进度
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
          
          // 更新文件状态
          const file = fileStore.uploadedFiles.find(f => f.id === fileId)
          if (file) {
            file.status = '解析完成'
          }
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
/* 上传容器样式 */
.upload-container {
  min-height: 80vh;
  padding: 40px 0;
}

/* 头部标题样式 */
.upload-header {
  text-align: center;
  margin-bottom: 40px;
}

.upload-title {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #ffffff; /* 白色粗体标题 */
}

.upload-description {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7); /* 浅灰色小字 */
  max-width: 800px;
  margin: 0 auto;
}

/* 上传卡片样式 - 核心修改 */
.upload-card {
  /* 半透明白色背景，融入页面背景 */
  background: rgba(255, 255, 255, 0.05);
  border-radius: var(--border-radius-lg);
  /* 移除默认阴影，减少视觉割裂 */
  box-shadow: none;
  padding: 40px;
  margin-bottom: 40px;
  /* 1px虚线边框，保留区域辨识度 */
  border: 1px dashed rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.upload-card:hover {
  /* 悬停时微调背景和边框，强化交互反馈 */
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.4);
  transform: translateY(-4px);
  /* 添加微妙阴影，增强层次感 */
  box-shadow: var(--shadow-lg);
}

/* 覆盖Element Plus上传组件样式 */
.upload-demo {
  background: transparent !important;
  border: none !important;
}

.upload-demo .el-upload-dragger {
  /* 完全透明背景，避免白色背景突兀 */
  background: transparent !important;
  /* 移除默认边框，使用父容器的虚线边框 */
  border: none !important;
  border-radius: var(--border-radius-lg) !important;
  padding: 40px !important;
  transition: all 0.3s ease !important;
}

.upload-demo .el-upload-dragger:hover {
  /* 悬停时不添加额外边框，保持简洁 */
  border: none !important;
  box-shadow: none !important;
}

.upload-demo .el-upload__text {
  color: rgba(255, 255, 255, 0.7) !important; /* 浅灰色文字 */
}

.upload-demo .el-upload__text em {
  color: #b388ff !important; /* 紫色交互文字 */
}

.upload-demo .el-upload__tip {
  color: rgba(255, 255, 255, 0.7) !important; /* 浅灰色提示文字 */
}

/* 上传图标样式 - 降低亮度和饱和度 */
.upload-icon {
  font-size: 48px;
  margin-bottom: 24px;
  color: var(--primary-light);
  /* 降低亮度和饱和度，适配深色背景 */
  filter: brightness(0.8) saturate(0.8);
}

/* 上传文字样式 */
.upload-text {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7); /* 浅灰色文字 */
  margin-bottom: 16px;
}

.upload-text em {
  color: #b388ff; /* 紫色交互文字 */
  cursor: pointer;
}

/* 上传提示样式 */
.upload-tip {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7); /* 浅灰色提示文字 */
  text-align: center;
  margin-top: 16px;
}

/* 上传进度样式 */
.upload-progress {
  background: var(--card-background);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-sm);
  padding: 24px;
  margin-bottom: 40px;
  border: 1px solid var(--border-color);
}

.upload-progress h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.progress-text {
  text-align: center;
  margin-top: 12px;
  font-size: 14px;
  color: var(--text-secondary);
}

/* 文件列表样式 */
.file-list-section {
  margin-bottom: 40px;
}

.file-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.file-list-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.file-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.file-card {
  background: var(--card-background);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-sm);
  padding: 24px;
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.file-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.file-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.file-info {
  flex: 1;
}

.file-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.file-name .file-icon {
  font-size: 20px;
}

.file-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-secondary);
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.file-status {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.status-pending {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
  border: 1px solid rgba(255, 193, 7, 0.3);
}

.status-processing {
  background: rgba(13, 202, 240, 0.2);
  color: #0dcaf0;
  border: 1px solid rgba(13, 202, 240, 0.3);
}

.status-success {
  background: rgba(25, 135, 84, 0.2);
  color: #198754;
  border: 1px solid rgba(25, 135, 84, 0.3);
}

.status-error {
  background: rgba(220, 53, 69, 0.2);
  color: #dc3545;
  border: 1px solid rgba(220, 53, 69, 0.3);
}

.file-actions {
  display: flex;
  gap: 8px;
  flex-direction: column;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--text-secondary);
  background: var(--card-background);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: var(--primary-light);
  /* 降低亮度和饱和度，适配深色背景 */
  filter: brightness(0.8) saturate(0.8);
}

.empty-state h3 {
  font-size: 18px;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.parse-status {
  background: var(--card-background);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-sm);
  padding: 24px;
  border: 1px solid var(--border-color);
}

.parse-status h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.status-text {
  text-align: center;
  margin-top: 12px;
  font-size: 14px;
  color: var(--text-secondary);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .upload-card {
    padding: 32px 20px;
  }
  
  .file-grid {
    grid-template-columns: 1fr;
  }
  
  .file-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .file-actions {
    flex-direction: row;
    align-self: flex-start;
  }
  
  .file-meta {
    gap: 8px;
  }
}
</style>