/* 会员个人中心演示脚本 */
(function () {
  "use strict";

  let appointments = [
    { id: "A01", course: "哈他瑜伽", time: "今天 19:30", coach: "刘洋", status: "已预约" },
    { id: "A02", course: "一对一塑形", time: "08月29日 15:00", coach: "张昊", status: "已预约" },
    { id: "A03", course: "燃脂有氧操", time: "08月24日 18:00", coach: "孙悦", status: "已完成" },
    { id: "A04", course: "肩颈放松瑜伽", time: "08月20日 10:00", coach: "郑雪", status: "已取消" }
  ];

  const memberCourses = [
    { name: "哈他瑜伽", meta: "周一 19:30 · 刘洋", tag: "已预约", tagClass: "info" },
    { name: "一对一塑形", meta: "私教课 · 张昊", tag: "已预约", tagClass: "info" },
    { name: "燃脂有氧操", meta: "周三 18:00 · 孙悦", tag: "已完成", tagClass: "success" }
  ];

  const trainingLog = [
    { date: "2026-08-26", content: "肩背力量训练", weight: "45kg", duration: "83 分钟", fat: "21.8%" },
    { date: "2026-08-24", content: "瑜伽核心训练", weight: "自重", duration: "90 分钟", fat: "22.1%" },
    { date: "2026-08-22", content: "下肢力量训练", weight: "60kg", duration: "85 分钟", fat: "22.0%" },
    { date: "2026-08-19", content: "有氧燃脂训练", weight: "8kg", duration: "60 分钟", fat: "22.3%" }
  ];

  const checkins = [
    { date: "2026-08-26", in: "18:42", out: "20:05", duration: "83 分钟" },
    { date: "2026-08-24", in: "19:10", out: "20:40", duration: "90 分钟" },
    { date: "2026-08-22", in: "18:30", out: "19:55", duration: "85 分钟" }
  ];

  function statusClass(status) {
    if (status === "已完成") {
      return "success";
    }
    if (status === "已取消") {
      return "muted";
    }
    return "info";
  }

  function renderAppointments() {
    const status = document.getElementById("appointment-status").value;
    const list = appointments.filter(function (item) {
      return !status || item.status === status;
    });
    const body = document.getElementById("appointment-table-body");
    if (!list.length) {
      body.innerHTML = "<tr><td colspan=\"5\">暂无预约记录</td></tr>";
    } else {
      body.innerHTML = list.map(function (item) {
        const cancelBtn = item.status === "已预约" ? "<button class=\"btn btn-danger btn-sm\" data-cancel-id=\"" + item.id + "\">取消预约</button>" : "";
        return "<tr>" +
          "<td>" + item.course + "</td>" +
          "<td>" + item.time + "</td>" +
          "<td>" + item.coach + "</td>" +
          "<td><span class=\"badge " + statusClass(item.status) + "\">" + item.status + "</span></td>" +
          "<td>" + cancelBtn + "</td>" +
        "</tr>";
      }).join("");
    }
  }

  function renderCourses() {
    const container = document.getElementById("member-course-cards");
    container.innerHTML = memberCourses.map(function (item) {
      return "<div class=\"course-card\">" +
        "<div class=\"course-card-top\">" +
          "<h3>" + item.name + "</h3>" +
          "<span class=\"badge " + item.tagClass + "\">" + item.tag + "</span>" +
        "</div>" +
        "<div class=\"course-card-meta\">" +
          "<span>" + item.meta + "</span>" +
        "</div>" +
      "</div>";
    }).join("");
  }

  function renderTraining() {
    const body = document.getElementById("training-table-body");
    body.innerHTML = trainingLog.map(function (item) {
      return "<tr>" +
        "<td>" + item.date + "</td>" +
        "<td>" + item.content + "</td>" +
        "<td>" + item.weight + "</td>" +
        "<td>" + item.duration + "</td>" +
        "<td>" + item.fat + "</td>" +
      "</tr>";
    }).join("");

    if (!window.echarts) {
      return;
    }
    const chart = echarts.init(document.getElementById("training-chart"));
    chart.setOption({
      color: ["#0f766e"],
      tooltip: { trigger: "axis" },
      grid: { left: 40, right: 20, top: 24, bottom: 30 },
      xAxis: {
        type: "category",
        data: ["第1周", "第2周", "第3周", "第4周"],
        boundaryGap: false
      },
      yAxis: { type: "value", minInterval: 1 },
      series: [
        {
          name: "训练次数",
          type: "line",
          smooth: true,
          data: [2, 3, 4, 3],
          areaStyle: { opacity: 0.16 }
        }
      ]
    });
  }

  function renderCheckins() {
    const body = document.getElementById("checkin-table-body");
    body.innerHTML = checkins.map(function (item) {
      return "<tr>" +
        "<td>" + item.date + "</td>" +
        "<td>" + item.in + "</td>" +
        "<td>" + item.out + "</td>" +
        "<td>" + item.duration + "</td>" +
      "</tr>";
    }).join("");
  }

  function switchTab(key) {
    document.querySelectorAll("#center-tabs .tab-btn").forEach(function (btn) {
      btn.classList.toggle("active", btn.getAttribute("data-tab") === key);
    });
    document.querySelectorAll(".panel .tab-content").forEach(function (content) {
      content.classList.toggle("active", content.id === "tab-" + key);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    renderAppointments();
    renderCourses();
    renderTraining();
    renderCheckins();

    document.querySelectorAll("#center-tabs .tab-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        switchTab(btn.getAttribute("data-tab"));
      });
    });

    document.getElementById("appointment-filter-btn").addEventListener("click", renderAppointments);

    document.getElementById("appointment-table-body").addEventListener("click", function (event) {
      const btn = event.target.closest("[data-cancel-id]");
      if (!btn) {
        return;
      }
      const id = btn.getAttribute("data-cancel-id");
      const item = appointments.find(function (target) {
        return target.id === id;
      });
      if (!item) {
        return;
      }
      window.GymUI.confirmAction("确定取消课程 " + item.course + " 的预约吗？", function () {
        item.status = "已取消";
        window.GymUI.toast("预约已取消");
        renderAppointments();
      });
    });

    document.getElementById("checkin-btn").addEventListener("click", function () {
      const now = new Date();
      const time = now.toTimeString().slice(0, 5);
      checkins.unshift({ date: now.toISOString().slice(0, 10), in: time, out: "待记录", duration: "训练中" });
      window.GymUI.toast("到店打卡成功");
      renderCheckins();
    });

    document.getElementById("profile-form").addEventListener("submit", function (event) {
      event.preventDefault();
      window.GymUI.toast("个人信息已保存");
    });
  });
})();
