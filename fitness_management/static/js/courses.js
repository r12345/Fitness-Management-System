/* 课程预约页面演示脚本 */
(function () {
  "use strict";

  let groupCourses = [
    { id: "G01", name: "哈他瑜伽", category: "瑜伽", coach: "刘洋", time: "周一 19:30", duration: "60 分钟", max: 20, booked: 16, status: "已上架", price: 45, remark: "适合入门会员" },
    { id: "G02", name: "燃脂有氧操", category: "有氧操", coach: "孙悦", time: "周三 18:00", duration: "60 分钟", max: 24, booked: 24, status: "已满员", price: 40, remark: "高强度间歇训练" },
    { id: "G03", name: "搏击基础课", category: "搏击操", coach: "马涛", time: "周五 20:00", duration: "60 分钟", max: 18, booked: 12, status: "已上架", price: 55, remark: "需自备拳套" },
    { id: "G04", name: "动感单车", category: "动感单车", coach: "王哲", time: "周二 20:00", duration: "45 分钟", max: 20, booked: 14, status: "已上架", price: 50, remark: "" },
    { id: "G05", name: "肩颈放松瑜伽", category: "瑜伽", coach: "郑雪", time: "周六 10:00", duration: "90 分钟", max: 16, booked: 9, status: "已上架", price: 60, remark: "" },
    { id: "G06", name: "增肌训练营", category: "力量训练", coach: "张昊", time: "周日 15:00", duration: "90 分钟", max: 12, booked: 7, status: "已下架", price: 80, remark: "暂停招生" }
  ];

  let privateCourses = [
    { id: "P01", name: "一对一塑形", coach: "张昊", duration: "60 分钟", price: 300, capacity: 10, status: "已上架", remark: "" },
    { id: "P02", name: "普拉提体态调整", coach: "刘洋", duration: "60 分钟", price: 280, capacity: 8, status: "已上架", remark: "" },
    { id: "P03", name: "产后修复训练", coach: "郑雪", duration: "60 分钟", price: 320, capacity: 6, status: "已上架", remark: "需提前评估" },
    { id: "P04", name: "搏击一对一", coach: "马涛", duration: "45 分钟", price: 260, capacity: 12, status: "已下架", remark: "" }
  ];

  const reservations = {
    G01: [
      { member: "王琳", phone: "13800000001", time: "2026-08-27 10:02", status: "已预约" },
      { member: "赵敏", phone: "13800000003", time: "2026-08-27 09:46", status: "已预约" },
      { member: "郑雪", phone: "13800000011", time: "2026-08-26 20:12", status: "已签到" }
    ],
    G02: [
      { member: "李强", phone: "13800000002", time: "2026-08-26 18:40", status: "已签到" },
      { member: "陈晨", phone: "13800000004", time: "2026-08-26 19:05", status: "冲突待处理" }
    ],
    G03: [
      { member: "郭磊", phone: "13800000012", time: "2026-08-27 11:20", status: "已预约" }
    ]
  };

  let activeType = "group";
  let page = 1;
  const pageSize = 8;
  let currentCourse = null;
  let currentReservationCourseId = null;
  const session = window.GymUI.getSession();
  const canManage = session && (session.role === "admin" || session.role === "reception");

  function getCurrentList() {
    return activeType === "group" ? groupCourses : privateCourses;
  }

  function getFilteredList() {
    const keyword = document.getElementById("course-keyword").value.trim().toLowerCase();
    const status = document.getElementById("course-status-filter").value;
    return getCurrentList().filter(function (item) {
      const matchKeyword = !keyword || item.name.toLowerCase().indexOf(keyword) >= 0 || item.coach.toLowerCase().indexOf(keyword) >= 0;
      const matchStatus = !status || item.status === status;
      return matchKeyword && matchStatus;
    });
  }

  function statusClass(status) {
    if (status === "已上架") {
      return "success";
    }
    if (status === "已满员") {
      return "warn";
    }
    return "muted";
  }

  function buildGroupActions(item) {
    if (canManage) {
      return "<button class=\"btn btn-secondary btn-sm\" data-action=\"reservations\" data-id=\"" + item.id + "\">预约名单</button>" +
        "<button class=\"btn btn-secondary btn-sm\" data-action=\"edit\" data-id=\"" + item.id + "\">编辑</button>" +
        "<button class=\"btn btn-secondary btn-sm\" data-action=\"toggle\" data-id=\"" + item.id + "\">" + (item.status === "已下架" ? "上架" : "下架") + "</button>" +
        "<button class=\"btn btn-danger btn-sm\" data-action=\"delete\" data-id=\"" + item.id + "\">删除</button>";
    }
    if (session && session.role === "coach") {
      return "<button class=\"btn btn-secondary btn-sm\" data-action=\"reservations\" data-id=\"" + item.id + "\">预约名单</button>";
    }
    return "<button class=\"btn btn-primary btn-sm\" data-action=\"book\" data-id=\"" + item.id + "\">预约</button>";
  }

  function buildPrivateActions(item) {
    if (canManage) {
      return "<button class=\"btn btn-secondary btn-sm\" data-action=\"edit\" data-id=\"" + item.id + "\">编辑</button>" +
        "<button class=\"btn btn-secondary btn-sm\" data-action=\"toggle\" data-id=\"" + item.id + "\">" + (item.status === "已下架" ? "上架" : "下架") + "</button>" +
        "<button class=\"btn btn-danger btn-sm\" data-action=\"delete\" data-id=\"" + item.id + "\">删除</button>";
    }
    if (session && session.role === "coach") {
      return "<button class=\"btn btn-secondary btn-sm\" data-action=\"reservations\" data-id=\"" + item.id + "\">预约名单</button>";
    }
    return "<button class=\"btn btn-primary btn-sm\" data-action=\"book\" data-id=\"" + item.id + "\">预约</button>";
  }

  function renderCourses() {
    const list = getFilteredList();
    document.getElementById("course-panel-title").textContent = activeType === "group" ? "公共团课" : "私教课程";
    document.getElementById("course-count").textContent = "共 " + list.length + " 条";
    const totalPages = Math.max(1, Math.ceil(list.length / pageSize));
    page = Math.min(page, totalPages);
    const start = (page - 1) * pageSize;
    const rows = list.slice(start, start + pageSize);

    const groupBody = document.getElementById("group-course-body");
    const privateBody = document.getElementById("private-course-body");
    document.getElementById("group-course-table").style.display = activeType === "group" ? "" : "none";
    document.getElementById("private-course-table").style.display = activeType === "private" ? "" : "none";

    if (activeType === "group") {
      groupBody.innerHTML = rows.length ? rows.map(function (item) {
        return "<tr>" +
          "<td>" + item.name + "</td>" +
          "<td>" + item.category + "</td>" +
          "<td>" + item.coach + "</td>" +
          "<td>" + item.time + "</td>" +
          "<td>" + item.duration + "</td>" +
          "<td>" + item.booked + " / " + item.max + "</td>" +
          "<td><span class=\"badge " + statusClass(item.status) + "\">" + item.status + "</span></td>" +
          "<td><div class=\"table-actions\">" +
            buildGroupActions(item) +
          "</div></td>" +
        "</tr>";
      }).join("") : "<tr><td colspan=\"8\">暂无符合条件的团课</td></tr>";
    } else {
      privateBody.innerHTML = rows.length ? rows.map(function (item) {
        return "<tr>" +
          "<td>" + item.name + "</td>" +
          "<td>" + item.coach + "</td>" +
          "<td>" + item.duration + "</td>" +
          "<td>¥ " + window.GymUI.formatMoney(item.price) + "</td>" +
          "<td>" + item.capacity + " 个名额</td>" +
          "<td><span class=\"badge " + statusClass(item.status) + "\">" + item.status + "</span></td>" +
          "<td><div class=\"table-actions\">" +
            buildPrivateActions(item) +
          "</div></td>" +
        "</tr>";
      }).join("") : "<tr><td colspan=\"7\">暂无符合条件的私教课</td></tr>";
    }

    window.GymUI.renderPagination("course-pagination", page, list.length, pageSize, function (nextPage) {
      page = nextPage;
      renderCourses();
    });
  }

  function findCourse(id) {
    return getCurrentList().find(function (item) {
      return item.id === id;
    });
  }

  function setCourseTypeFields(type) {
    document.getElementById("course-category-field").style.display = type === "group" ? "" : "none";
    document.getElementById("course-time-field").style.display = type === "group" ? "" : "none";
    document.getElementById("course-capacity-field").style.display = type === "group" ? "" : "none";
  }

  function openCourseModal(course) {
    currentCourse = course;
    document.getElementById("course-modal-title").textContent = course ? "编辑课程" : "新增课程";
    document.getElementById("course-id").value = course ? course.id : "";
    document.getElementById("course-name").value = course ? course.name : "";
    document.getElementById("course-category").value = course ? course.category || "瑜伽" : "瑜伽";
    document.getElementById("course-coach").value = course ? course.coach : "张昊";
    document.getElementById("course-duration").value = course ? course.duration.split(" ")[0] : "60";
    document.getElementById("course-time").value = course ? course.time || "" : "";
    document.getElementById("course-capacity").value = course ? (isGroup ? course.max : course.capacity) || "" : "";
    document.getElementById("course-price").value = course ? course.price : "";
    document.getElementById("course-status").value = course ? course.status === "已满员" ? "已上架" : course.status : "已上架";
    document.getElementById("course-remark").value = course ? course.remark || "" : "";
    setCourseTypeFields(activeType);
    window.GymUI.openModal("course-modal");
  }

  function saveCourse() {
    const id = document.getElementById("course-id").value;
    const isGroup = activeType === "group";
    const data = {
      name: document.getElementById("course-name").value.trim(),
      category: document.getElementById("course-category").value,
      coach: document.getElementById("course-coach").value,
      duration: document.getElementById("course-duration").value + " 分钟",
      time: document.getElementById("course-time").value.trim(),
      max: Number(document.getElementById("course-capacity").value || 0),
      price: Number(document.getElementById("course-price").value || 0),
      status: document.getElementById("course-status").value,
      remark: document.getElementById("course-remark").value.trim()
    };
    if (!data.name || !data.price) {
      window.GymUI.toast("请填写课程名称和价格", "warn");
      return;
    }
    if (id) {
      const list = getCurrentList();
      const index = list.findIndex(function (item) {
        return item.id === id;
      });
      if (index >= 0) {
        list[index] = Object.assign({}, list[index], data);
      }
      window.GymUI.toast("课程信息已更新");
    } else {
      const prefix = isGroup ? "G" : "P";
      const nextId = prefix + String(getCurrentList().length + 1).padStart(2, "0");
      const extra = isGroup ? { booked: 0 } : { capacity: Number(document.getElementById("course-capacity").value || 0) };
      getCurrentList().unshift(Object.assign({ id: nextId }, data, extra));
      window.GymUI.toast("课程已新增");
    }
    window.GymUI.closeModal("course-modal");
    renderCourses();
  }

  function openReservations(course) {
    currentReservationCourseId = course.id;
    document.getElementById("reservation-course-name").textContent = course.name;
    const list = reservations[course.id] || [];
    const total = list.length;
    const checked = list.filter(function (item) {
      return item.status === "已签到";
    }).length;
    const conflict = list.filter(function (item) {
      return item.status.indexOf("冲突") >= 0;
    }).length;
    document.getElementById("reservation-total").textContent = total;
    document.getElementById("reservation-checked").textContent = checked;
    document.getElementById("reservation-conflict").textContent = conflict;
    const body = document.getElementById("reservation-table-body");
    if (!list.length) {
      body.innerHTML = "<tr><td colspan=\"5\">暂无预约记录</td></tr>";
    } else {
      body.innerHTML = list.map(function (item, index) {
        const cls = item.status === "已签到" ? "success" : item.status.indexOf("冲突") >= 0 ? "danger" : "info";
        return "<tr>" +
          "<td>" + item.member + "</td>" +
          "<td>" + item.phone + "</td>" +
          "<td>" + item.time + "</td>" +
          "<td><span class=\"badge " + cls + "\">" + item.status + "</span></td>" +
          "<td><button class=\"btn btn-secondary btn-sm\" data-reservation-index=\"" + index + "\">处理</button></td>" +
        "</tr>";
      }).join("");
    }
    window.GymUI.openModal("reservation-modal");
  }

  function switchType(type) {
    activeType = type;
    page = 1;
    document.querySelectorAll("#course-tabs .tab-btn").forEach(function (btn) {
      btn.classList.toggle("active", btn.getAttribute("data-type") === type);
    });
    renderCourses();
  }

  document.addEventListener("DOMContentLoaded", function () {
    renderCourses();

    if (!canManage) {
      document.getElementById("add-course-btn").style.display = "none";
    }

    document.querySelectorAll("#course-tabs .tab-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        switchType(btn.getAttribute("data-type"));
      });
    });

    document.getElementById("add-course-btn").addEventListener("click", function () {
      openCourseModal(null);
    });
    document.getElementById("save-course-btn").addEventListener("click", saveCourse);

    document.getElementById("course-search-btn").addEventListener("click", function () {
      page = 1;
      renderCourses();
    });
    document.getElementById("course-reset-btn").addEventListener("click", function () {
      document.getElementById("course-keyword").value = "";
      document.getElementById("course-status-filter").value = "";
      page = 1;
      renderCourses();
    });

    document.getElementById("course-modal").addEventListener("click", function (event) {
      const btn = event.target.closest("[data-action]");
      if (!btn) {
        return;
      }
    });

    document.getElementById("group-course-body").addEventListener("click", handleTableAction);
    document.getElementById("private-course-body").addEventListener("click", handleTableAction);

    document.getElementById("reservation-table-body").addEventListener("click", function (event) {
      const btn = event.target.closest("[data-reservation-index]");
      if (!btn || !currentReservationCourseId) {
        return;
      }
      const list = reservations[currentReservationCourseId] || [];
      const item = list[Number(btn.getAttribute("data-reservation-index"))];
      if (!item) {
        return;
      }
      window.GymUI.toast("已处理 " + item.member + " 的预约记录");
    });
  });

  function handleTableAction(event) {
    const btn = event.target.closest("[data-action]");
    if (!btn) {
      return;
    }
    const course = findCourse(btn.getAttribute("data-id"));
    if (!course) {
      return;
    }
    const action = btn.getAttribute("data-action");
    if (action === "reservations") {
      openReservations(course);
    } else if (action === "book") {
      window.GymUI.toast("预约成功，可在会员个人中心查看");
    } else if (action === "edit") {
      openCourseModal(course);
    } else if (action === "toggle") {
      course.status = course.status === "已下架" ? "已上架" : "已下架";
      window.GymUI.toast(course.name + " 已" + course.status);
      renderCourses();
    } else if (action === "delete") {
      window.GymUI.confirmAction("确定删除课程 " + course.name + " 吗？", function () {
        const list = getCurrentList();
        const index = list.findIndex(function (item) {
          return item.id === course.id;
        });
        if (index >= 0) {
          list.splice(index, 1);
        }
        window.GymUI.toast("课程已删除");
        renderCourses();
      });
    }
  }
})();
