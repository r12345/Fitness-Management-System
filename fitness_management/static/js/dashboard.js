/* 管理员数据大盘演示脚本 */
(function () {
  "use strict";

  const trendData = {
    day: {
      label: "今日",
      categories: ["09:00", "10:00", "11:00", "14:00", "16:00", "18:00", "20:00"],
      members: [8, 16, 12, 22, 26, 31, 18],
      revenue: [1200, 2600, 1800, 5200, 6800, 8600, 4200]
    },
    week: {
      label: "本周",
      categories: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
      members: [18, 26, 21, 34, 29, 42, 23],
      revenue: [3200, 5600, 4200, 8900, 7600, 12400, 6800]
    },
    month: {
      label: "本月",
      categories: ["第1周", "第2周", "第3周", "第4周", "第5周"],
      members: [86, 108, 96, 124, 42],
      revenue: [16800, 21400, 19800, 25600, 8200]
    }
  };

  const reservations = [
    { member: "王琳", course: "哈他瑜伽", time: "今天 19:30", status: "已预约" },
    { member: "李强", course: "燃脂有氧操", time: "明天 18:00", status: "已预约" },
    { member: "赵敏", course: "动感单车", time: "明天 20:00", status: "已签到" },
    { member: "陈晨", course: "一对一塑形", time: "后天 15:00", status: "已预约" }
  ];

  const activities = [
    { user: "前台小周", content: "会员王琳续费季卡", time: "10:24" },
    { user: "教练张昊", content: "更新课程燃脂有氧操时间", time: "09:48" },
    { user: "超级管理员", content: "处理跑步机报修", time: "09:12" },
    { user: "前台小周", content: "新会员李强开卡", time: "08:36" }
  ];

  function renderTable() {
    const reservationBody = document.getElementById("recent-reservations");
    reservationBody.innerHTML = reservations.map(function (item) {
      const statusClass = item.status === "已签到" ? "success" : "info";
      return "<tr>" +
        "<td>" + item.member + "</td>" +
        "<td>" + item.course + "</td>" +
        "<td>" + item.time + "</td>" +
        "<td><span class=\"badge " + statusClass + "\">" + item.status + "</span></td>" +
      "</tr>";
    }).join("");

    const activityBody = document.getElementById("activity-log");
    activityBody.innerHTML = activities.map(function (item) {
      return "<tr>" +
        "<td>" + item.user + "</td>" +
        "<td>" + item.content + "</td>" +
        "<td>" + item.time + "</td>" +
      "</tr>";
    }).join("");
  }

  function renderTrend(period) {
    const data = trendData[period] || trendData.week;
    document.getElementById("period-label").textContent = data.label;
    const chart = echarts.init(document.getElementById("trend-chart"));
    chart.setOption({
      color: ["#0f766e", "#d97706"],
      tooltip: { trigger: "axis" },
      legend: { data: ["会员数", "营收"], top: 12, right: 20 },
      grid: { left: 50, right: 50, top: 56, bottom: 32 },
      xAxis: {
        type: "category",
        data: data.categories,
        boundaryGap: false
      },
      yAxis: [
        { type: "value", name: "会员数", splitLine: { lineStyle: { color: "#eef2f6" } } },
        { type: "value", name: "营收", splitLine: { show: false } }
      ],
      series: [
        {
          name: "会员数",
          type: "line",
          smooth: true,
          data: data.members,
          areaStyle: { opacity: 0.14 }
        },
        {
          name: "营收",
          type: "line",
          yAxisIndex: 1,
          smooth: true,
          data: data.revenue,
          areaStyle: { opacity: 0.08 }
        }
      ]
    });
  }

  function renderCharts() {
    if (!window.echarts) {
      window.GymUI.toast("图表组件未加载，请检查网络后刷新", "warn");
      return;
    }

    renderTrend("week");

    const cardChart = echarts.init(document.getElementById("card-chart"));
    cardChart.setOption({
      color: ["#0f766e", "#d97706", "#2563eb", "#dc2626"],
      tooltip: { trigger: "item" },
      legend: { bottom: 12 },
      series: [
        {
          name: "卡种占比",
          type: "pie",
          radius: ["42%", "68%"],
          center: ["50%", "44%"],
          label: { formatter: "{b}\n{d}%" },
          data: [
            { value: 480, name: "年卡" },
            { value: 320, name: "季卡" },
            { value: 286, name: "月卡" },
            { value: 200, name: "次卡" }
          ]
        }
      ]
    });

    const coachChart = echarts.init(document.getElementById("coach-chart"));
    coachChart.setOption({
      color: ["#0f766e"],
      tooltip: { trigger: "axis" },
      grid: { left: 50, right: 24, top: 28, bottom: 48 },
      xAxis: {
        type: "category",
        data: ["张昊", "刘洋", "周琪", "王哲", "孙悦"]
      },
      yAxis: { type: "value", name: "课时" },
      series: [
        {
          name: "授课课时",
          type: "bar",
          barWidth: 22,
          data: [42, 38, 35, 46, 29],
          itemStyle: { borderRadius: [4, 4, 0, 0] }
        }
      ]
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    renderTable();
    renderCharts();

    document.querySelectorAll("#date-filter button").forEach(function (btn) {
      btn.addEventListener("click", function () {
        document.querySelectorAll("#date-filter button").forEach(function (item) {
          item.classList.remove("active");
        });
        btn.classList.add("active");
        renderTrend(btn.getAttribute("data-period"));
      });
    });

    window.addEventListener("resize", function () {
      if (!window.echarts) {
        return;
      }
      ["trend-chart", "card-chart", "coach-chart"].forEach(function (id) {
        const chart = echarts.getInstanceByDom(document.getElementById(id));
        if (chart) {
          chart.resize();
        }
      });
    });
  });
})();
