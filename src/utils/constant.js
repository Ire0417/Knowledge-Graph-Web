// 接口状态码
export const API_STATUS = {
  SUCCESS: 200,
  ERROR: 500,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  NOT_FOUND: 404
}

// 实体类型
export const ENTITY_TYPES = {
  PERSON: 'PERSON',
  ORG: 'ORG',
  LOCATION: 'LOCATION',
  TIME: 'TIME',
  EVENT: 'EVENT',
  CONCEPT: 'CONCEPT',
  OBJECT: 'OBJECT'
}

// 关系类型
export const RELATION_TYPES = {
  HAS_PART: 'HAS_PART',
  PART_OF: 'PART_OF',
  IS_A: 'IS_A',
  RELATED_TO: 'RELATED_TO',
  LOCATED_IN: 'LOCATED_IN',
  OCCURRED_AT: 'OCCURRED_AT',
  CREATED_BY: 'CREATED_BY',
  USED_BY: 'USED_BY'
}

// 文件类型
export const FILE_TYPES = {
  PDF: 'application/pdf',
  WORD: 'application/msword',
  WORDX: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  EXCEL: 'application/vnd.ms-excel',
  EXCELX: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  TXT: 'text/plain',
  MARKDOWN: 'text/markdown'
}

// 允许上传的文件类型
export const ALLOWED_FILE_TYPES = [
  FILE_TYPES.PDF,
  FILE_TYPES.WORD,
  FILE_TYPES.WORDX,
  FILE_TYPES.EXCEL,
  FILE_TYPES.EXCELX,
  FILE_TYPES.TXT,
  FILE_TYPES.MARKDOWN
]

// 最大文件大小（100MB）
export const MAX_FILE_SIZE = 100 * 1024 * 1024

// 图谱布局类型
export const LAYOUT_TYPES = {
  FORCE: 'force',
  CIRCLE: 'circle',
  RADIAL: 'radial',
  TREE: 'tree'
}

// 颜色配置
export const COLORS = {
  PRIMARY: '#409eff',
  SUCCESS: '#67c23a',
  WARNING: '#e6a23c',
  DANGER: '#f56c6c',
  INFO: '#909399',
  // 实体类型颜色
  ENTITY: {
    PERSON: '#409eff',
    ORG: '#67c23a',
    LOCATION: '#e6a23c',
    TIME: '#f56c6c',
    EVENT: '#909399',
    CONCEPT: '#c0c4cc',
    OBJECT: '#d9a966'
  }
}