/* 教练工作台演示脚本 */
(function () {
  "use strict";

  let schedules = [
    { id: "S01", date: "2026-08-27", time: "09:00 - 10:00", course: "增肌基础课", location: "力量区 C1", booked: 8, status: "未开始" },
    { id: "S02", date: "2026-08-28", time: "19:00 - 20:00", course: "一对一塑形", location: "私教室 1", booked: 1, status: "已预约" },
    { id: "S03", date: "2026-08-29", time: "15:00 - 17:00", course: "肩颈力量训练", location: "团课教室 E1", booked: 12, status: "已预约" },
    { id: "S04", date: "2026-08-30", time: "10:00 - 11:00", course: "增肌基础课", location: "力量区 C1", booked: 6, status: "已签到" }
  ];

  const students = [
    { name: "王琳", phone: "13800000001", goal: "塑形", plan: "肩背训练计划", recent: "2026-08-26" },
    { name: "陈晨", phone: "13800000004", goal: "增肌", plan: "全身力量计划", recent: "2026-08-25" },
    { name: "郑雪", phone: "13800000011", goal: "减脂", plan: "核心燃脂计划", recent: "2026-08-24" },
    { name: "郭磊", phone: "13800000012", goal: "体态调整", plan: "体态纠正计划", recent: "2026-08-22" }
  ];

  const records = [
    { date: "2026-08-26", course: "增肌基础课", student: "王琳", hours: "1 课时", score: "5.0", comment: "动作执行标准" },
    { date: "2026-08-25", course: "一对一塑形", student: "陈晨", hours: "2 课时", score: "4.9", comment: "训练强度合适" },
    { date: "2026-08-24", course: "肩颈力量训练", student: "郑雪", hours: "1 课时", score: "4.8", comment: "需注意呼吸节奏" }
  ];

  let plans = [
    { student: "王琳", goal: "塑形", part: "肩背、核心", action: "哑铃划船、平板支撑", sets: "4 组 × 12 次", frequency: "每周 3 次", start: "2026-08-01", end: "2026-09-30" },
    { student: "陈晨", goal: "增肌", part: "胸、背、腿", action: "卧推、深蹲、硬拉", sets: "5 组 × 8 次", frequency: "每周 4 次", start: "2026-08-10", end: "2026-11-10" },
    { student: "郑雪", goal: "减脂", part: "全身循环", action: "战绳、开合跳、划船", sets: "3 组 × 20 次", frequency: "每周 4 次", start: "2026-08-15", end: "2026-10-15" }
  ];

  function renderSchedules() {
    const body = document.getElementById("coach-schedule-body");
    if (!schedules.length) {
      body.innerHTML = "<tr><td colspan=\"7\">暂无排课记录</td></tr>";
    } else {
      body.innerHTML = schedules.map(function (item) {
        const statusClass = item.status === "已签到" ? "success" : item.status === "已预约" ? "info" : "warn";
        return "<tr>" +
          "<td>" + item.date + "</td>" +
          "<td>" + item.time + "</td>" +
          "<td>" + item.course + "</td>" +
          "<td>" + item.location + "</td>" +
          "<td>" + item.booked + " 人</td>" +
          "<td><span class=\"badge " + statusClass + "\">" + item.status + "</span></td>" +
          "<td><button class=\"btn btn-secondary btn-sm\" data-schedule-id=\"" + item.id + "\">签到确认</button></td>" +
        "</tr>";
      }).join("");
    }
  }

  function renderStudents() {
    const body = document.getElementById("coach-students-body");
    body.innerHTML = students.map(function (item) {
      return "<tr>" +
        "<td>" + item.name + "</td>" +
        "<td>" + item.phone + "</td>" +
        "<td>" + item.goal + "</td>" +
        "<td>" + item.plan + "</td>" +
        "<td>" + item.recent + "</td>" +
        "<td><button class=\"btn btn-secondary btn-sm\" data-student-name=\"" + item.name + "\">制定计划</button></td>" +
      "</tr>";
    }).join("");
  }

  function renderRecords() {
    const body = document.getElementById("coach-records-body");
    body.innerHTML = records.map(function (item) {
      return "<tr>" +
        "<td>" + item.date + "</td>" +
        "<td>" + item.course + "</td>" +
        "<td>" + item.student + "</td>" +
        "<td>" + item.hours + "</td>" +
        "<td>" + item.score + "</td>" +
        "<td>" + item.comment + "</td>" +
      "</tr>";
    }).join("");
  }

  function renderPlans() {
    const body = document.getElementById("coach-plans-body");
    if (!plans.length) {
      body.innerHTML = "<tr><td colspan=\"7\">暂无训练计划</td></tr>";
    } else {
      body.innerHTML = plans.map(function (item) {
        return "<tr>" +
          "<td>" + item.student + "</td>" +
          "<td>" + item.goal + "</td>" +
          "<td>" + item.part + "</td>" +
          "<td>" + item.action + "</td>" +
          "<td>" + item.sets + "</td>" +
          "<td>" + item.frequency + "</td>" +
          "<td>" + item.start + " 至 " + item.end + "</td>" +
        "</tr>";
      }).join("");
    }
  }

  function switchTab(key) {
    document.querySelectorAll("#coach-tabs .tab-btn").forEach(function (btn) {
      btn.classList.toggle("active", btn.getAttribute("data-tab") === key);
    });
    document.querySelectorAll(".panel .tab-content").forEach(function (content) {
      content.classList.toggle("active", content.id === "tab-" + key);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    renderSchedules();
    renderStudents();
    renderRecords();
    renderPlans();

    document.querySelectorAll("#coach-tabs .tab-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        switchTab(btn.getAttribute("data-tab"));
      });
    });

    document.getElementById("add-schedule-btn").addEventListener("click", function () {
      document.getElementById("schedule-date").value = "";
      document.getElementById("schedule-start").value = "19:00";
      document.getElementById("schedule-end").value = "20:00";
      document.getElementById("schedule-location").value = "";
      window.GymUI.openModal("coach-schedule-modal");
    });

    document.getElementById("save-coach-schedule-btn").addEventListener("click", function () {
      const date = document.getElementById("schedule-date").value;
      const start = document.getElementById("schedule-start").value;
      const end = document.getElementById("schedule-end").value;
      const course = document.getElementById("schedule-course").value;
      const location = document.getElementById("schedule-location").value.trim();
      if (!date || !start || !end || !location) {
        window.GymUI.toast("请完整填写排课信息", "warn");
        return;
      }
      schedules.unshift({
        id: "S" + String(schedules.length + 1).padStart(2, "0"),
        date: date,
        time: start + " - " + end,
        course: course,
        location: location,
        booked: 0,
        status: "未开始"
      });
      window.GymUI.closeModal("coach-schedule-modal");
      window.GymUI.toast("排课已新增");
      renderSchedules();
    });

    document.getElementById("coach-schedule-body").addEventListener("click", function (event) {
      const btn = event.target.closest("[data-schedule-id]");
      if (!btn) {
        return;
      }
      const item = schedules.find(function (target) {
        return target.id === btn.getAttribute("data-schedule-id");
      });
      if (item) {
        item.status = "已签到";
        window.GymUI.toast(item.course + " 签到完成");
        renderSchedules();
      }
    });

    document.getElementById("add-plan-btn").addEventListener("click", function () {
      openPlanModal(null);
    });

    document.getElementById("coach-students-body").addEventListener("click", function (event) {
      const btn = event.target.closest("[data-student-name]");
      if (!btn) {
        return;
      }
      openPlanModal(btn.getAttribute("data-student-name"));
    });

    document.getElementById("save-plan-btn").addEventListener("click", function () {
      const student = document.getElementById("plan-student").value;
      const goal = document.getElementById("plan-goal").value;
      const part = document.getElementById("plan-part").value.trim();
      const action = document.getElementById("plan-action").value.trim();
      const sets = document.getElementById("plan-sets").value.trim();
      const frequency = document.getElementById("plan-frequency").value.trim();
      const start = document.getElementById("plan-start").value;
      const end = document.getElementById("plan-end").value;
      if (!part || !action || !sets || !frequency || !start || !end) {
        window.GymUI.toast("请完整填写训练计划", "warn");
        return;
      }
      plans.unshift({
        student: student,
        goal: goal,
        part: part,
        action: action,
        sets: sets,
        frequency: frequency,
        start: start,
        end: end
      });
      window.GymUI.closeModal("plan-modal");
      window.GymUI.toast("训练计划已保存");
      renderPlans();
    });
  });

  function openPlanModal(studentName) {
    if (studentName) {
      document.getElementById("plan-student").value = studentName;
    }
    document.getElementById("plan-part").value = "";
    document.getElementById("plan-action").value = "";
    document.getElementById("plan-sets").value = "";
    document.getElementById("plan-frequency").value = "";
    document.getElementById("plan-start").value = "";
    document.getElementById("plan-end").value = "";
    document.getElementById("plan-remark").value = "";
    window.GymUI.openModal("plan-modal");
  }
})();
