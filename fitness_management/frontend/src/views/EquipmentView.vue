<template>
  <div>
    <transition name="fade">
      <div v-if="toast.message" class="toast-banner" :class="toast.type">{{ toast.message }}</div>
    </transition>

    <div class="page-header">
      <div>
        <h1>{{ isReception ? "器材报修" : "器材管理" }}</h1>
        <p class="page-desc">{{ isReception ? "登记器材报修，跟进维修状态和保养记录。" : "维护器材档案、报修维修、盘点和保养记录。" }}</p>
      </div>
      <div class="page-actions">
        <button v-if="canManage" class="btn btn-primary" type="button" @click="showAdd = true">新增器材</button>
      </div>
    </div>

    <div class="stat-grid">
      <StatCard label="器材总数" value="56" unit="台" icon="器" />
      <StatCard label="正常" value="48" unit="台" icon="正" />
      <StatCard label="维修中" value="6" unit="台" icon="修" tone="warn" />
      <StatCard label="已报废" value="2" unit="台" icon="废" tone="danger" />
    </div>

    <div class="panel">
      <div class="panel-header">
        <h2 class="panel-title">器材列表</h2>
      </div>
      <div class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>器材名称</th><th>型号</th><th>分类</th><th>存放位置</th><th>采购时间</th><th>价格</th><th>状态</th><th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in list" :key="item.name + item.model">
                <td>{{ item.name }}</td>
                <td>{{ item.model }}</td>
                <td>{{ item.category }}</td>
                <td>{{ item.location }}</td>
                <td>{{ item.purchaseDate }}</td>
                <td>¥ {{ item.price.toLocaleString("zh-CN") }}</td>
                <td><span class="badge" :class="statusClass(item.status)">{{ item.status }}</span></td>
                <td>
                  <div class="page-actions">
                    <button class="btn btn-secondary btn-sm" type="button" @click="openRepair(item)">报修</button>
                    <button class="btn btn-secondary btn-sm" type="button" @click="toast.show(item.name + ' 保养记录已保存')">保养</button>
                    <button v-if="canManage" class="btn btn-danger btn-sm" type="button" @click="remove(item)">删除</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-if="showAdd" class="modal-mask" @click.self="showAdd = false">
      <div class="modal">
        <div class="modal-header">
          <h3 class="panel-title">新增器材</h3>
          <button class="btn btn-secondary btn-sm" type="button" @click="showAdd = false">关闭</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field"><label>器材名称</label><input v-model="form.name" type="text"></div>
            <div class="field"><label>型号</label><input v-model="form.model" type="text"></div>
            <div class="field"><label>分类</label><input v-model="form.category" type="text"></div>
            <div class="field"><label>存放位置</label><input v-model="form.location" type="text"></div>
            <div class="field"><label>采购时间</label><input v-model="form.purchaseDate" type="date"></div>
            <div class="field"><label>价格</label><input v-model.number="form.price" type="number"></div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" @click="showAdd = false">取消</button>
          <button class="btn btn-primary" type="button" @click="saveEquipment">保存</button>
        </div>
      </div>
    </div>

    <div v-if="repairTarget" class="modal-mask" @click.self="repairTarget = null">
      <div class="modal">
        <div class="modal-header">
          <h3 class="panel-title">报修登记：{{ repairTarget.name }}</h3>
          <button class="btn btn-secondary btn-sm" type="button" @click="repairTarget = null">关闭</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field full"><label>故障描述</label><textarea v-model="repairDesc"></textarea></div>
            <div class="field"><label>维修费用</label><input v-model.number="repairCost" type="number"></div>
            <div class="field"><label>维修完成时间</label><input v-model="repairDate" type="date"></div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" @click="repairTarget = null">取消</button>
          <button class="btn btn-primary" type="button" @click="submitRepair">提交维修</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { useAuth } from "../composables/useAuth";
import { useToast } from "../composables/useToast";
import { equipment } from "../data/mock";
import StatCard from "../components/StatCard.vue";

const auth = useAuth();
const toast = useToast();
const role = auth.currentRole.value;
const canManage = role === "admin";
const isReception = role === "reception";
const list = ref(equipment.map((item) => ({ ...item })));
const showAdd = ref(false);
const repairTarget = ref(null);
const repairDesc = ref("");
const repairCost = ref(0);
const repairDate = ref("");
const form = reactive({
  name: "",
  model: "",
  category: "有氧器械",
  location: "",
  purchaseDate: "",
  price: 0
});

function statusClass(status) {
  if (status === "正常") return "success";
  if (status === "维修") return "warn";
  return "muted";
}

function saveEquipment() {
  list.value.unshift({
    ...form,
    status: "正常"
  });
  showAdd.value = false;
  toast.show("器材已新增");
}

function remove(item) {
  list.value = list.value.filter((target) => target.name + target.model !== item.name + item.model);
  toast.show("器材已删除");
}

function openRepair(item) {
  repairTarget.value = item;
  repairDesc.value = "";
  repairCost.value = 0;
  repairDate.value = "";
}

function submitRepair() {
  repairTarget.value.status = "维修";
  repairTarget.value = null;
  toast.show("报修已登记");
}
</script>
