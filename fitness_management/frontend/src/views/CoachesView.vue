<template>
  <div>
    <div class="page-header">
      <div>
        <h1>教练管理</h1>
        <p class="page-desc">管理教练档案、专长排班与授课统计。</p>
      </div>
    </div>

    <div class="stat-grid">
      <StatCard label="在职教练" value="12" unit="人" icon="人" />
      <StatCard label="今日排课" value="18" unit="节" icon="排" />
      <StatCard label="本月授课课时" value="246" unit="课时" icon="课" tone="warn" />
      <StatCard label="平均评分" value="4.8" unit="分" icon="分" />
    </div>

    <div class="panel">
      <div class="panel-header">
        <h2 class="panel-title">教练列表</h2>
      </div>
      <div class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>姓名</th><th>联系方式</th><th>专长</th><th>状态</th><th>入职时间</th><th>本月课时</th><th>评分</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in coaches" :key="item.name">
                <td>{{ item.name }}</td>
                <td>{{ item.phone }}</td>
                <td>{{ item.specialty }}</td>
                <td><span class="badge" :class="item.status === '在职' ? 'success' : item.status === '休假' ? 'warn' : 'muted'">{{ item.status }}</span></td>
                <td>{{ item.hireDate }}</td>
                <td>{{ item.hours }} 课时</td>
                <td>{{ item.score.toFixed(1) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { coaches } from "../data/mock";
import StatCard from "../components/StatCard.vue";
</script>
