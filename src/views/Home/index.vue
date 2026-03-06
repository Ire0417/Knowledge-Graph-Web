<template>
  <div class="home-container">
    <!-- 英雄区域 -->
    <div class="hero">
      <div class="hero-bg-glow"></div>
      <div class="hero-container">
        <div class="hero-content">
          <div class="hero-badge glass-panel">智能知识图谱系统 v2.0</div>
          <h1 class="hero-title">构建您的<br><span class="text-gradient">知识宇宙</span></h1>
          <p class="hero-description">
            基于多模态数据的智能知识图谱构建与可视化平台。
            <br>从文件到知识的全流程解决方案，让数据触手可及。
          </p>
          <div class="hero-buttons">
            <router-link to="/upload" class="btn btn-primary">
              <span>开始上传</span>
            </router-link>
            <router-link to="/kg-visual" class="btn btn-secondary">
              <span>查看演示</span>
            </router-link>
          </div>
        </div>
        
        <!-- 装饰性 3D 元素 -->
        <div class="hero-visual">
          <div class="floating-card glass-panel card-1">
            <div class="card-icon">📄</div>
            <div class="card-line"></div>
            <div class="card-line short"></div>
          </div>
          <div class="floating-card glass-panel card-2">
            <div class="card-icon">🕸️</div>
            <div class="card-graph">
              <div class="node n1"></div>
              <div class="node n2"></div>
              <div class="node n3"></div>
              <div class="link l1"></div>
              <div class="link l2"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 特性区域 -->
    <div class="features">
      <div class="features-container">
        <h2 class="section-title">核心功能</h2>
        <p class="section-subtitle">探索 AI 驱动的知识图谱构建能力</p>
        
        <div class="features-grid">
          <div 
            v-for="(feature, index) in features" 
            :key="index"
            class="feature-card glass-panel"
            :class="{ 'active': activeFeature === index }"
            @click="activateFeature(index)"
          >
            <div class="feature-content">
              <h3 class="feature-title">{{ feature.title }}</h3>
              <p class="feature-description">{{ feature.desc }}</p>
            </div>
            
            <!-- 展开后的额外内容 -->
            <div class="feature-details" v-if="activeFeature === index">
              <div class="detail-line"></div>
              <p>点击进入功能详情页面，体验更深度的 {{ feature.title }} 服务。</p>
              <button class="btn btn-sm btn-primary">立即体验</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 沉浸式展开遮罩 (可选，如果想要全屏体验) -->
    <transition name="modal">
      <div class="feature-modal" v-if="activeFeature !== null" @click.self="activeFeature = null">
        <div class="modal-content glass-panel">
          <button class="close-btn" @click="activeFeature = null">×</button>
          <h2>{{ features[activeFeature].title }}</h2>
          <p class="modal-desc">{{ features[activeFeature].desc }}</p>
          <div class="modal-body">
            <p>这里展示关于 {{ features[activeFeature].title }} 的更多详细信息。在这个沉浸式视图中，您可以专注于当前的功能模块。</p>
            <div class="modal-visual">
              <!-- 模拟功能预览图 -->
              <div class="skeleton-box"></div>
              <div class="skeleton-lines">
                <div class="line"></div>
                <div class="line"></div>
                <div class="line"></div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-primary">进入功能</button>
          </div>
        </div>
      </div>
    </transition>

  </div>
</template>

<script setup>
import { ref } from 'vue'

const activeFeature = ref(null)

const features = [
  { title: '多模态数据处理', desc: '支持PDF、Word、Excel等多种文件格式，自动解析文本、表格和图片内容' },
  { title: '智能知识抽取', desc: '基于学术领域NER模型，自动识别实体和关系，提取结构化知识' },
  { title: '图谱构建与优化', desc: '支持实体对齐、关系合并和图谱结构优化，构建高质量知识网络' },
  { title: '交互式可视化', desc: '力导向图布局，支持节点拖拽、缩放、折叠和路径查询' },
  { title: '智能问答', desc: '基于知识图谱的自然语言问答，支持上下文理解和多轮对话' },
  { title: '数据导出', desc: '支持多种格式导出，包括JSON、CSV和图形文件' }
]

const activateFeature = (index) => {
  activeFeature.value = index
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  color: #fff;
}

/* 文本渐变通用类 */
.text-gradient {
  background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 英雄区域 */
.hero {
  padding: 120px 0 80px;
  position: relative;
  /* overflow: hidden; 不隐藏溢出，为了光晕效果 */
}

.hero-bg-glow {
  position: absolute;
  top: -20%;
  left: 50%;
  transform: translateX(-50%);
  width: 80%;
  height: 80%;
  background: radial-gradient(circle, rgba(123, 44, 191, 0.4) 0%, transparent 70%);
  filter: blur(60px);
  z-index: -1;
  pointer-events: none;
}

.hero-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.hero-content {
  max-width: 600px;
  z-index: 2;
}

.hero-badge {
  display: inline-block;
  padding: 8px 16px;
  font-size: 14px;
  color: #d8b4fe;
  border-radius: 50px;
  margin-bottom: 24px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.hero-title {
  font-size: 64px;
  font-weight: 800;
  line-height: 1.1;
  margin-bottom: 24px;
  letter-spacing: -2px;
}

.hero-description {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 40px;
  line-height: 1.6;
}

.hero-buttons {
  display: flex;
  gap: 20px;
}

/* 装饰元素 */
.hero-visual {
  position: relative;
  width: 400px;
  height: 400px;
  display: none; /* 移动端隐藏 */
}

@media (min-width: 992px) {
  .hero-visual {
    display: block;
  }
}

.floating-card {
  position: absolute;
  padding: 20px;
  border-radius: 20px;
  animation: float 6s ease-in-out infinite;
}

.card-1 {
  width: 200px;
  height: 280px;
  top: 0;
  right: 40px;
  z-index: 1;
  transform: rotate(-10deg);
  animation-delay: 0s;
}

.card-2 {
  width: 240px;
  height: 160px;
  bottom: 40px;
  left: 0;
  z-index: 2;
  transform: rotate(5deg);
  animation-delay: 3s;
}

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(var(--rot, 0deg)); }
  50% { transform: translateY(-20px) rotate(var(--rot, 0deg)); }
}

.card-icon { font-size: 40px; margin-bottom: 10px; }
.card-line { height: 10px; background: rgba(255,255,255,0.1); border-radius: 5px; margin-bottom: 8px; }
.card-line.short { width: 60%; }

/* 特性与卡片 */
.features {
  padding: 80px 0;
}

.features-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.section-title {
  font-size: 40px;
  text-align: center;
  margin-bottom: 10px;
  font-weight: 700;
}

.section-subtitle {
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 60px;
  font-size: 18px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px;
}

.feature-card {
  padding: 40px 30px;
  border-radius: 24px;
  transition: all 0.4s var(--spring-easing);
  cursor: pointer;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-height: 240px;
}

.feature-card:hover {
  transform: translateY(-10px) scale(1.02);
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
}

.feature-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 16px;
}

.feature-description {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.6;
}

/* Modal 沉浸式展开 */
.feature-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(10px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.modal-content {
  width: 100%;
  max-width: 800px;
  padding: 60px;
  position: relative;
  background: rgba(30, 30, 40, 0.6); /*稍微深一点以突出*/
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  transform-origin: center;
}

.close-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  background: none;
  border: none;
  color: white;
  font-size: 32px;
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.close-btn:hover { opacity: 1; }
.modal-content h2 { font-size: 36px; margin-bottom: 16px; }
.modal-desc { font-size: 20px; color: rgba(255, 255, 255, 0.8); margin-bottom: 40px; }
.modal-body { display: flex; flex-direction: column; gap: 20px; }
.modal-visual {
  height: 200px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

/* Skeleton loader for visual */
.skeleton-box { width: 100px; height: 100px; background: rgba(255,255,255,0.1); border-radius: 8px; float: left; margin-right: 20px; }
.skeleton-lines .line { height: 12px; background: rgba(255,255,255,0.1); border-radius: 6px; margin-bottom: 12px; }
.skeleton-lines .line:last-child { width: 60%; }

/* Modal 动画 */
.modal-enter-active, .modal-leave-active {
  transition: opacity 0.3s ease;
}
.modal-enter-from, .modal-leave-to {
  opacity: 0;
}
.modal-enter-active .modal-content {
  animation: modal-pop 0.4s var(--spring-easing) forwards;
}
@keyframes modal-pop {
  0% { transform: scale(0.9); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}
</style>