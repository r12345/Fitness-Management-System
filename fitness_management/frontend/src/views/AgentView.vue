<template>
  <div>
    <div v-if="toast.message" class="toast-banner" :class="toast.type">{{ toast.message }}</div>

    <div class="page-header">
      <div>
        <h1>AI 助手</h1>
        <p class="page-desc">接入扣子（Coze）智能体，在系统里直接问健身相关的问题。</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-secondary" type="button" @click="handleOpen" :disabled="loading">
          {{ opened ? "再次唤出对话" : "开始对话" }}
        </button>
      </div>
    </div>

    <div class="panel agent-hero">
      <div class="agent-avatar">健</div>
      <div class="agent-meta">
        <div class="agent-title">
          <h2>{{ agentName }}</h2>
          <span class="badge" :class="statusTone">{{ statusText }}</span>
        </div>
        <p class="agent-desc">{{ agentDesc }}</p>
        <p class="agent-id">智能体 ID：{{ agentId }} · 模型：豆包 2.0 pro</p>
      </div>
    </div>

    <div class="course-cards">
      <div v-for="item in samples" :key="item.q" class="course-card" @click="askSample(item.q)">
        <div class="course-card-top">
          <h3>{{ item.q }}</h3>
          <span class="badge info">复制并提问</span>
        </div>
        <div class="course-card-meta">
          <span>{{ item.hint }}</span>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <h2 class="panel-title">接入说明</h2>
      </div>
      <div class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <tbody>
              <tr><th>智能体</th><td>{{ agentName }}（{{ agentId }}）</td></tr>
              <tr>
                <th>接入方式</th>
                <td>扣子 Chat SDK 的 <code>CozeWebSDK.WebChatClient</code>，令牌（PAT）鉴权</td>
              </tr>
              <tr>
                <th>加载时机</th>
                <td>
                  <strong>懒加载</strong>：SDK 单文件约 13MB，首次进入本页、或鼠标移到悬浮球上预取时才注入，
                  不参与首屏加载。
                </td>
              </tr>
              <tr>
                <th>悬浮球</th>
                <td>
                  登录后的<strong>每个页面</strong>都常驻一枚可拖动的球：按住拖动、松手自动吸附到最近一侧，
                  位置记在浏览器本地，刷新后仍在原处。
                </td>
              </tr>
              <tr>
                <th>打开失败？</th>
                <td>
                  ① 确认网络能访问 <code>lf-cdn.coze.cn</code>（公司网络与广告拦截插件常拦它）；
                  ② 确认该智能体已在扣子「发布」页勾选并发布了 <strong>Chat SDK</strong>；
                  ③ 确认令牌没过期、且勾了 <code>bot</code> 相关权限。
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useToast } from "../composables/useToast";
import { useCozeAgent } from "../composables/useCozeAgent";

const toast = useToast();
const { openAgent, agentName, agentDesc, agentId } = useCozeAgent();

const loading = ref(false);
const opened = ref(false);
const failed = ref(false);

const samples = [
  { q: "新手第一次去健身房该练什么？", hint: "求一份能直接照做的入门安排" },
  { q: "练完之后肌肉酸痛正常吗？", hint: "区分正常酸痛和需要停练的信号" },
  { q: "增肌期间一天要吃多少蛋白质？", hint: "按体重算一个区间" },
  { q: "有氧和力量训练怎么排顺序？", hint: "同一天该先做哪一个" }
];

const statusText = computed(() => {
  if (loading.value) return "加载中";
  if (failed.value) return "加载失败";
  if (opened.value) return "对话已打开";
  return "待唤起";
});

const statusTone = computed(() => {
  if (loading.value) return "info";
  if (failed.value) return "danger";
  if (opened.value) return "success";
  return "muted";
});

/** 唤起对话窗。首次会先加载 SDK（约 13MB），所以按钮要置灰 */
async function handleOpen() {
  if (loading.value) return;
  loading.value = true;
  try {
    await openAgent();
    opened.value = true;
    failed.value = false;
  } catch (err) {
    failed.value = true;
    toast.show(err.message || "智能体打开失败", "error");
  } finally {
    loading.value = false;
  }
}

/**
 * 点示例问题时：唤起对话窗 + 把问题复制到剪贴板。
 * SDK 没有「代替用户发一条消息」的公开能力，所以只帮到「复制」，剩下的粘贴发送。
 */
async function askSample(question) {
  await handleOpen();
  try {
    await navigator.clipboard.writeText(question);
    toast.show("问题已复制，粘贴发送即可");
  } catch (err) {
    // 非 HTTPS 或用户拒绝授权时剪贴板不可用，不影响对话窗已经打开
    toast.show("对话窗已打开，把问题发给他就行");
  }
}

onMounted(() => {
  // 进本页即自动唤起，省掉一次点击
  handleOpen();
});
</script>

<style scoped>
.agent-hero {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 20px;
  margin-bottom: 20px;
}

.agent-avatar {
  flex: 0 0 auto;
  width: 60px;
  height: 60px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
}

.agent-meta {
  min-width: 0;
}

.agent-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.agent-title h2 {
  margin: 0;
  font-size: 20px;
}

.agent-desc {
  margin: 6px 0 0;
  color: var(--muted);
}

.agent-id {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--muted);
}

.course-card {
  cursor: pointer;
}
</style>
