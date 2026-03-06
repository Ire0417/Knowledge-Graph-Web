import { ALLOWED_FILE_TYPES, MAX_FILE_SIZE } from './constant'

// 验证文件类型
export const validateFileType = (file) => {
  if (!file) return false
  return ALLOWED_FILE_TYPES.includes(file.type)
}

// 验证文件大小
export const validateFileSize = (file) => {
  if (!file) return false
  return file.size <= MAX_FILE_SIZE
}

// 验证文件
export const validateFile = (file) => {
  if (!file) {
    return { valid: false, message: '请选择文件' }
  }
  
  if (!validateFileType(file)) {
    return { valid: false, message: '不支持的文件类型' }
  }
  
  if (!validateFileSize(file)) {
    return { valid: false, message: '文件大小不能超过100MB' }
  }
  
  return { valid: true, message: '' }
}

// 验证表单字段
export const validateField = (value, rules) => {
  if (!rules) return { valid: true, message: '' }
  
  // 必选字段
  if (rules.required && (!value || (typeof value === 'string' && value.trim() === ''))) {
    return { valid: false, message: rules.message || '此字段为必填项' }
  }
  
  // 最小长度
  if (rules.min && value && value.length < rules.min) {
    return { valid: false, message: `长度不能小于${rules.min}个字符` }
  }
  
  // 最大长度
  if (rules.max && value && value.length > rules.max) {
    return { valid: false, message: `长度不能超过${rules.max}个字符` }
  }
  
  // 正则表达式
  if (rules.pattern && value && !rules.pattern.test(value)) {
    return { valid: false, message: rules.message || '格式不正确' }
  }
  
  return { valid: true, message: '' }
}

// 验证整个表单
export const validateForm = (formData, rules) => {
  const errors = {}
  let isValid = true
  
  for (const field in rules) {
    const value = formData[field]
    const fieldRules = rules[field]
    const result = validateField(value, fieldRules)
    
    if (!result.valid) {
      errors[field] = result.message
      isValid = false
    }
  }
  
  return { isValid, errors }
}