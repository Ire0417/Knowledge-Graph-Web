<template>
  <div class="qa-container">
    <div class="page-header">
      <h1 class="page-title">智能问答</h1>
      <p class="page-description">基于知识图谱的智能问答系统，支持自然语言查询</p>
      <div class="health-panel">
        <div class="health-panel-header">
          <span>问答服务状态</span>
          <button class="btn btn-sm btn-secondary" @click="refreshQaHealth" :disabled="healthLoading">
            {{ healthLoading ? '检测中...' : '刷新状态' }}
          </button>
        </div>
        <p v-if="healthMessage" :class="['health-tip', healthLevelClass]">{{ healthMessage }}</p>
        <p v-if="fileHealthTip" class="file-health-tip">{{ fileHealthTip }}</p>
        <ul v-if="healthIssues.length > 0" class="health-issues">
          <li v-for="(issue, index) in healthIssues" :key="index">{{ issue }}</li>
        </ul>
      </div>
    </div>
    
    <div class="qa-content">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">问答历史</h3>
          <button class="btn btn-sm btn-secondary" @click="clearHistory">
            清空历史
          </button>
        </div>
        <div class="card-body">
          <div v-if="qaHistory.length === 0" class="empty-history">
            <div class="empty-icon">💬</div>
            <h4>暂无问答历史</h4>
            <p>开始向系统提问吧</p>
          </div>
          <div v-else class="history-list">
            <div
              v-for="(item, index) in qaHistory"
              :key="index"
              class="history-item"
            >
              <div class="question">
                <div class="message-header">
                  <span class="message-label">你</span>
                  <span class="message-time">{{ formatTime(item.timestamp) }}</span>
                </div>
                <div class="message-content">{{ item.question }}</div>
              </div>
              <div class="answer">
                <div class="message-header">
                  <span class="message-label">系统</span>
                </div>
                <div class="message-content">{{ item.answer }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">提问</h3>
        </div>
        <div class="card-body">
          <div class="qa-input-area">
            <textarea
              v-model="question"
              :rows="4"
              placeholder="请输入您的问题..."
              class="form-control"
              @keyup.enter.exact="askQuestion"
            ></textarea>
            <div class="qa-actions">
              <button class="btn btn-primary" @click="askQuestion" :disabled="isLoading">
                <span v-if="isLoading" class="loading"></span>
                <span v-else>发送</span>
              </button>
            </div>
          </div>
          
          <div v-if="relatedQuestions.length > 0" class="related-questions">
            <h4 class="related-title">相关问题</h4>
            <div class="related-tags">
              <span
                v-for="(q, index) in relatedQuestions"
                :key="index"
                @click="useRelatedQuestion(q)"
                class="related-tag"
              >
                {{ q }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="answer" class="card">
      <div class="card-header">
        <h3 class="card-title">回答</h3>
      </div>
      <div class="card-body">
        <div class="answer-content">{{ answer }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useFileStore } from '../../store/fileStore'
import { qaApi } from '../../api/qa'
import { formatTime } from '../../utils/format'

const fileStore = useFileStore()
const question = ref('')
const answer = ref('')
const isLoading = ref(false)
const qaHistory = ref([])
const relatedQuestions = ref([])
const healthMessage = ref('')
const healthLevel = ref('info')
const qaHealth = ref(null)
const healthLoading = ref(false)

const healthLevelClass = computed(() => {
  if (healthLevel.value === 'success') return 'tip-success'
  if (healthLevel.value === 'error') return 'tip-error'
  return 'tip-info'
})

const fileHealthTip = computed(() => {
  const file = qaHealth.value?.file
  if (!file) return ''
  if (file.rag_ready) return '当前文件索引状态：已就绪，可直接提问。'
  if (file.rag_error) return `当前文件索引状态：未就绪（${file.rag_error}）。`
  return '当前文件索引状态：未就绪，请先完成解析。'
})

const healthIssues = computed(() => {
  const checks = qaHealth.value?.checks || {}
  const issueMap = {
    api_key: 'API Key',
    vector_db_path: '向量库路径',
    embedding: 'Embedding',
    llm: 'LLM'
  }
  return Object.keys(checks)
    .filter((k) => checks[k] && checks[k].ok === false)
    .map((k) => `${issueMap[k] || k}: ${checks[k].message}`)
})

const classifyQaError = (rawMessage = '') => {
  const msg = String(rawMessage || '')
  const lower = msg.toLowerCase()

  if (lower.includes('file not found')) {
    return '未找到文件，请先上传并解析文件。'
  }
  if (lower.includes('not parsed yet') || lower.includes('parse failed') || lower.includes('parse error')) {
    return '文件尚未可用于问答，请先完成解析。'
  }
  if (lower.includes('qwen_api_key') || lower.includes('api key') || lower.includes('invalid api key')) {
    return '问答配置异常：API Key 无效或未配置。'
  }
  if (lower.includes('timed out') || lower.includes('timeout') || lower.includes('connection') || lower.includes('network')) {
    return '问答服务连接超时，请稍后重试。'
  }
  if (lower.includes('rate limit') || lower.includes('quota') || lower.includes('429')) {
    return '问答服务限流或配额不足，请稍后重试。'
  }
  if (lower.includes('failed to build vector store') || lower.includes('index is not ready')) {
    return '知识索引未就绪，请重新解析文件后再试。'
  }
  return `问答失败：${msg || '未知错误'}`
}

const refreshQaHealth = async () => {
  healthLoading.value = true
  try {
    const fileId = fileStore.currentFile?.id || fileStore.uploadedFiles[0]?.id
    const response = await qaApi.checkHealth(fileId)
    const health = response.health || {}
    const fileHealth = health.file || {}
    qaHealth.value = health

    if (response.success) {
      healthLevel.value = 'success'
      healthMessage.value = fileHealth.rag_ready
        ? '问答服务状态：可用，当前文件索引已就绪。'
        : '问答服务状态：可用，请先解析文件以构建索引。'
      return
    }

    healthLevel.value = 'error'
    const checks = health.checks || {}
    if (checks.api_key && checks.api_key.ok === false) {
      healthMessage.value = `问答服务状态：不可用（API Key）- ${checks.api_key.message}`
    } else if (checks.embedding && checks.embedding.ok === false) {
      healthMessage.value = `问答服务状态：不可用（Embedding）- ${checks.embedding.message}`
    } else if (checks.llm && checks.llm.ok === false) {
      healthMessage.value = `问答服务状态：不可用（LLM）- ${checks.llm.message}`
    } else {
      healthMessage.value = '问答服务状态：不可用，请检查后端配置。'
    }
  } catch (_error) {
    healthLevel.value = 'error'
    healthMessage.value = '问答服务状态：检测失败，请确认后端服务已启动。'
    qaHealth.value = {
      checks: {
        llm: { ok: false, message: '健康检查请求失败，请确认后端服务运行正常。' }
      }
    }
  } finally {
    healthLoading.value = false
  }
}

const askQuestion = async () => {
  if (!question.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }
  
  if (fileStore.uploadedFiles.length === 0) {
    ElMessage.warning('请先上传文件')
    return
  }
  
  try {
    isLoading.value = true
    const fileId = fileStore.currentFile?.id || fileStore.uploadedFiles[0].id
    
    const response = await qaApi.askQuestion(question.value, fileId)
    if (response.success) {
      answer.value = response.answer
      
      // 添加到历史记录
      qaHistory.value.unshift({
        question: question.value,
        answer: response.answer,
        timestamp: new Date()
      })
      
      // 保存到后端
      await qaApi.saveQaResult(question.value, response.answer, fileId)
      
      // 获取相关问题
      await getRelatedQuestions(question.value, fileId)
      
      // 清空输入框
      question.value = ''
    } else {
      ElMessage.error(classifyQaError(response.message))
      await refreshQaHealth()
    }
  } catch (error) {
    const backendMessage = error?.response?.data?.message || error?.message || ''
    ElMessage.error(classifyQaError(backendMessage || '问答请求失败'))
    await refreshQaHealth()
  } finally {
    isLoading.value = false
  }
}

const getRelatedQuestions = async (question, fileId) => {
  try {
    const response = await qaApi.getRelatedQuestions(question, fileId)
    if (response.success) {
      relatedQuestions.value = response.questions
    }
  } catch (error) {
    console.error('获取相关问题失败', error)
  }
}

const useRelatedQuestion = (q) => {
  question.value = q
}

const clearHistory = async () => {
  ElMessageBox.confirm('确定要清空问答历史吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    if (fileStore.uploadedFiles.length > 0) {
      const fileId = fileStore.currentFile?.id || fileStore.uploadedFiles[0].id
      try {
        await qaApi.clearQaHistory(fileId)
        qaHistory.value = []
        ElMessage.success('问答历史已清空')
      } catch (error) {
        ElMessage.error('清空历史失败')
      }
    } else {
      qaHistory.value = []
      ElMessage.success('问答历史已清空')
    }
  }).catch(() => {
    // 取消操作
  })
}

const loadQaHistory = async () => {
  if (fileStore.uploadedFiles.length > 0) {
    const fileId = fileStore.currentFile?.id || fileStore.uploadedFiles[0].id
    try {
      const response = await qaApi.getQaHistory(fileId)
      if (response.success) {
        qaHistory.value = response.history
      }
    } catch (error) {
      console.error('加载问答历史失败', error)
    }
  }
}

onMounted(() => {
  loadQaHistory()
  refreshQaHealth()
})

watch(
  () => [fileStore.currentFile?.id, fileStore.uploadedFiles.length],
  () => {
    refreshQaHealth()
  }
)
</script>

<style scoped>
.qa-container {
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

.health-panel {
  margin: 14px auto 0;
  max-width: 900px;
  padding: 12px 14px;
  border-radius: var(--border-radius-md);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color);
}

.health-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 600;
}

.health-tip {
  margin: 10px 0 0;
  padding: 10px 14px;
  border-radius: var(--border-radius-md);
  font-size: 13px;
  border: 1px solid transparent;
}

.file-health-tip {
  margin-top: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

.health-issues {
  margin-top: 8px;
  padding-left: 18px;
  color: #ffb3bf;
  font-size: 12px;
  line-height: 1.5;
}

.tip-success {
  background: rgba(25, 135, 84, 0.2);
  color: #9be7c4;
  border-color: rgba(25, 135, 84, 0.4);
}

.tip-info {
  background: rgba(13, 110, 253, 0.18);
  color: #9bc7ff;
  border-color: rgba(13, 110, 253, 0.38);
}

.tip-error {
  background: rgba(220, 53, 69, 0.2);
  color: #ffb3bf;
  border-color: rgba(220, 53, 69, 0.4);
}

.qa-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.card {
  background: var(--card-background);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-md);
  padding: 24px;
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

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.empty-history {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: var(--primary-light);
}

.empty-history h4 {
  font-size: 18px;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.history-list {
  max-height: 500px;
  overflow-y: auto;
}

.history-item {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border-color);
}

.history-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.question {
  margin-bottom: 16px;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.message-label {
  font-weight: 600;
  color: var(--primary-light);
  font-size: 14px;
}

.message-time {
  font-size: 12px;
  color: var(--text-secondary);
}

.message-content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: var(--border-radius-md);
  border: 1px solid var(--border-color);
}

.answer .message-content {
  background: rgba(123, 44, 191, 0.1);
  border-color: var(--primary-color);
}

.qa-input-area {
  margin-bottom: 24px;
}

.form-control {
  width: 100%;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-md);
  font-size: 14px;
  color: var(--text-primary);
  resize: none;
  transition: all 0.3s ease;
  font-family: inherit;
}

.form-control:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(123, 44, 191, 0.2);
}

.qa-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.loading {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-color);
  border-radius: 50%;
  border-top-color: var(--primary-color);
  animation: spin 1s ease-in-out infinite;
  margin-right: 8px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.related-questions {
  margin-top: 24px;
}

.related-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.related-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.related-tag {
  display: inline-block;
  padding: 6px 12px;
  background: rgba(123, 44, 191, 0.2);
  border: 1px solid var(--primary-color);
  border-radius: 16px;
  font-size: 12px;
  color: var(--primary-light);
  cursor: pointer;
  transition: all 0.3s ease;
}

.related-tag:hover {
  background: var(--primary-color);
  color: var(--text-primary);
  transform: translateY(-2px);
}

.answer-content {
  font-size: 16px;
  line-height: 1.6;
  color: var(--text-primary);
  padding: 20px;
  background: rgba(123, 44, 191, 0.1);
  border-radius: var(--border-radius-md);
  border: 1px solid var(--primary-color);
}

@media (max-width: 768px) {
  .qa-content {
    grid-template-columns: 1fr;
  }
  
  .card {
    padding: 20px;
  }
  
  .history-list {
    max-height: 400px;
  }
}
</style>