/* 会员管理页面演示脚本 */
(function () {
  "use strict";

  let members = [
    { id: "M1001", name: "王琳", phone: "13800000001", gender: "女", age: 29, cardType: "年卡", expire: "2027-08-20", balance: 1280, status: "正常", remark: "偏好瑜伽课程" },
    { id: "M1002", name: "李强", phone: "13800000002", gender: "男", age: 34, cardType: "季卡", expire: "2026-11-12", balance: 680, status: "正常", remark: "" },
    { id: "M1003", name: "赵敏", phone: "13800000003", gender: "女", age: 26, cardType: "月卡", expire: "2026-09-27", balance: 320, status: "正常", remark: "预约需提前提醒" },
    { id: "M1004", name: "陈晨", phone: "13800000004", gender: "男", age: 41, cardType: "年卡", expire: "2027-03-15", balance: 2200, status: "正常", remark: "私教学员" },
    { id: "M1005", name: "孙悦", phone: "13800000005", gender: "女", age: 23, cardType: "次卡", expire: "2026-12-01", balance: 0, status: "正常", remark: "" },
    { id: "M1006", name: "刘洋", phone: "13800000006", gender: "男", age: 38, cardType: "月卡", expire: "2026-08-31", balance: 120, status: "过期", remark: "待续费" },
    { id: "M1007", name: "周琪", phone: "13800000007", gender: "女", age: 31, cardType: "季卡", expire: "2026-12-20", balance: 860, status: "暂停", remark: "出差暂停" },
    { id: "M1008", name: "王哲", phone: "13800000008", gender: "男", age: 28, cardType: "年卡", expire: "2027-06-10", balance: 1560, status: "正常", remark: "" },
    { id: "M1009", name: "何佳", phone: "13800000009", gender: "女", age: 36, cardType: "次卡", expire: "2026-09-15", balance: 0, status: "注销", remark: "已退款注销" },
    { id: "M1010", name: "马涛", phone: "13800000010", gender: "男", age: 45, cardType: "月卡", expire: "2026-09-03", balance: 0, status: "正常", remark: "" },
    { id: "M1011", name: "郑雪", phone: "13800000011", gender: "女", age: 27, cardType: "年卡", expire: "2027-01-18", balance: 980, status: "正常", remark: "搏击操爱好者" },
    { id: "M1012", name: "郭磊", phone: "13800000012", gender: "男", age: 33, cardType: "季卡", expire: "2026-12-09", balance: 540, status: "正常", remark: "" }
  ];

  let page = 1;
  const pageSize = 8;
  let currentMember = null;

  function getFilteredList() {
    const keyword = document.getElementById("keyword").value.trim().toLowerCase();
    const status = document.getElementById("status-filter").value;
    const cardType = document.getElementById("card-type-filter").value;
    return members.filter(function (item) {
      const matchKeyword = !keyword || item.name.toLowerCase().indexOf(keyword) >= 0 || item.phone.indexOf(keyword) >= 0;
      const matchStatus = !status || item.status === status;
      const matchCard = !cardType || item.cardType === cardType;
      return matchKeyword && matchStatus && matchCard;
    });
  }

  function statusClass(status) {
    if (status === "正常") {
      return "success";
    }
    if (status === "过期") {
      return "danger";
    }
    if (status === "暂停") {
      return "warn";
    }
    return "muted";
  }

  function renderMembers() {
    const list = getFilteredList();
    document.getElementById("member-count").textContent = "共 " + list.length + " 条";
    const totalPages = Math.max(1, Math.ceil(list.length / pageSize));
    page = Math.min(page, totalPages);
    const start = (page - 1) * pageSize;
    const rows = list.slice(start, start + pageSize);
    const body = document.getElementById("member-table-body");
    if (!rows.length) {
      body.innerHTML = "<tr><td colspan=\"10\">暂无符合条件的会员</td></tr>";
    } else {
      body.innerHTML = rows.map(function (item) {
        return "<tr>" +
          "<td>" + item.id + "</td>" +
          "<td>" + item.name + "</td>" +
          "<td>" + item.phone + "</td>" +
          "<td>" + item.gender + "</td>" +
          "<td>" + item.age + "</td>" +
          "<td>" + item.cardType + "</td>" +
          "<td>" + item.expire + "</td>" +
          "<td>¥ " + window.GymUI.formatMoney(item.balance) + "</td>" +
          "<td><span class=\"badge " + statusClass(item.status) + "\">" + item.status + "</span></td>" +
          "<td><div class=\"table-actions\">" +
            "<button class=\"btn btn-secondary btn-sm\" data-action=\"detail\" data-id=\"" + item.id + "\">详情</button>" +
            "<button class=\"btn btn-secondary btn-sm\" data-action=\"edit\" data-id=\"" + item.id + "\">编辑</button>" +
            "<button class=\"btn btn-secondary btn-sm\" data-action=\"renew\" data-id=\"" + item.id + "\">续费</button>" +
            "<button class=\"btn btn-danger btn-sm\" data-action=\"delete\" data-id=\"" + item.id + "\">删除</button>" +
          "</div></td>" +
        "</tr>";
      }).join("");
    }
    window.GymUI.renderPagination("member-pagination", page, list.length, pageSize, function (nextPage) {
      page = nextPage;
      renderMembers();
    });
  }

  function findMember(id) {
    return members.find(function (item) {
      return item.id === id;
    });
  }

  function openMemberModal(member) {
    currentMember = member;
    document.getElementById("member-modal-title").textContent = member ? "编辑会员" : "新增会员";
    document.getElementById("member-id").value = member ? member.id : "";
    document.getElementById("member-name").value = member ? member.name : "";
    document.getElementById("member-phone").value = member ? member.phone : "";
    document.getElementById("member-gender").value = member ? member.gender : "男";
    document.getElementById("member-age").value = member ? member.age : "";
    document.getElementById("member-card-type").value = member ? member.cardType : "月卡";
    document.getElementById("member-expire").value = member ? member.expire : "";
    document.getElementById("member-balance").value = member ? member.balance : "";
    document.getElementById("member-status").value = member ? member.status : "正常";
    document.getElementById("member-remark").value = member ? member.remark || "" : "";
    window.GymUI.openModal("member-modal");
  }

  function saveMember() {
    const id = document.getElementById("member-id").value;
    const data = {
      name: document.getElementById("member-name").value.trim(),
      phone: document.getElementById("member-phone").value.trim(),
      gender: document.getElementById("member-gender").value,
      age: Number(document.getElementById("member-age").value),
      cardType: document.getElementById("member-card-type").value,
      expire: document.getElementById("member-expire").value,
      balance: Number(document.getElementById("member-balance").value || 0),
      status: document.getElementById("member-status").value,
      remark: document.getElementById("member-remark").value.trim()
    };
    if (!data.name || !data.phone || !data.expire) {
      window.GymUI.toast("请完整填写姓名、手机号和到期时间", "warn");
      return;
    }
    if (id) {
      const index = members.findIndex(function (item) {
        return item.id === id;
      });
      if (index >= 0) {
        members[index] = Object.assign({}, members[index], data);
      }
      window.GymUI.toast("会员信息已更新");
    } else {
      const nextId = "M" + (1013 + members.length);
      members.unshift(Object.assign({ id: nextId }, data));
      window.GymUI.toast("新会员已创建");
    }
    window.GymUI.closeModal("member-modal");
    renderMembers();
  }

  function openRenew(member) {
    document.getElementById("renew-member-id").value = member.id;
    document.getElementById("renew-member-name").value = member.name;
    document.getElementById("renew-current-expire").value = member.expire;
    document.getElementById("renew-duration").value = "3";
    document.getElementById("renew-amount").value = "";
    document.getElementById("renew-remark").value = "";
    window.GymUI.openModal("renew-modal");
  }

  function saveRenew() {
    const id = document.getElementById("renew-member-id").value;
    const member = findMember(id);
    if (!member) {
      return;
    }
    const months = Number(document.getElementById("renew-duration").value);
    const amount = Number(document.getElementById("renew-amount").value || 0);
    if (amount <= 0) {
      window.GymUI.toast("请输入有效续费金额", "warn");
      return;
    }
    const base = new Date(member.expire);
    if (isNaN(base.getTime()) || base < new Date()) {
      base.setTime(Date.now());
    }
    base.setMonth(base.getMonth() + months);
    member.expire = base.toISOString().slice(0, 10);
    member.balance = Number(member.balance || 0) + amount;
    member.status = "正常";
    window.GymUI.closeModal("renew-modal");
    window.GymUI.toast(member.name + " 续费成功");
    renderMembers();
  }

  const detailData = {
    card: [
      { type: "年卡", start: "2025-08-20", expire: "2026-08-20", amount: "2880", operator: "前台小周" },
      { type: "年卡续费", start: "2026-08-20", expire: "2027-08-20", amount: "2880", operator: "前台小周" }
    ],
    consume: [
      { item: "年卡续费", amount: "2880.00", time: "2026-08-20 10:20", pay: "微信" },
      { item: "私教课 10 节", amount: "3000.00", time: "2026-07-18 16:30", pay: "支付宝" },
      { item: "运动饮品", amount: "18.00", time: "2026-08-19 20:10", pay: "余额" }
    ],
    reserve: [
      { course: "哈他瑜伽", time: "2026-08-27 19:30", coach: "周琪", status: "已预约" },
      { course: "肩颈放松私教", time: "2026-08-29 15:00", coach: "张昊", status: "已完成" }
    ],
    checkin: [
      { date: "2026-08-26", in: "18:42", out: "20:05", duration: "83 分钟" },
      { date: "2026-08-24", in: "19:10", out: "20:40", duration: "90 分钟" },
      { date: "2026-08-22", in: "18:30", out: "19:55", duration: "85 分钟" }
    ]
  };

  function renderDetailList(containerId, list, columns) {
    const container = document.getElementById(containerId);
    container.innerHTML = list.map(function (item) {
      return "<tr>" + columns.map(function (key) {
        return "<td>" + item[key] + "</td>";
      }).join("") + "</tr>";
    }).join("");
  }

  function openDetail(member) {
    document.getElementById("detail-avatar").textContent = member.name.slice(0, 1);
    document.getElementById("detail-name").textContent = member.name;
    document.getElementById("detail-phone").textContent = member.phone;
    document.getElementById("detail-card-type").textContent = member.cardType;
    const statusEl = document.getElementById("detail-status");
    statusEl.textContent = member.status;
    statusEl.className = "badge " + statusClass(member.status);

    renderDetailList("detail-card-list", detailData.card, ["type", "start", "expire", "amount", "operator"]);
    renderDetailList("detail-consume-list", detailData.consume, ["item", "amount", "time", "pay"]);
    renderDetailList("detail-reserve-list", detailData.reserve, ["course", "time", "coach", "status"]);
    renderDetailList("detail-checkin-list", detailData.checkin, ["date", "in", "out", "duration"]);

    document.querySelectorAll("#detail-tabs .tab-btn").forEach(function (btn, index) {
      btn.classList.toggle("active", index === 0);
    });
    document.querySelectorAll("#member-detail-modal .tab-content").forEach(function (content, index) {
      content.classList.toggle("active", index === 0);
    });
    window.GymUI.openModal("member-detail-modal");
  }

  document.addEventListener("DOMContentLoaded", function () {
    renderMembers();

    document.getElementById("add-member-btn").addEventListener("click", function () {
      openMemberModal(null);
    });

    document.getElementById("save-member-btn").addEventListener("click", saveMember);
    document.getElementById("save-renew-btn").addEventListener("click", saveRenew);

    document.getElementById("search-btn").addEventListener("click", function () {
      page = 1;
      renderMembers();
    });

    document.getElementById("reset-btn").addEventListener("click", function () {
      document.getElementById("keyword").value = "";
      document.getElementById("status-filter").value = "";
      document.getElementById("card-type-filter").value = "";
      page = 1;
      renderMembers();
    });

    document.getElementById("export-btn").addEventListener("click", function () {
      window.GymUI.toast("演示环境暂不执行导出");
    });

    document.getElementById("member-table-body").addEventListener("click", function (event) {
      const btn = event.target.closest("[data-action]");
      if (!btn) {
        return;
      }
      const member = findMember(btn.getAttribute("data-id"));
      if (!member) {
        return;
      }
      const action = btn.getAttribute("data-action");
      if (action === "detail") {
        openDetail(member);
      } else if (action === "edit") {
        openMemberModal(member);
      } else if (action === "renew") {
        openRenew(member);
      } else if (action === "delete") {
        window.GymUI.confirmAction("确定删除会员 " + member.name + " 吗？", function () {
          members = members.filter(function (item) {
            return item.id !== member.id;
          });
          window.GymUI.toast("会员已删除");
          renderMembers();
        });
      }
    });

    document.querySelectorAll("#detail-tabs .tab-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const key = btn.getAttribute("data-tab");
        document.querySelectorAll("#detail-tabs .tab-btn").forEach(function (item) {
          item.classList.toggle("active", item === btn);
        });
        document.querySelectorAll("#member-detail-modal .tab-content").forEach(function (content) {
          content.classList.toggle("active", content.id === "tab-" + key);
        });
      });
    });
  });
})();
