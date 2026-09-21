<template>
  <div v-if="open" class="modal-mask" @click.self="close">
    <div class="modal">
      <div class="modal-header">
        <h3 class="panel-title">修改密码</h3>
        <button class="btn btn-secondary btn-sm" type="button" @click="close">关闭</button>
      </div>
      <div class="modal-body">
        <div class="form-grid">
          <div class="field full">
            <label>当前密码</label>
            <input v-model="form.old_password" type="password" autocomplete="current-password" placeholder="请输入当前密码">
          </div>
          <div class="field full">
            <label>新密码</label>
            <input v-model="form.new_password" type="password" autocomplete="new-password" placeholder="至少 6 位">
          </div>
          <div class="field full">
            <label>确认新密码</label>
            <input v-model="form.confirm" type="password" autocomplete="new-password" placeholder="再输入一次新密码">
          </div>
        </div>
        <!-- 初始账号（新增教练/运营/会员时开的）统一是 123456，改完就只有本人知道了。 -->
        <p class="field-hint">
          新密码至少 6 位，且不能与当前密码相同。修改后请用新密码登录。
        </p>
        <p v-if="error" class="field-hint" style="color: #c0392b;">{{ error }}</p>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" type="button" @click="close">取消</button>
        <button class="btn btn-primary" type="button" :disabled="submitting" @click="submit">
          {{ submitting ? "提交中…" : "确认修改" }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, watch } from "vue";
import { changePassword } from "../api/user.js";

/**
 * 修改密码弹窗。
 *
 * 顶层布局（AppLayout 的顶栏）与会员个人中心都用它，
 * 所以成功提示交给调用方显示 —— 弹窗一关，里面的提示条就看不见了。
 */
const props = defineProps({
  open: { type: Boolean, default: false }
});
const emit = defineEmits(["update:open", "saved"]);

const form = reactive({ old_password: "", new_password: "", confirm: "" });
const error = ref("");
const submitting = ref(false);

/** 每次打开都重置：上一次输了一半的密码不该留在框里 */
watch(
  () => props.open,
  (visible) => {
    if (visible) {
      form.old_password = "";
      form.new_password = "";
      form.confirm = "";
      error.value = "";
      submitting.value = false;
    }
  }
);

function close() {
  emit("update:open", false);
}

async function submit() {
  // 三个框都做前后端双重校验：前端先给出人话提示，后端仍会再校验一遍
  if (!form.old_password) {
    error.value = "请输入当前密码";
    return;
  }
  if (form.new_password.length < 6) {
    error.value = "新密码至少 6 位";
    return;
  }
  if (form.new_password === form.old_password) {
    error.value = "新密码不能与当前密码相同";
    return;
  }
  if (form.new_password !== form.confirm) {
    error.value = "两次输入的新密码不一致";
    return;
  }
  error.value = "";
  submitting.value = true;
  try {
    const res = await changePassword(form.old_password, form.new_password);
    emit("saved", res.msg || "密码已修改");
    close();
  } catch (err) {
    // 后端对「当前密码不正确」回 400，这里把原话显示出来
    error.value = err.friendlyMessage || err.msg || "修改失败，请重试";
  } finally {
    submitting.value = false;
  }
}
</script>
