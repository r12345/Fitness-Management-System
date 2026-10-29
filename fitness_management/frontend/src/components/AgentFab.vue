<template>
  <!--
    全局悬浮球。
    挂在 AppLayout 上，所以**登录后的每个页面**都有它；位置可拖、可吸附、可记忆。
    聊天窗本身是 SDK 渲染的 fixed 浮层（无法内嵌），这个球就是它唯一的入口开关。
  -->
  <div
    class="agent-fab"
    :class="{ dragging, snapping, loading, 'on-left': side === 'left' }"
    :style="{ transform: `translate3d(${pos.x}px, ${pos.y}px, 0)` }"
  >
    <button
      ref="btnRef"
      class="agent-fab-btn"
      type="button"
      :aria-label="ariaLabel"
      :disabled="loading"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="onPointerUp"
      @pointercancel="onPointerUp"
      @click="handleClick"
      @mouseenter="handleEnter"
      @mouseleave="hovering = false"
      @focus="focused = true"
      @blur="focused = false"
    >
      <span class="agent-fab-halo" aria-hidden="true"></span>
      <span class="agent-fab-core">
        <svg v-if="!loading" viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
          <rect
            x="4"
            y="7"
            width="16"
            height="12"
            rx="4"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
          />
          <circle cx="9.5" cy="12.6" r="1.25" fill="currentColor" />
          <circle cx="14.5" cy="12.6" r="1.25" fill="currentColor" />
          <path
            d="M12 7V4.4"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
          />
          <circle cx="12" cy="3.2" r="1.25" fill="currentColor" />
        </svg>
        <span v-else class="agent-fab-spinner" aria-hidden="true"></span>
      </span>
    </button>

    <!-- 悬停 / 加载 / 报错时在球的旁侧浮出的气泡；绝对定位，不影响球的尺寸计算 -->
    <span v-if="tipVisible" class="agent-fab-tip" :class="{ error: Boolean(errorText) }">
      {{ tipText }}
    </span>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { useCozeAgent } from "../composables/useCozeAgent";

const { openAgent, preloadAgent, authMode } = useCozeAgent();

/** 球直径与贴边留白，与样式里的 .agent-fab 宽高必须一致 */
const SIZE = 56;
const MARGIN = 16;
/** 位移超过这个像素数就当成「拖动」，不再当成「点击」 */
const DRAG_THRESHOLD = 6;
const POS_KEY = "gym.agent-fab.pos";

const btnRef = ref(null);
const pos = reactive({ x: 0, y: 0 });
const side = ref("right");
const dragging = ref(false);
const snapping = ref(false);
const loading = ref(false);
const hovering = ref(false);
const focused = ref(false);
const errorText = ref("");

let snapTimer = null;
let errorTimer = null;
/** 本次按下的位移量，用来区分拖动与点击 */
const drag = { active: false, sx: 0, sy: 0, ox: 0, oy: 0, moved: 0 };

const vw = () => window.innerWidth;
const vh = () => window.innerHeight;
const maxX = () => Math.max(MARGIN, vw() - SIZE - MARGIN);
const maxY = () => Math.max(MARGIN, vh() - SIZE - MARGIN);
const clamp = (v, min, max) => Math.min(Math.max(v, min), max);
const edgeX = (s) => (s === "left" ? MARGIN : maxX());

/* ---------- 初始位置与持久化 ---------- */

/**
 * 存的是「贴哪一侧 + 纵向坐标」而不是绝对 x、y：
 * 窗口宽度变了（折叠侧栏、改窗口大小）时绝对坐标会把球甩到屏幕外，贴边坐标不会。
 */
function restorePosition() {
  let saved = null;
  try {
    saved = JSON.parse(localStorage.getItem(POS_KEY) || "null");
  } catch (err) {
    saved = null;
  }
  side.value = saved && saved.side === "left" ? "left" : "right";
  // 默认落在右下角偏上一点，避开聊天窗和页面右下角的操作区
  const fallbackY = Math.round(vh() - SIZE - 140);
  pos.x = edgeX(side.value);
  pos.y = clamp(Number.isFinite(saved?.y) ? saved.y : fallbackY, MARGIN, maxY());
}

function savePosition() {
  try {
    localStorage.setItem(POS_KEY, JSON.stringify({ side: side.value, y: Math.round(pos.y) }));
  } catch (err) {
    // 隐私模式下 localStorage 可能不可写，位置记不住而已，不影响使用
  }
}

/** 窗口尺寸变化后重新贴边，避免球被挤到视口外 */
function handleResize() {
  if (dragging.value) return;
  pos.x = edgeX(side.value);
  pos.y = clamp(pos.y, MARGIN, maxY());
}

/* ---------- 拖动 ---------- */

function onPointerDown(event) {
  // 只响应左键 / 触摸；右键留给浏览器菜单
  if (event.button !== undefined && event.button !== 0) return;
  drag.active = true;
  drag.sx = event.clientX;
  drag.sy = event.clientY;
  drag.ox = pos.x;
  drag.oy = pos.y;
  drag.moved = 0;

  dragging.value = true;
  snapping.value = false;
  window.clearTimeout(snapTimer);

  // 捕获指针：手指/鼠标滑出球体外也继续收到 move，否则拖到一半就断了
  try {
    btnRef.value?.setPointerCapture(event.pointerId);
  } catch (err) {
    // 个别浏览器不支持捕获，退化成普通拖动，不影响主流程
  }
  event.preventDefault();
}

function onPointerMove(event) {
  if (!drag.active) return;
  const dx = event.clientX - drag.sx;
  const dy = event.clientY - drag.sy;
  // 用最大值累计：来回小幅抖动不会被抵消成「没动过」
  drag.moved = Math.max(drag.moved, Math.hypot(dx, dy));
  pos.x = clamp(drag.ox + dx, MARGIN, maxX());
  pos.y = clamp(drag.oy + dy, MARGIN, maxY());
}

function onPointerUp(event) {
  if (!drag.active) return;
  drag.active = false;
  dragging.value = false;
  try {
    btnRef.value?.releasePointerCapture(event.pointerId);
  } catch (err) {
    // 忽略：捕获没建立成功时释放也会抛
  }
  // 真拖动过才吸附落位；轻点不动就原地不动
  if (drag.moved > DRAG_THRESHOLD) snapToEdge();
}

/** 松手后吸附到就近的一侧，带一段过渡动画 —— 这就是「让它动起来」的那一下 */
function snapToEdge() {
  side.value = pos.x + SIZE / 2 < vw() / 2 ? "left" : "right";
  snapping.value = true;
  pos.x = edgeX(side.value);
  pos.y = clamp(pos.y, MARGIN, maxY());
  savePosition();
  window.clearTimeout(snapTimer);
  snapTimer = window.setTimeout(() => {
    snapping.value = false;
  }, 340);
}

/* ---------- 点击 ---------- */

async function handleClick() {
  // 拖动结束浏览器仍会补发一次 click，这里按位移把它滤掉
  if (drag.moved > DRAG_THRESHOLD) {
    drag.moved = 0;
    return;
  }
  if (loading.value) return;
  loading.value = true;
  errorText.value = "";
  try {
    await openAgent();
  } catch (err) {
    errorText.value = err.message || "智能体打开失败";
    window.clearTimeout(errorTimer);
    errorTimer = window.setTimeout(() => {
      errorText.value = "";
    }, 4500);
  } finally {
    loading.value = false;
  }
}

/** 悬停即预取 13MB 的 SDK，真点下去时基本秒开 */
function handleEnter() {
  hovering.value = true;
  preloadAgent();
}

/* ---------- 展示态 ---------- */

const tipText = computed(() => {
  if (errorText.value) return errorText.value;
  if (loading.value) return "正在加载智能体…";
  // 会话隔离降级是静默发生的，把状态写进气泡里，别让人以为每个人都是独立的
  if (authMode.value === "isolated") return "AI 助手 · 独立会话 · 按住可拖动";
  if (authMode.value === "shared") return "AI 助手 · 共享会话 · 按住可拖动";
  return "AI 助手 · 按住可拖动";
});

const tipVisible = computed(() => Boolean(errorText.value) || loading.value || hovering.value || focused.value);

const ariaLabel = computed(() =>
  errorText.value ? `AI 助手：${errorText.value}` : "打开 AI 助手对话窗"
);

onMounted(() => {
  restorePosition();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  window.clearTimeout(snapTimer);
  window.clearTimeout(errorTimer);
});
</script>

<style scoped>
.agent-fab {
  position: fixed;
  left: 0;
  top: 0;
  width: 56px;
  height: 56px;
  /* 低于 SDK 聊天窗的 1200、高于页面内容：窗口打开时球被盖住，符合直觉 */
  z-index: 1150;
  will-change: transform;
}

.agent-fab.snapping {
  transition: transform 0.32s cubic-bezier(0.22, 0.61, 0.36, 1);
}

.agent-fab.dragging {
  transition: none;
}

.agent-fab-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: #fff;
  cursor: grab;
  /* 触摸拖动时不要触发页面滚动/缩放，否则手指一滑页面跟着滚 */
  touch-action: none;
  -webkit-user-select: none;
  user-select: none;
}

.agent-fab.dragging .agent-fab-btn {
  cursor: grabbing;
}

.agent-fab-halo {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: var(--primary);
  opacity: 0.35;
  animation: agent-fab-pulse 2.8s ease-out infinite;
}

.agent-fab-core {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(140deg, var(--primary), var(--primary-dark));
  /* 第一层白色描边是必需的：拖到左侧会贴在深绿色的 .sidebar（#123c3a）上，
     球本身也是深绿，没有这圈白边几乎看不出是个按钮。 */
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.92), 0 10px 24px rgba(15, 118, 110, 0.42);
  /* 待机时的轻微上下浮动，和内层脉冲叠加出「活着」的感觉 */
  animation: agent-fab-float 4.6s ease-in-out infinite;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.agent-fab-btn:hover .agent-fab-core {
  transform: scale(1.06);
  box-shadow: 0 0 0 3px #fff, 0 14px 30px rgba(15, 118, 110, 0.5);
}

.agent-fab-btn:focus-visible {
  outline: 2px solid var(--primary-dark);
  outline-offset: 4px;
  border-radius: 50%;
}

.agent-fab.dragging .agent-fab-core {
  transform: scale(1.12);
  box-shadow: 0 0 0 3px #fff, 0 18px 36px rgba(15, 118, 110, 0.55);
  /* 拖动时停掉浮动，否则位移会和手指打架 */
  animation-play-state: paused;
}

.agent-fab.dragging .agent-fab-halo {
  animation-play-state: paused;
  opacity: 0;
}

.agent-fab.loading .agent-fab-halo {
  animation-duration: 1.2s;
}

.agent-fab-spinner {
  width: 22px;
  height: 22px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: agent-fab-spin 0.8s linear infinite;
}

.agent-fab-tip {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  /* 球在右侧时气泡朝左展开，反之朝右，始终不越出视口 */
  right: calc(100% + 12px);
  white-space: nowrap;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(17, 94, 89, 0.95);
  color: #fff;
  font-size: 12px;
  line-height: 1.4;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.22);
  pointer-events: none;
  animation: agent-fab-fade 0.16s ease-out;
}

.agent-fab.on-left .agent-fab-tip {
  right: auto;
  left: calc(100% + 12px);
}

.agent-fab-tip.error {
  background: rgba(220, 38, 38, 0.96);
  white-space: normal;
  width: 210px;
  border-radius: 10px;
}

@keyframes agent-fab-float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}

@keyframes agent-fab-pulse {
  0% {
    transform: scale(1);
    opacity: 0.42;
  }
  70% {
    transform: scale(1.75);
    opacity: 0;
  }
  100% {
    transform: scale(1.75);
    opacity: 0;
  }
}

@keyframes agent-fab-spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes agent-fab-fade {
  from {
    opacity: 0;
    transform: translateY(-50%) translateX(4px);
  }
  to {
    opacity: 1;
    transform: translateY(-50%) translateX(0);
  }
}

/* 窄屏：气泡会挡住半个屏幕，且没有悬停一说，直接不要 */
@media (max-width: 860px) {
  .agent-fab-tip {
    display: none;
  }
}

/* 尊重系统的「减少动态效果」设置：关掉浮动与脉冲，只留拖拽 */
@media (prefers-reduced-motion: reduce) {
  .agent-fab-core,
  .agent-fab-halo {
    animation: none;
  }
  .agent-fab.snapping {
    transition: none;
  }
}
</style>
