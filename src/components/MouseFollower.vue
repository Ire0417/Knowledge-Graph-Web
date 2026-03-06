<template>
  <div class="custom-cursor-container">
    <div class="cursor-dot" ref="dot"></div>
    <div class="cursor-ring" ref="ring"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const dot = ref(null)
const ring = ref(null)

// 鼠标位置
const mouseX = ref(0)
const mouseY = ref(0)

// 环形位置（带延迟）
const ringX = ref(0)
const ringY = ref(0)

// 交互状态
const isHovering = ref(false)
const isClicking = ref(false)

let animationFrameId = null

const onMouseMove = (e) => {
  mouseX.value = e.clientX
  mouseY.value = e.clientY
  
  // 检查鼠标下的元素是否可交互
  const target = e.target
  if (target) {
    const clickable = target.closest('a, button, input, textarea, .btn, .clickable, .glass-card, .menu-item')
    isHovering.value = !!clickable
  }
}

const onMouseDown = () => {
  isClicking.value = true
}

const onMouseUp = () => {
  isClicking.value = false
}

const animate = () => {
  // 设置点的直接位置
  if (dot.value) {
    dot.value.style.transform = `translate3d(${mouseX.value}px, ${mouseY.value}px, 0)`
  }
  
  // 设置圆环的延迟跟随（弹簧阻尼效果）
  const strength = 0.15
  ringX.value += (mouseX.value - ringX.value) * strength
  ringY.value += (mouseY.value - ringY.value) * strength
  
  if (ring.value) {
    const scale = isClicking.value ? 0.8 : (isHovering.value ? 1.5 : 1)
    const opacity = isHovering.value ? 0.3 : 0.6
    
    // 使用 translate3d 开启硬件加速
    ring.value.style.transform = `translate3d(${ringX.value}px, ${ringY.value}px, 0) scale(${scale})`
    ring.value.style.opacity = opacity
    ring.value.style.borderColor = isHovering.value ? 'rgba(255, 215, 0, 0.8)' : 'rgba(255, 255, 255, 0.5)'
    ring.value.style.backgroundColor = isHovering.value ? 'rgba(255, 215, 0, 0.1)' : 'transparent'
  }
  
  animationFrameId = requestAnimationFrame(animate)
}

onMounted(() => {
  // 隐藏默认鼠标
  // 注意：在某些情况下完全隐藏鼠标可能会影响用户体验，这里已经在 style.css 设置了 body cursor: none
  
  // 初始化位置
  mouseX.value = window.innerWidth / 2
  mouseY.value = window.innerHeight / 2
  ringX.value = mouseX.value
  ringY.value = mouseY.value
  
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mousedown', onMouseDown)
  window.addEventListener('mouseup', onMouseUp)
  
  // 启动动画循环
  animate()
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mousedown', onMouseDown)
  window.removeEventListener('mouseup', onMouseUp)
  
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
  }
})
</script>

<style scoped>
.custom-cursor-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  pointer-events: none;
  z-index: 9999;
}

.cursor-dot {
  position: fixed;
  top: 0;
  left: 0;
  width: 8px;
  height: 8px;
  margin-top: -4px;
  margin-left: -4px;
  background-color: white;
  border-radius: 50%;
  pointer-events: none;
  z-index: 10001;
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
}

.cursor-ring {
  position: fixed;
  top: 0;
  left: 0;
  width: 40px;
  height: 40px;
  margin-top: -20px;
  margin-left: -20px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 50%;
  pointer-events: none; 
  /* 关键点：使用 transition 实现除位置外的其他属性平滑过渡，位置更新由 JS 控制 */
  transition: width 0.3s, height 0.3s, background-color 0.3s, border-color 0.3s, opacity 0.3s, transform 0.1s linear;
  z-index: 10000;
  will-change: transform;
}
</style>
