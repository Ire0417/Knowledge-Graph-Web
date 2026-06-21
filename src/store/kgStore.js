import { defineStore } from 'pinia'

export const useKgStore = defineStore('kg', {
  state: () => ({
    graphData: {
      nodes: [],
      links: []
    },
    buildProgress: 0,
    buildStatus: '',
    selectedNode: null,
    expandedNodes: [],
    searchKeyword: ''
  }),
  getters: {
    hasGraphData: (state) => {
      // 安全检查
      if (!state.graphData) return false
      if (!state.graphData.nodes) return false
      return state.graphData.nodes.length > 0
    }
  },
  actions: {
    setGraphData(data) {
      // 确保数据结构安全
      this.graphData = {
        nodes: (data && data.nodes) || [],
        links: (data && data.links) || []
      }
    },
    setBuildProgress(progress) {
      this.buildProgress = progress
    },
    setBuildStatus(status) {
      this.buildStatus = status
    },
    selectNode(node) {
      this.selectedNode = node
    },
    toggleNodeExpansion(nodeId) {
      const index = this.expandedNodes.indexOf(nodeId)
      if (index > -1) {
        this.expandedNodes.splice(index, 1)
      } else {
        this.expandedNodes.push(nodeId)
      }
    },
    setSearchKeyword(keyword) {
      this.searchKeyword = keyword
    },
    clearGraph() {
      this.graphData = { nodes: [], links: [] }
      this.buildProgress = 0
      this.buildStatus = ''
      this.selectedNode = null
      this.expandedNodes = []
      this.searchKeyword = ''
    }
  }
})