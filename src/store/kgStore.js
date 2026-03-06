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
    hasGraphData: (state) => state.graphData.nodes.length > 0
  },
  actions: {
    setGraphData(data) {
      this.graphData = data
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