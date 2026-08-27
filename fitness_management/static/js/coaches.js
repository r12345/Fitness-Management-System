/* 教练管理页面演示脚本 */
(function () {
  "use strict";

  let coaches = [
    { id: "C01", name: "张昊", phone: "13900000001", specialty: ["增肌", "减脂"], status: "在职", hireDate: "2023-03-12", hours: 42, score: 4.9, salary: 12000, remark: "" },
    { id: "C02", name: "刘洋", phone: "13900000002", specialty: ["瑜伽", "普拉提"], status: "在职", hireDate: "2022-09-05", hours: 38, score: 4.8, salary: 11000, remark: "擅长女性会员课程" },
    { id: "C03", name: "周琪", phone: "13900000003", specialty: ["瑜伽", "减脂"], status: "休假", hireDate: "2024-01-18", hours: 24, score: 4.7, salary: 9500, remark: "休假至月底" },
    { id: "C04", name: "王哲", phone: "13900000004", specialty: ["增肌", "康复"], status: "在职", hireDate: "2021-06-10", hours: 46, score: 4.9, salary: 13500, remark: "" },
    { id: "C05", name: "孙悦", phone: "13900000005", specialty: ["搏击", "减脂"], status: "在职", hireDate: "2023-11-02", hours: 29, score: 4.6, salary: 10000, remark: "" },
    { id: "C06", name: "何佳", phone: "13900000006", specialty: ["普拉提", "康复"], status: "离职", hireDate: "2022-04-21", hours: 0, score: 4.5, salary: 0, remark: "已离职" },
    { id: "C07", name: "马涛", phone: "13900000007", specialty: ["减脂", "搏击"], status: "在职", hireDate: "2024-05-16", hours: 31, score: 4.7, salary: 10800, remark: "" },
    { id: "C08", name: "郑雪", phone: "13900000008", specialty: ["瑜伽", "普拉提"], status: "在职", hireDate: "2023-08-08", hours: 36, score: 4.8, salary: 10500, remark: "" }
  ];

  const scheduleData = {
    C01: [{ weekday: "周一", start: "09:00", end: "10:00" }, { weekday: "周三", start: "19:00", end: "20:00" }, { weekday: "周六", start: "10:00", end: "12:00" }],
    C02: [{ weekday: "周二", start: "18:30", end: "19:30" }, { weekday: "周五", start: "19:30", end: "20:30" }],
    C03: [{ weekday: "周四", start: "10:00", end: "11:00" }],
    C04: [{ weekday: "周一", start: "18:00", end: "19:00" }, { weekday: "周日", start: "15:00", end: "17:00" }],
    C05: [{ weekday: "周二", start: "20:00", end: "21:00" }, { weekday: "周六", start: "19:00", end: "20:00" }],
    C07: [{ weekday: "周三", start: "18:30", end: "19:30" }, { weekday: "周日", start: "10:00", end: "11:00" }],
    C08: [{ weekday: "周五", start: "10:00", end: "11:00" }, { weekday: "周日", start: "19:30", end: "20:30" }]
  };

  let page = 1;
  const pageSize = 8;
  let currentCoach = null;

  function getFilteredCoaches() {
    const keyword = document.getElementById("coach-keyword").value.trim().toLowerCase();
    const status = document.getElementById("coach-status-filter").value;
    const specialty = document.getElementById("coach-specialty-filter").value;
    return coaches.filter(function (item) {
      const matchKeyword = !keyword || item.name.toLowerCase().indexOf(keyword) >= 0 || item.phone.indexOf(keyword) >= 0;
      const matchStatus = !status || item.status === status;
      const matchSpecialty = !specialty || item.specialty.indexOf(specialty) >= 0;
      return matchKeyword && matchStatus && matchSpecialty;
    });
  }

  function statusClass(status) {
    if (status === "在职") {
      return "success";
    }
    if (status === "休假") {
      return "warn";
    }
    return "muted";
  }

  function renderCoaches() {
    const list = getFilteredCoaches();
    document.getElementById("coach-count").textContent = "共 " + list.length + " 条";
    const totalPages = Math.max(1, Math.ceil(list.length / pageSize));
    page = Math.min(page, totalPages);
    const start = (page - 1) * pageSize;
    const rows = list.slice(start, start + pageSize);
    const body = document.getElementById("coach-table-body");
    if (!rows.length) {
      body.innerHTML = "<tr><td colspan=\"8\">暂无符合条件的教练</td></tr>";
    } else {
      body.innerHTML = rows.map(function (item) {
        return "<tr>" +
          "<td>" + item.name + "</td>" +
          "<td>" + item.phone + "</td>" +
          "<td>" + item.specialty.join("、") + "</td>" +
          "<td><span class=\"badge " + statusClass(item.status) + "\">" + item.status + "</span></td>" +
          "<td>" + item.hireDate + "</td>" +
          "<td>" + item.hours + " 课时</td>" +
          "<td>" + item.score.toFixed(1) + "</td>" +
          "<td><div class=\"table-actions\">" +
            "<button class=\"btn btn-secondary btn-sm\" data-action=\"edit\" data-id=\"" + item.id + "\">编辑</button>" +
            "<button class=\"btn btn-secondary btn-sm\" data-action=\"schedule\" data-id=\"" + item.id + "\">排班</button>" +
            "<button class=\"btn btn-secondary btn-sm\" data-action=\"stats\" data-id=\"" + item.id + "\">授课统计</button>" +
            "<button class=\"btn btn-danger btn-sm\" data-action=\"delete\" data-id=\"" + item.id + "\">删除</button>" +
          "</div></td>" +
        "</tr>";
      }).join("");
    }
    window.GymUI.renderPagination("coach-pagination", page, list.length, pageSize, function (nextPage) {
      page = nextPage;
      renderCoaches();
    });
  }

  function findCoach(id) {
    return coaches.find(function (item) {
      return item.id === id;
    });
  }

  function openCoachModal(coach) {
    currentCoach = coach;
    document.getElementById("coach-modal-title").textContent = coach ? "编辑教练" : "新增教练";
    document.getElementById("coach-id").value = coach ? coach.id : "";
    document.getElementById("coach-name").value = coach ? coach.name : "";
    document.getElementById("coach-phone").value = coach ? coach.phone : "";
    document.getElementById("coach-salary").value = coach ? coach.salary : "";
    document.getElementById("coach-hire-date").value = coach ? coach.hireDate : "";
    document.getElementById("coach-status").value = coach ? coach.status : "在职";
    document.getElementById("coach-remark").value = coach ? coach.remark || "" : "";
    document.querySelectorAll("#specialty-checkboxes input").forEach(function (checkbox) {
      checkbox.checked = coach ? coach.specialty.indexOf(checkbox.value) >= 0 : false;
    });
    window.GymUI.openModal("coach-modal");
  }

  function saveCoach() {
    const id = document.getElementById("coach-id").value;
    const specialty = Array.from(document.querySelectorAll("#specialty-checkboxes input:checked")).map(function (item) {
      return item.value;
    });
    const data = {
      name: document.getElementById("coach-name").value.trim(),
      phone: document.getElementById("coach-phone").value.trim(),
      specialty: specialty,
      salary: Number(document.getElementById("coach-salary").value || 0),
      hireDate: document.getElementById("coach-hire-date").value,
      status: document.getElementById("coach-status").value,
      remark: document.getElementById("coach-remark").value.trim()
    };
    if (!data.name || !data.phone) {
      window.GymUI.toast("请填写教练姓名和联系方式", "warn");
      return;
    }
    if (id) {
      const index = coaches.findIndex(function (item) {
        return item.id === id;
      });
      if (index >= 0) {
        coaches[index] = Object.assign({}, coaches[index], data);
      }
      window.GymUI.toast("教练信息已更新");
    } else {
      const nextId = "C" + String(coaches.length + 1).padStart(2, "0");
      coaches.unshift(Object.assign({ id: nextId, hours: 0, score: 5.0 }, data));
      window.GymUI.toast("教练已新增");
    }
    window.GymUI.closeModal("coach-modal");
    renderCoaches();
  }

  function renderSchedule(coach) {
    currentCoach = coach;
    document.getElementById("schedule-coach-name").textContent = coach.name;
    const slots = scheduleData[coach.id] || [];
    const body = document.getElementById("schedule-table-body");
    if (!slots.length) {
      body.innerHTML = "<tr><td colspan=\"5\">暂无排班时段</td></tr>";
    } else {
      body.innerHTML = slots.map(function (slot, index) {
        return "<tr>" +
          "<td>" + slot.weekday + "</td>" +
          "<td>" + slot.start + "</td>" +
          "<td>" + slot.end + "</td>" +
          "<td><span class=\"badge success\">可用</span></td>" +
          "<td><button class=\"btn btn-danger btn-sm\" data-schedule-index=\"" + index + "\">移除</button></td>" +
        "</tr>";
      }).join("");
    }
    window.GymUI.openModal("schedule-modal");
  }

  function renderStats(coach) {
    document.getElementById("stats-coach-name").textContent = coach.name;
    document.getElementById("stats-hours").textContent = coach.hours + " 课时";
    document.getElementById("stats-students").textContent = Math.max(1, Math.round(coach.hours / 4));
    document.getElementById("stats-revenue").textContent = "¥ " + (coach.hours * 120).toLocaleString("zh-CN");
    const records = [
      { date: "2026-08-26", course: "增肌基础课", student: "陈晨", hours: 1, score: "5.0" },
      { date: "2026-08-25", course: "减脂训练营", student: "李强", hours: 1, score: "4.9" },
      { date: "2026-08-24", course: "一对一塑形", student: "王琳", hours: 2, score: "5.0" }
    ];
    document.getElementById("stats-table-body").innerHTML = records.map(function (item) {
      return "<tr>" +
        "<td>" + item.date + "</td>" +
        "<td>" + item.course + "</td>" +
        "<td>" + item.student + "</td>" +
        "<td>" + item.hours + " 课时</td>" +
        "<td>" + item.score + "</td>" +
      "</tr>";
    }).join("");
    window.GymUI.openModal("coach-stats-modal");
  }

  document.addEventListener("DOMContentLoaded", function () {
    renderCoaches();

    document.getElementById("add-coach-btn").addEventListener("click", function () {
      openCoachModal(null);
    });
    document.getElementById("save-coach-btn").addEventListener("click", saveCoach);

    document.getElementById("coach-search-btn").addEventListener("click", function () {
      page = 1;
      renderCoaches();
    });
    document.getElementById("coach-reset-btn").addEventListener("click", function () {
      document.getElementById("coach-keyword").value = "";
      document.getElementById("coach-status-filter").value = "";
      document.getElementById("coach-specialty-filter").value = "";
      page = 1;
      renderCoaches();
    });

    document.getElementById("coach-table-body").addEventListener("click", function (event) {
      const btn = event.target.closest("[data-action]");
      if (!btn) {
        return;
      }
      const coach = findCoach(btn.getAttribute("data-id"));
      if (!coach) {
        return;
      }
      const action = btn.getAttribute("data-action");
      if (action === "edit") {
        openCoachModal(coach);
      } else if (action === "schedule") {
        renderSchedule(coach);
      } else if (action === "stats") {
        renderStats(coach);
      } else if (action === "delete") {
        window.GymUI.confirmAction("确定删除教练 " + coach.name + " 吗？", function () {
          coaches = coaches.filter(function (item) {
            return item.id !== coach.id;
          });
          delete scheduleData[coach.id];
          window.GymUI.toast("教练已删除");
          renderCoaches();
        });
      }
    });

    document.getElementById("add-schedule-btn").addEventListener("click", function () {
      if (!currentCoach) {
        return;
      }
      const coach = currentCoach;
      const weekday = document.getElementById("schedule-weekday").value;
      const start = document.getElementById("schedule-start").value;
      const end = document.getElementById("schedule-end").value;
      if (!start || !end) {
        window.GymUI.toast("请选择开始和结束时间", "warn");
        return;
      }
      if (!scheduleData[coach.id]) {
        scheduleData[coach.id] = [];
      }
      scheduleData[coach.id].push({ weekday: weekday, start: start, end: end });
      renderSchedule(coach);
      window.GymUI.toast("排班时段已添加");
    });

    document.getElementById("schedule-table-body").addEventListener("click", function (event) {
      const btn = event.target.closest("[data-schedule-index]");
      if (!btn) {
        return;
      }
      const coach = currentCoach;
      if (!coach) {
        return;
      }
      const index = Number(btn.getAttribute("data-schedule-index"));
      scheduleData[coach.id].splice(index, 1);
      renderSchedule(coach);
    });
  });
})();
