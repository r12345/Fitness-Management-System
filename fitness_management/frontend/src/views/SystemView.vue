<template>
  <div>
    <transition name="fade">
      <div v-if="toast.message" class="toast-banner" :class="toast.type">{{ toast.message }}</div>
    </transition>

    <div class="page-header">
      <div>
        <h1>系统配置</h1>
        <p class="page-desc">维护健身房基础信息、系统日志和字典配置。</p>
      </div>
    </div>

    <div class="split-layout">
      <div class="panel">
        <div class="panel-header">
          <h2 class="panel-title">健身房基础信息</h2>
        </div>
        <div class="panel-body">
          <div class="form-grid">
            <div class="field"><label>名称</label><input v-model="form.name" type="text"></div>
            <div class="field"><label>联系电话</label><input v-model="form.phone" type="text"></div>
            <div class="field full"><label>地址</label><input v-model="form.address" type="text"></div>
            <div class="field full"><label>营业时间</label><input v-model="form.hours" type="text"></div>
          </div>
          <div class="page-actions" style="margin-top: 16px;">
            <button class="btn btn-primary" type="button" @click="save">保存配置</button>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <h2 class="panel-title">字典配置</h2>
        </div>
        <div class="panel-body no-padding">
          <div class="data-table-wrap">
            <table class="data-table">
              <thead><tr><th>字典类型</th><th>配置项</th><th>状态</th></tr></thead>
              <tbody>
                <tr v-for="item in dictionaries" :key="item.type">
                  <td>{{ item.type }}</td>
                  <td>{{ item.value }}</td>
                  <td><span class="badge success">启用</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <h2 class="panel-title">系统日志</h2>
      </div>
      <div class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead><tr><th>时间</th><th>类型</th><th>操作人</th><th>操作内容</th></tr></thead>
            <tbody>
              <tr v-for="(item, index) in logs" :key="index">
                <td>{{ item.time }}</td>
                <td>{{ item.type }}</td>
                <td>{{ item.user }}</td>
                <td>{{ item.content }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive } from "vue";
import { useToast } from "../composables/useToast";

const toast = useToast();
const form = reactive({
  name: "活力健身中心",
  phone: "0571-88886666",
  address: "杭州市西湖区健身路 88 号",
  hours: "周一至周日 08:00 - 22:00"
});

const dictionaries = [
  { type: "运动部位", value: "胸、背、腿、肩、核心、手臂" },
  { type: "器材分类", value: "有氧器械、力量器械、自由重量、瑜伽普拉提、辅助器材" },
  { type: "课程分类", value: "瑜伽、有氧操、搏击操、动感单车、力量训练" },
  { type: "卡状态", value: "正常、过期、暂停、注销" }
];

const logs = [
  { time: "2026-08-27 10:24", type: "操作日志", user: "前台小周", content: "会员王琳续费季卡" },
  { time: "2026-08-27 09:12", type: "操作日志", user: "超级管理员", content: "处理动感单车报修" },
  { time: "2026-08-27 08:36", type: "登录日志", user: "前台小周", content: "登录前台运营工作台" }
];

function save() {
  toast.show("系统配置已保存");
}
</script>
