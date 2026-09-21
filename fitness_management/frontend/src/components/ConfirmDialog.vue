<template>
  <Teleport to="body">
    <Transition name="confirm">
      <div v-if="state.visible" class="confirm-mask" @click.self="onCancel" @keydown.esc="onCancel">
        <div
          class="confirm-card"
          :class="`tone-${state.tone}`"
          role="alertdialog"
          aria-modal="true"
          :aria-label="state.title"
        >
          <div class="confirm-head">
            <span class="confirm-icon" aria-hidden="true">
              <!-- 危险操作给警示三角，普通操作给问号圆，色跟随 tone -->
              <svg v-if="state.tone === 'danger'" viewBox="0 0 24 24" width="22" height="22"
                   fill="none" stroke="currentColor" stroke-width="2"
                   stroke-linecap="round" stroke-linejoin="round">
                <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
              <svg v-else viewBox="0 0 24 24" width="22" height="22"
                   fill="none" stroke="currentColor" stroke-width="2"
                   stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10" />
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </span>
            <h3 class="confirm-title">{{ state.title }}</h3>
          </div>

          <p v-if="state.message" class="confirm-message">{{ state.message }}</p>

          <dl v-if="state.details.length" class="confirm-details">
            <div v-for="(item, index) in state.details" :key="index" class="confirm-row">
              <dt>{{ item.label }}</dt>
              <dd>{{ item.value }}</dd>
            </div>
          </dl>

          <div class="confirm-foot">
            <button ref="cancelRef" type="button" class="btn btn-secondary" @click="onCancel">
              {{ state.cancelText }}
            </button>
            <button
              ref="confirmRef"
              type="button"
              class="btn"
              :class="state.tone === 'danger' ? 'btn-danger' : 'btn-primary'"
              @click="onConfirm"
            >
              {{ state.confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
// 全局确认弹窗：只读 useConfirm.js 里的单例状态，按钮把结果回填给那边。
// 不用浏览器原生 confirm，是为了样式统一、能放多行关键信息（课程/时间/地点）。
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { settleConfirm, useConfirmState } from "../composables/useConfirm.js";

const state = useConfirmState();
const confirmRef = ref(null);
const cancelRef = ref(null);

function onConfirm() {
  settleConfirm(true);
}

function onCancel() {
  settleConfirm(false);
}

function onKeydown(event) {
  if (!state.visible) return;
  if (event.key === "Escape") {
    event.preventDefault();
    onCancel();
  } else if (event.key === "Enter") {
    // 回车默认落在「取消」上（浏览器对按钮的默认行为），这里按确认按钮的意图走
    event.preventDefault();
    onConfirm();
  }
}

// 打开时把焦点放到确认按钮，并锁住背景滚动，避免弹窗下面还能滚
watch(
  () => state.visible,
  async (visible) => {
    document.body.style.overflow = visible ? "hidden" : "";
    if (visible) {
      await nextTick();
      confirmRef.value?.focus();
    }
  }
);

onMounted(() => window.addEventListener("keydown", onKeydown));
onBeforeUnmount(() => {
  window.removeEventListener("keydown", onKeydown);
  document.body.style.overflow = "";
});
</script>

<style scoped>
.confirm-mask {
  position: fixed;
  inset: 0;
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(2px);
}

.confirm-card {
  width: min(460px, 100%);
  padding: 24px 24px 20px;
  background: var(--surface);
  border-radius: 14px;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.22);
}

.confirm-head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.confirm-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--primary-light);
  color: var(--primary-dark);
}

.tone-danger .confirm-icon {
  background: #fee2e2;
  color: var(--danger);
}

.confirm-title {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: var(--text);
}

.confirm-message {
  margin: 14px 0 0;
  color: var(--muted);
  line-height: 1.7;
  white-space: pre-line;
}

.confirm-details {
  margin: 14px 0 0;
  padding: 12px 14px;
  background: var(--surface-soft);
  border: 1px solid var(--border);
  border-radius: 10px;
}

.confirm-row {
  display: flex;
  gap: 12px;
  font-size: 13px;
}

.confirm-row + .confirm-row {
  margin-top: 6px;
}

.confirm-row dt {
  flex: none;
  width: 62px;
  color: var(--muted);
}

.confirm-row dd {
  margin: 0;
  color: var(--text);
  word-break: break-all;
}

.confirm-foot {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 22px;
}

.confirm-enter-active {
  transition: opacity 0.18s ease;
}

.confirm-leave-active {
  transition: opacity 0.14s ease;
}

.confirm-enter-from,
.confirm-leave-to {
  opacity: 0;
}

.confirm-enter-active .confirm-card {
  animation: confirm-pop 0.2s ease;
}

@keyframes confirm-pop {
  from {
    transform: translateY(10px) scale(0.97);
    opacity: 0;
  }
  to {
    transform: none;
    opacity: 1;
  }
}
</style>
