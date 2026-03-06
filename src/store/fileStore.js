import { defineStore } from 'pinia'

export const useFileStore = defineStore('file', {
  state: () => ({
    uploadedFiles: [],
    currentFile: null,
    uploadProgress: 0,
    parseStatus: '',
    parseProgress: 0
  }),
  getters: {
    hasUploadedFiles: (state) => state.uploadedFiles.length > 0
  },
  actions: {
    addFile(file) {
      this.uploadedFiles.push(file)
      this.currentFile = file
    },
    removeFile(fileId) {
      this.uploadedFiles = this.uploadedFiles.filter(file => file.id !== fileId)
      if (this.currentFile && this.currentFile.id === fileId) {
        this.currentFile = this.uploadedFiles.length > 0 ? this.uploadedFiles[0] : null
      }
    },
    setUploadProgress(progress) {
      this.uploadProgress = progress
    },
    setParseStatus(status) {
      this.parseStatus = status
    },
    setParseProgress(progress) {
      this.parseProgress = progress
    },
    clearFiles() {
      this.uploadedFiles = []
      this.currentFile = null
      this.uploadProgress = 0
      this.parseStatus = ''
      this.parseProgress = 0
    }
  }
})