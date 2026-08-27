/* 通用前端交互与角色会话工具 */
(function () {
  "use strict";

  const ToastContainerId = "gym-toast-container";
  const SessionKey = "gym_session";

  const ROLE_CONFIG = {
    admin: { name: "超级管理员", home: "index.html", avatar: "管" },
    reception: { name: "前台运营", home: "reception.html", avatar: "前" },
    coach: { name: "健身教练", home: "coach_panel.html", avatar: "教" },
    member: { name: "普通会员", home: "member_center.html", avatar: "会" }
  };

  const PAGE_ROLES = {
    index: ["admin", "reception"],
    members: ["admin", "reception"],
    coaches: ["admin"],
    courses: ["admin", "reception", "coach", "member"],
    equipment: ["admin", "reception"],
    reception: ["admin", "reception"],
    system: ["admin"],
    member_center: ["admin", "member"],
    coach_panel: ["admin", "coach"]
  };

  const HREF_PAGE = {
    "index.html": "index",
    "members.html": "members",
    "coaches.html": "coaches",
    "courses.html": "courses",
    "equipment.html": "equipment",
    "reception.html": "reception",
    "system.html": "system",
    "member_center.html": "member_center",
    "coach_panel.html": "coach_panel"
  };

  const ROLE_MODULE_NAMES = {
    admin: {
      index: "数据大盘",
      members: "会员管理",
      coaches: "教练管理",
      courses: "课程与预约",
      equipment: "器材管理",
      system: "系统配置",
      reception: "前台运营工作台"
    },
    reception: {
      index: "运营概览",
      members: "会员开卡续费",
      coaches: "教练管理",
      courses: "预约处理",
      equipment: "器材报修",
      system: "系统配置",
      reception: "前台运营工作台"
    },
    coach: {
      courses: "课程中心"
    },
    member: {
      courses: "预约课程"
    }
  };

  const ROLE_PAGE_TEXT = {
    admin: {
      index: { title: "数据大盘", desc: "查看场馆核心运营指标与近期业务动态。" },
      members: { title: "会员管理", desc: "维护会员档案、办卡续费、消费记录和会员明细。" },
      courses: { title: "课程与预约", desc: "维护公共团课、私教课程和会员预约记录。" },
      equipment: { title: "器材管理", desc: "维护器材档案、报修维修、盘点和保养记录。" },
      system: { title: "系统配置", desc: "维护健身房基础信息、系统日志和字典配置。" }
    },
    reception: {
      index: { title: "运营概览", desc: "查看今日开卡、预约、消费和报修动态。" },
      members: { title: "会员开卡续费", desc: "办理会员开卡、续费，查询消费流水和会员详情。" },
      courses: { title: "预约处理", desc: "处理课程预约、取消预约和会员签到。" },
      equipment: { title: "器材报修", desc: "登记器材报修，跟进维修状态和保养记录。" }
    },
    coach: {
      courses: { title: "课程中心", desc: "查看课程信息、预约人数和授课安排。" }
    },
    member: {
      courses: { title: "预约课程", desc: "浏览可预约课程并管理自己的预约。" }
    }
  };

  function ensureToastContainer() {
    let container = document.getElementById(ToastContainerId);
    if (!container) {
      container = document.createElement("div");
      container.id = ToastContainerId;
      container.className = "toast-container";
      document.body.appendChild(container);
    }
    return container;
  }

  /* 统一提示 */
  function toast(message, type) {
    const container = ensureToastContainer();
    const item = document.createElement("div");
    item.className = "toast " + (type || "success");
    item.textContent = message;
    container.appendChild(item);
    window.setTimeout(function () {
      item.remove();
    }, 2800);
  }

  /* 打开和关闭弹窗 */
  function openModal(id) {
    const mask = document.getElementById(id);
    if (mask) {
      mask.classList.add("open");
    }
  }

  function closeModal(id) {
    const mask = document.getElementById(id);
    if (mask) {
      mask.classList.remove("open");
    }
  }

  /* 关闭确认弹窗并执行回调 */
  function confirmAction(message, callback) {
    const confirmBox = document.getElementById("confirm-modal");
    const textEl = document.getElementById("confirm-message");
    if (!confirmBox || !textEl) {
      if (window.confirm(message)) {
        callback();
      }
      return;
    }
    textEl.textContent = message;
    openModal("confirm-modal");
    const okBtn = document.getElementById("confirm-ok");
    const cancelBtn = document.getElementById("confirm-cancel");
    const cleanup = function () {
      okBtn.removeEventListener("click", handleOk);
      cancelBtn.removeEventListener("click", handleCancel);
    };
    const handleOk = function () {
      cleanup();
      closeModal("confirm-modal");
      callback();
    };
    const handleCancel = function () {
      cleanup();
      closeModal("confirm-modal");
    };
    okBtn.addEventListener("click", handleOk);
    cancelBtn.addEventListener("click", handleCancel);
  }

  /* 会话读写 */
  function getSession() {
    try {
      const value = localStorage.getItem(SessionKey);
      return value ? JSON.parse(value) : null;
    } catch (error) {
      return null;
    }
  }

  function getRoleConfig(role) {
    return ROLE_CONFIG[role] || null;
  }

  function login(role, username, avatarText) {
    const config = getRoleConfig(role);
    const session = {
      role: role,
      roleName: config ? config.name : "用户",
      username: username || "用户",
      avatarText: avatarText || (config ? config.avatar : "用"),
      loginAt: new Date().toISOString()
    };
    localStorage.setItem(SessionKey, JSON.stringify(session));
    return session;
  }

  function logout() {
    localStorage.removeItem(SessionKey);
    window.location.replace("login.html");
  }

  /* 按当前角色限制页面访问 */
  function guardPage() {
    const page = document.body.getAttribute("data-page");
    if (!page || page === "login") {
      return;
    }
    const allowed = PAGE_ROLES[page];
    if (!allowed) {
      return;
    }
    const session = getSession();
    if (!session) {
      window.location.replace("login.html");
      return;
    }
    if (allowed.indexOf(session.role) < 0) {
      localStorage.removeItem(SessionKey);
      sessionStorage.setItem("gym_login_notice", "当前角色无权访问该页面，请退出后重新登录");
      window.location.replace("login.html");
    }
  }

  /* 顶部用户信息 */
  function renderUserChip() {
    const session = getSession();
    if (!session) {
      return;
    }
    const avatarText = session.avatarText || (session.username || session.roleName || "用").slice(0, 1);
    document.querySelectorAll(".user-avatar").forEach(function (el) {
      el.textContent = avatarText;
    });
    const roleText = session.role === "member" || session.role === "coach"
      ? session.username + " · " + session.roleName
      : session.roleName;
    document.querySelectorAll(".user-chip-name").forEach(function (el) {
      el.textContent = roleText;
    });
    document.querySelectorAll(".user-chip span:not(.user-avatar):not(.user-chip-name)").forEach(function (el) {
      el.textContent = roleText;
    });
  }

  /* 隐藏当前角色不可访问的导航入口 */
  function applyRoleNav() {
    const session = getSession();
    if (!session) {
      return;
    }
    document.querySelectorAll(".nav-link").forEach(function (link) {
      const href = link.getAttribute("href") || "";
      const page = HREF_PAGE[href];
      const allowed = page ? PAGE_ROLES[page] : null;
      if (allowed && allowed.indexOf(session.role) < 0) {
        link.style.display = "none";
      }
      const labels = ROLE_MODULE_NAMES[session.role];
      if (labels && page && labels[page]) {
        link.textContent = labels[page];
      }
    });
    document.querySelectorAll(".nav-section").forEach(function (section) {
      const links = section.querySelectorAll(".nav-link");
      const visible = Array.prototype.some.call(links, function (link) {
        return link.style.display !== "none";
      });
      if (links.length && !visible) {
        section.style.display = "none";
      }
    });
  }

  /* 按角色替换页面标题与说明 */
  function setRolePageText() {
    const session = getSession();
    if (!session) {
      return;
    }
    const page = document.body.getAttribute("data-page");
    const text = ROLE_PAGE_TEXT[session.role] && ROLE_PAGE_TEXT[session.role][page];
    if (!text) {
      return;
    }
    document.querySelectorAll("[data-dynamic-title]").forEach(function (el) {
      el.textContent = text.title;
    });
    document.querySelectorAll("[data-dynamic-desc]").forEach(function (el) {
      el.textContent = text.desc;
    });
  }

  /* 初始化当前日期与导航状态 */
  function initCommon() {
    guardPage();
    renderUserChip();
    applyRoleNav();
    setRolePageText();

    const page = document.body.getAttribute("data-page") || "";
    const navLinks = document.querySelectorAll(".nav-link");
    navLinks.forEach(function (link) {
      const target = link.getAttribute("data-page");
      if (target && target === page) {
        link.classList.add("active");
      }
    });

    const now = new Date();
    const yearText = now.getFullYear() + "年";
    document.querySelectorAll("[data-current-year]").forEach(function (el) {
      el.textContent = yearText;
    });
    document.querySelectorAll("[data-current-date]").forEach(function (el) {
      el.textContent = now.toLocaleDateString("zh-CN");
    });

    const menuBtn = document.getElementById("mobile-menu-btn");
    const sidebar = document.getElementById("sidebar");
    if (menuBtn && sidebar) {
      menuBtn.addEventListener("click", function () {
        sidebar.classList.toggle("open");
      });
    }

    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", function () {
        logout();
      });
    }

    document.querySelectorAll(".modal-mask").forEach(function (mask) {
      mask.addEventListener("click", function (event) {
        if (event.target === mask) {
          mask.classList.remove("open");
        }
      });
    });

    document.querySelectorAll("[data-close-modal]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const target = btn.getAttribute("data-close-modal");
        closeModal(target);
      });
    });

    if (window.lucide) {
      window.lucide.createIcons();
    }
  }

  /* 数值格式化 */
  function formatMoney(value) {
    return Number(value || 0).toLocaleString("zh-CN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  /* 简易分页渲染 */
  function renderPagination(containerId, page, total, pageSize, callback) {
    const container = document.getElementById(containerId);
    if (!container) {
      return;
    }
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    const current = Math.min(page, totalPages);
    const start = (current - 1) * pageSize + 1;
    const end = Math.min(current * pageSize, total);
    container.innerHTML = "";

    const info = document.createElement("span");
    info.className = "pagination-info";
    info.textContent = "第 " + current + " / " + totalPages + " 页，共 " + total + " 条";
    container.appendChild(info);

    const pages = document.createElement("div");
    pages.className = "pagination-pages";

    const prevBtn = document.createElement("button");
    prevBtn.type = "button";
    prevBtn.className = "page-btn";
    prevBtn.textContent = "上一页";
    prevBtn.disabled = current <= 1;
    prevBtn.addEventListener("click", function () {
      callback(current - 1);
    });
    pages.appendChild(prevBtn);

    for (let i = 1; i <= totalPages; i += 1) {
      if (totalPages > 7 && i > 2 && i < totalPages - 1 && Math.abs(i - current) > 1) {
        continue;
      }
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "page-btn" + (i === current ? " active" : "");
      btn.textContent = String(i);
      btn.addEventListener("click", function () {
        callback(i);
      });
      pages.appendChild(btn);
    }

    const nextBtn = document.createElement("button");
    nextBtn.type = "button";
    nextBtn.className = "page-btn";
    nextBtn.textContent = "下一页";
    nextBtn.disabled = current >= totalPages;
    nextBtn.addEventListener("click", function () {
      callback(current + 1);
    });
    pages.appendChild(nextBtn);

    container.appendChild(pages);
  }

  /* 把数值转成带单位的显示文本 */
  function numberWithUnit(value, unit) {
    return Number(value || 0) + (unit || "");
  }

  window.GymUI = {
    toast: toast,
    openModal: openModal,
    closeModal: closeModal,
    confirmAction: confirmAction,
    initCommon: initCommon,
    formatMoney: formatMoney,
    renderPagination: renderPagination,
    numberWithUnit: numberWithUnit,
    getSession: getSession,
    getRoleConfig: getRoleConfig,
    login: login,
    logout: logout
  };

  document.addEventListener("DOMContentLoaded", initCommon);
})();
