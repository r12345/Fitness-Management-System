<template>
  <div>
    <div class="page-header">
      <div>
        <h1>前台运营工作台</h1>
        <p class="page-desc">处理会员开卡、续费、课程预约和器材报修登记。</p>
      </div>
    </div>

    <div class="stat-grid">
      <StatCard
        v-for="(item, index) in receptionData.stats"
        :key="item.label"
        :label="item.label"
        :value="item.value"
        :unit="item.unit"
        :icon="['开', '约', '修', '收'][index]"
        :tone="index === 2 ? 'warn' : ''"
      />
    </div>

    <div class="course-cards" style="margin-bottom: 20px;">
      <router-link
        v-for="item in receptionData.actions"
        :key="item.path"
        class="course-card"
        :to="item.path"
      >
        <div class="course-card-top">
          <h3>{{ item.title }}</h3>
          <span class="badge" :class="item.tone">{{ item.badge }}</span>
        </div>
        <div class="course-card-meta">
          <span>{{ item.desc }}</span>
        </div>
      </router-link>
    </div>

    <div class="panel">
      <div class="panel-header">
        <h2 class="panel-title">今日业务动态</h2>
      </div>
      <div class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>时间</th><th>业务类型</th><th>会员或器材</th><th>内容</th><th>状态</th></tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in receptionData.business" :key="index">
                <td>{{ item.time }}</td>
                <td>{{ item.type }}</td>
                <td>{{ item.target }}</td>
                <td>{{ item.content }}</td>
                <td>
                  <span class="badge" :class="item.status === '已完成' ? 'success' : item.status === '处理中' ? 'warn' : 'info'">
                    {{ item.status }}
                  </span>
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
import { receptionData } from "../data/mock";
import StatCard from "../components/StatCard.vue";
</script>
