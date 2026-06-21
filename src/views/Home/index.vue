<template>
  <div class="app-container stagingIndex">
    <el-row :gutter="16">
      <el-col :xs="24" :sm="24" :md="18" :lg="18" class="home-gutter">
        <div class="userInfo module-1">
          <div class="info-main">
            <div class="avatar-placeholder">
              <span class="avatar-icon"></span>
            </div>
            <div class="info-con">
              <div class="info-con-name">
                上午好，{{ userStore.user?.nickname || userStore.user?.username || '用户' }}，祝您开心每一天！
              </div>
              <div class="info-con-desc">
                <span class="role-tag">系统管理员</span>
                <span class="desc-text">{{ xljtcont }}</span>
              </div>
            </div>
            <div class="info-btns">
              <el-button type="primary" size="default" @click="goprofile">
                个人中心
              </el-button>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="24" :md="6" :lg="6" class="home-gutter">
        <div class="module-2">
          <div class="weather-card">
            <div class="weather-icon"></div>
            <div class="weather-temp">23°C</div>
            <div class="weather-desc">晴朗</div>
            <div class="weather-city">北京</div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="24" :md="18" :lg="18" class="home-gutter">
        <div class="module-3">
          <div
            class="module-item"
            v-for="(item, index) in module1"
            :key="index"
          >
            <div class="module-item-t">
              <div class="module-item-t-l">
                <div class="name">{{ item.name }}</div>
                <span class="value">{{ item.value }}</span>
              </div>
              <div class="module-item-t-r"></div>
            </div>

            <div class="module-item-data">
              <span class="label">周同比：</span>
              <span :class="['trend', item.up ? 'trend-up' : 'trend-down']">
                {{ item.up ? '+' : '' }}{{ item.speed }}%
              </span>
            </div>
          </div>
        </div>

        <el-row :gutter="16">
          <el-col :xs="24" :sm="24" :md="12" :lg="12">
            <div class="module-4 border-item">
              <div class="border-item-head">
                <span class="head-title">文件类型统计</span>
              </div>
              <div class="border-item-body">
                <div class="chart-container" ref="module4ChartRef"></div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="24" :md="12" :lg="12">
            <div class="module-5 border-item">
              <div class="border-item-head">
                <span class="head-title">近7日抽取数量统计</span>
              </div>
              <div class="border-item-body">
                <div class="chart-container" ref="module5ChartRef"></div>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-col>

      <el-col :xs="24" :sm="24" :md="6" :lg="6" class="home-gutter">
        <div class="border-item module-6 home-gutter">
          <div class="border-item-head">
            <span class="head-title">新闻公告</span>
            <el-link type="primary" :underline="false" @click="goxinwen">
              查看更多
            </el-link>
          </div>
          <div class="border-item-body">
            <div
              class="news-item"
              v-for="(item, index) in module6"
              :key="index"
              @click="goxinwen"
            >
              <el-tag :type="item.type" size="small" effect="light">{{ item.title }}</el-tag>
              <div class="news-text">{{ item.value }}</div>
              <div class="news-time">{{ item.date }}</div>
            </div>
          </div>
        </div>
        <div class="border-item module-7">
          <div class="border-item-head">
            <span class="head-title">快捷功能入口</span>
          </div>
          <div class="border-item-body">
            <div class="all-entrance">
              <div
                class="entrance-item"
                v-for="item in entranceList"
                :key="item.name"
                @click="routeTo(item.path, item.query)"
              >
                <div class="name">{{ item.name }}</div>
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="24" :md="9" :lg="9">
        <div class="module-8 border-item">
          <div class="border-item-head">
            <span class="head-title">近半年实体新增趋势</span>
            <el-link type="primary" :underline="false">查看更多</el-link>
          </div>
          <div class="border-item-body">
            <div class="chart-container" ref="module8ChartRef"></div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="24" :md="15" :lg="15">
        <div class="module-9 border-item">
          <div class="border-item-head">
            <span class="head-title">抽取任务</span>
            <el-link type="primary" :underline="false">查看更多</el-link>
          </div>
          <div class="border-item-body">
            <el-table :data="module9" style="width: 100%" size="default">
              <el-table-column
                fixed
                prop="id"
                label="ID"
                align="center"
                width="80"
              >
                <template #default="scope">
                  <span class="table-id">{{ scope.row.id }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="name" label="任务名称" min-width="200" />
              <el-table-column prop="status" align="center" label="任务状态" width="100">
                <template #default="scope">
                  <el-tag :type="getStatusType(scope.row.status)" size="small">
                    {{ scope.row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column
                prop="publishStatus"
                align="center"
                label="发布状态"
                width="100"
              >
                <template #default="scope">
                  <el-tag :type="scope.row.publishStatus === '已发布' ? 'success' : 'info'" size="small">
                    {{ scope.row.publishStatus }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="publishBy" align="center" label="发布人" width="100" />
              <el-table-column prop="createTime" label="创建时间" width="180" />
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="Index">
import { useRouter } from 'vue-router';
import { onBeforeUnmount, onMounted, ref } from "vue";
import * as echarts from "echarts";
import { useUserStore } from '../../store/userStore';

const router = useRouter();
const userStore = useUserStore();

const entranceList = [
  {
    name: "文件管理",
    path: "/upload",
    query: {},
  },
  {
    name: "知识问答",
    path: "/qa",
    query: {},
  },
  {
    name: "图谱构建",
    path: "/kg-build",
    query: {},
  },
  {
    name: "图谱可视化",
    path: "/kg-visual",
    query: {},
  },
];

const chartInstances = [];

const module1 = ref([
  {
    name: "实体总数",
    value: 126,
    up: true,
    speed: 12,
  },
  {
    name: "关系总数",
    value: 72,
    up: true,
    speed: 2,
  },
  {
    name: "三元组总数",
    value: 164,
    up: true,
    speed: 9,
  },
  {
    name: "文件总数",
    value: 76,
    up: true,
    speed: 10,
  },
  {
    name: "抽取任务总数",
    value: 18,
    up: false,
    speed: 10,
  },
]);

const goxinwen = () => {
  console.log("查看新闻公告");
};

const goprofile = () => {
  router.push("/profile");
};

const routeTo = (link, query = {}) => {
  if (link) {
    router.push({ path: link, query });
  }
};

const xljtcont = ref("");
const getxljtcont = () => {
  const xljtlist = [
    { value: "起风的日子，学会依风起舞，下雨的时候，学会为自己撑伞。" },
    { value: "别让鸡零狗碎的破事，耗尽你对美好生活的所有向往。" },
    { value: "管好身体，照顾好家人，要自己感受生活的美好。" },
    { value: "我希望你过普通的生活，有稳定的收入和爱你的人。" },
    { value: "一定要努力赚钱，好好经营自己。" },
    { value: "我们穷极一生追求的幸福，眼中景，盘中餐，身边人。" },
    { value: "日出有盼，日落有思，平平安安，所遇皆甜。" },
    { value: "不要慌，太阳下山有月光。" },
    { value: "几经波折见风雪，再见是我也非我。" },
  ];
  const num = Math.floor(Math.random() * xljtlist.length);
  xljtcont.value = xljtlist[num].value;
};

const module4ChartRef = ref(null);
const initModule4 = () => {
  const instance = echarts.init(module4ChartRef.value);
  const data = [
    { value: 130, name: "基础理论" },
    { value: 150, name: "智能技术" },
    { value: 100, name: "行业应用" },
    { value: 190, name: "未来趋势" },
    { value: 200, name: "其他" },
  ];

  const option = {
    tooltip: {
      trigger: "item",
      formatter: "{b}: {c} ({d}%)",
    },
    legend: {
      orient: "vertical",
      right: 10,
      top: "center",
      textStyle: {
        color: "#606266",
        fontSize: 12,
      },
    },
    series: [
      {
        name: "文件类型",
        type: "pie",
        radius: ["40%", "60%"],
        center: ["35%", "50%"],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 4,
          borderColor: "#fff",
          borderWidth: 2,
        },
        label: {
          show: false,
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: "bold",
          },
        },
        data: data,
        color: ["#7fb3e0", "#a5d0a7", "#e8c88a", "#b8a5d3", "#e0a5bd"],
      },
    ],
  };
  instance.setOption(option);
  chartInstances.push(instance);
};

const module5ChartRef = ref(null);
const initModule5 = () => {
  const instance = echarts.init(module5ChartRef.value);
  instance.setOption({
    grid: {
      top: 40,
      bottom: 30,
      right: 20,
      left: 50,
    },
    xAxis: {
      type: "category",
      data: ["05-01", "05-02", "05-03", "05-04", "05-05", "05-06", "05-07"],
      axisLine: { lineStyle: { color: "#e4e7ed" } },
      axisLabel: { color: "#909399" },
    },
    yAxis: {
      type: "value",
      max: 1000,
      splitLine: { lineStyle: { color: "#f5f7fa" } },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#909399" },
    },
    series: [
      {
        type: "bar",
        name: "抽取实体数量",
        barWidth: 30,
        itemStyle: {
          color: "#1890ff",
          borderRadius: [4, 4, 0, 0],
        },
        data: [800, 550, 740, 450, 800, 730, 600],
      },
    ],
  });
  chartInstances.push(instance);
};

const module6 = ref([
  {
    date: "2025-05-20",
    title: "置顶",
    value: "知识图谱系统 v2.0 发布",
    type: "danger",
  },
  {
    date: "2025-05-18",
    title: "新闻",
    value: "新增智能问答功能",
    type: "success",
  },
  {
    date: "2025-05-15",
    title: "公告",
    value: "系统升级维护通知",
    type: "primary",
  },
  {
    date: "2025-05-10",
    title: "其他",
    value: "文档更新完成",
    type: "info",
  },
  {
    date: "2025-05-05",
    title: "新闻",
    value: "新功能上线预告",
    type: "warning",
  },
]);

const module8ChartRef = ref(null);
const initModule8 = () => {
  const instance = echarts.init(module8ChartRef.value);
  instance.setOption({
    grid: {
      top: 40,
      bottom: 30,
      right: 20,
      left: 50,
    },
    xAxis: {
      type: "category",
      data: ["12月", "1月", "2月", "3月", "4月", "5月"],
      axisLine: { lineStyle: { color: "#e4e7ed" } },
      axisLabel: { color: "#909399" },
    },
    yAxis: {
      type: "value",
      splitLine: { lineStyle: { color: "#f5f7fa" } },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#909399" },
    },
    series: [
      {
        type: "line",
        name: "实体新增趋势",
        smooth: true,
        symbol: "circle",
        symbolSize: 6,
        lineStyle: {
          color: "#1890ff",
          width: 2,
        },
        itemStyle: {
          color: "#1890ff",
        },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(24, 144, 255, 0.3)" },
              { offset: 1, color: "rgba(24, 144, 255, 0.05)" },
            ],
          },
        },
        data: [120, 132, 101, 134, 90, 230],
      },
    ],
  });
  chartInstances.push(instance);
};

const module9 = ref([
  {
    id: "1",
    name: "论文数据集抽取任务",
    status: "进行中",
    publishStatus: "已发布",
    publishBy: "管理员",
    createTime: "2025-05-20 10:30:00",
  },
  {
    id: "2",
    name: "知识库构建任务",
    status: "已完成",
    publishStatus: "已发布",
    publishBy: "管理员",
    createTime: "2025-05-18 14:20:00",
  },
  {
    id: "3",
    name: "新闻资讯抽取",
    status: "等待中",
    publishStatus: "草稿",
    publishBy: "用户",
    createTime: "2025-05-15 09:15:00",
  },
  {
    id: "4",
    name: "产品文档分析",
    status: "已完成",
    publishStatus: "已发布",
    publishBy: "管理员",
    createTime: "2025-05-12 16:45:00",
  },
]);

const getStatusType = (status) => {
  const map = {
    "进行中": "primary",
    "已完成": "success",
    "等待中": "warning",
    "失败": "danger",
  };
  return map[status] || "info";
};

onMounted(() => {
  getxljtcont();
  setTimeout(() => {
    initModule4();
    initModule5();
    initModule8();
  }, 100);

  const handleResize = () => {
    chartInstances.forEach(chart => {
      chart.resize();
    });
  };
  window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
  chartInstances.forEach(chart => {
    chart.dispose();
  });
});
</script>

<style scoped>
.app-container {
  padding: 16px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.stagingIndex {
  padding-bottom: 20px;
}

.home-gutter {
  margin-bottom: 16px;
}

/* 用户信息模块 */
.module-1 {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #ebeef5;
}

.info-main {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar-placeholder {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-icon {
  font-size: 28px;
  background: #fff;
}

.info-con {
  flex: 1;
}

.info-con-name {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.info-con-desc {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.role-tag {
  display: inline-block;
  padding: 2px 12px;
  background: #e6f7ff;
  color: #1890ff;
  border-radius: 4px;
  font-size: 13px;
}

.desc-text {
  color: #909399;
  font-size: 13px;
}

/* 天气模块 */
.module-2 {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #ebeef5;
  height: 100%;
}

.weather-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.weather-icon {
  font-size: 40px;
  margin-bottom: 8px;
  background: #fff;
}

.weather-temp {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.weather-desc {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
}

.weather-city {
  font-size: 12px;
  color: #909399;
}

/* 统计模块 */
.module-3 {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.module-3 .module-item {
  flex: 1;
  min-width: 160px;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #ebeef5;
}

.module-item-t {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.module-item-t-l {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.module-item-t-l .name {
  font-size: 13px;
  color: #909399;
}

.module-item-t-l .value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.module-item-t-r {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.item-icon {
  font-size: 22px;
  background: #fff;
}

.module-item-data {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.module-item-data .label {
  color: #909399;
}

.trend {
  font-weight: 500;
}

.trend-up {
  color: #52c41a;
}

.trend-down {
  color: #f5222d;
}

/* 通用卡片 */
.border-item {
  background: #fff;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  margin-bottom: 16px;
}

.border-item-head {
  padding: 14px 16px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.head-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.border-item-body {
  padding: 16px;
}

.chart-container {
  width: 100%;
  height: 220px;
}

/* 新闻公告 */
.module-6 .news-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #f5f7fa;
  cursor: pointer;
  transition: background 0.2s;
}

.module-6 .news-item:hover {
  background: #fafafa;
  margin: 0 -8px;
  padding: 10px 8px;
  border-radius: 4px;
}

.module-6 .news-item:last-child {
  border-bottom: none;
}

.module-6 .news-text {
  flex: 1;
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.module-6 .news-time {
  font-size: 12px;
  color: #c0c4cc;
  flex-shrink: 0;
}

/* 快捷入口 */
.all-entrance {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.entrance-item {
  width: calc(50% - 6px);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafafa;
  border: 1px solid transparent;
}

.entrance-item:hover {
  background: #f0f7ff;
  border-color: #1890ff;
}

.entrance-item .entrance-icon {
  font-size: 28px;
  margin-bottom: 8px;
  background: #fff;
}

.entrance-item .name {
  font-size: 13px;
  color: #303133;
  text-align: center;
}

/* 表格样式 */
.table-id {
  font-family: 'Courier New', monospace;
  color: #606266;
  font-size: 13px;
}

/* 响应式 */
@media (max-width: 1200px) {
  .module-3 .module-item {
    min-width: 140px;
  }
}

@media (max-width: 768px) {
  .app-container {
    padding: 12px;
  }

  .info-main {
    flex-direction: column;
    text-align: center;
  }

  .info-con-desc {
    justify-content: center;
  }

  .module-3 {
    flex-direction: column;
  }

  .module-3 .module-item {
    min-width: 100%;
  }

  .entrance-item {
    width: calc(50% - 6px);
  }
}
</style>