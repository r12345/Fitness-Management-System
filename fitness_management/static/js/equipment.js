/* 器材管理页面演示脚本 */
(function () {
  "use strict";

  let equipment = [
    { id: "E01", name: "商用跑步机", model: "YJ-8000", category: "有氧器械", location: "有氧区 A1", purchaseDate: "2024-06-10", price: 12800, status: "正常", remark: "" },
    { id: "E02", name: "椭圆机", model: "BH-520", category: "有氧器械", location: "有氧区 A2", purchaseDate: "2024-06-10", price: 9600, status: "正常", remark: "" },
    { id: "E03", name: "动感单车", model: "SPIN-X", category: "有氧器械", location: "单车房 B1", purchaseDate: "2023-11-20", price: 4200, status: "维修", remark: "座椅异响" },
    { id: "E04", name: "卧推架", model: "Power-01", category: "力量器械", location: "力量区 C1", purchaseDate: "2023-08-15", price: 8800, status: "正常", remark: "" },
    { id: "E05", name: "深蹲架", model: "Power-02", category: "力量器械", location: "力量区 C2", purchaseDate: "2023-08-15", price: 9600, status: "正常", remark: "" },
    { id: "E06", name: "哑铃组", model: "DB-2.5-30", category: "自由重量", location: "自由力量区 D1", purchaseDate: "2022-03-01", price: 7600, status: "正常", remark: "" },
    { id: "E07", name: "杠铃片", model: "PL-20", category: "自由重量", location: "自由力量区 D2", purchaseDate: "2022-03-01", price: 3200, status: "报废", remark: "边缘破损" },
    { id: "E08", name: "瑜伽垫", model: "YJ-6MM", category: "瑜伽普拉提", location: "团课教室 E1", purchaseDate: "2025-02-18", price: 180, status: "正常", remark: "" },
    { id: "E09", name: "普拉提核心床", model: "PL-REFO", category: "瑜伽普拉提", location: "私教室 E2", purchaseDate: "2024-09-12", price: 15600, status: "正常", remark: "" },
    { id: "E10", name: "泡沫轴", model: "FA-45", category: "辅助器材", location: "拉伸区 F1", purchaseDate: "2025-05-08", price: 120, status: "正常", remark: "" },
    { id: "E11", name: "战绳", model: "BS-15M", category: "辅助器材", location: "训练区 F2", purchaseDate: "2023-10-05", price: 860, status: "维修", remark: "绳头开线" },
    { id: "E12", name: "划船机", model: "ROW-PRO", category: "有氧器械", location: "有氧区 A3", purchaseDate: "2024-12-20", price: 11200, status: "正常", remark: "" }
  ];

  let page = 1;
  const pageSize = 8;
  let currentEquipment = null;
  const session = window.GymUI.getSession();
  const canManage = session && session.role === "admin";

  function getFilteredList() {
    const keyword = document.getElementById("equipment-keyword").value.trim().toLowerCase();
    const status = document.getElementById("equipment-status-filter").value;
    const category = document.getElementById("equipment-category-filter").value;
    return equipment.filter(function (item) {
      const matchKeyword = !keyword ||
        item.name.toLowerCase().indexOf(keyword) >= 0 ||
        item.model.toLowerCase().indexOf(keyword) >= 0 ||
        item.location.toLowerCase().indexOf(keyword) >= 0;
      const matchStatus = !status || item.status === status;
      const matchCategory = !category || item.category === category;
      return matchKeyword && matchStatus && matchCategory;
    });
  }

  function statusClass(status) {
    if (status === "正常") {
      return "success";
    }
    if (status === "维修") {
      return "warn";
    }
    return "muted";
  }

  function buildEquipmentActions(item) {
    if (canManage) {
      return "<button class=\"btn btn-secondary btn-sm\" data-action=\"edit\" data-id=\"" + item.id + "\">编辑</button>" +
        "<button class=\"btn btn-secondary btn-sm\" data-action=\"repair\" data-id=\"" + item.id + "\">报修</button>" +
        "<button class=\"btn btn-secondary btn-sm\" data-action=\"maintenance\" data-id=\"" + item.id + "\">保养</button>" +
        "<button class=\"btn btn-danger btn-sm\" data-action=\"delete\" data-id=\"" + item.id + "\">删除</button>";
    }
    return "<button class=\"btn btn-secondary btn-sm\" data-action=\"repair\" data-id=\"" + item.id + "\">报修</button>" +
      "<button class=\"btn btn-secondary btn-sm\" data-action=\"maintenance\" data-id=\"" + item.id + "\">保养</button>";
  }

  function renderEquipment() {
    const list = getFilteredList();
    document.getElementById("equipment-count").textContent = "共 " + list.length + " 条";
    const totalPages = Math.max(1, Math.ceil(list.length / pageSize));
    page = Math.min(page, totalPages);
    const start = (page - 1) * pageSize;
    const rows = list.slice(start, start + pageSize);
    const body = document.getElementById("equipment-table-body");
    if (!rows.length) {
      body.innerHTML = "<tr><td colspan=\"8\">暂无符合条件的器材</td></tr>";
    } else {
      body.innerHTML = rows.map(function (item) {
        return "<tr>" +
          "<td>" + item.name + "</td>" +
          "<td>" + item.model + "</td>" +
          "<td>" + item.category + "</td>" +
          "<td>" + item.location + "</td>" +
          "<td>" + item.purchaseDate + "</td>" +
          "<td>¥ " + window.GymUI.formatMoney(item.price) + "</td>" +
          "<td><span class=\"badge " + statusClass(item.status) + "\">" + item.status + "</span></td>" +
          "<td><div class=\"table-actions\">" +
            buildEquipmentActions(item) +
          "</div></td>" +
        "</tr>";
      }).join("");
    }
    window.GymUI.renderPagination("equipment-pagination", page, list.length, pageSize, function (nextPage) {
      page = nextPage;
      renderEquipment();
    });
  }

  function findEquipment(id) {
    return equipment.find(function (item) {
      return item.id === id;
    });
  }

  function openEquipmentModal(item) {
    currentEquipment = item;
    document.getElementById("equipment-modal-title").textContent = item ? "编辑器材" : "新增器材";
    document.getElementById("equipment-id").value = item ? item.id : "";
    document.getElementById("equipment-name").value = item ? item.name : "";
    document.getElementById("equipment-model").value = item ? item.model : "";
    document.getElementById("equipment-category").value = item ? item.category : "有氧器械";
    document.getElementById("equipment-location").value = item ? item.location : "";
    document.getElementById("equipment-purchase-date").value = item ? item.purchaseDate : "";
    document.getElementById("equipment-price").value = item ? item.price : "";
    document.getElementById("equipment-status").value = item ? item.status : "正常";
    document.getElementById("equipment-remark").value = item ? item.remark || "" : "";
    window.GymUI.openModal("equipment-modal");
  }

  function saveEquipment() {
    const id = document.getElementById("equipment-id").value;
    const data = {
      name: document.getElementById("equipment-name").value.trim(),
      model: document.getElementById("equipment-model").value.trim(),
      category: document.getElementById("equipment-category").value,
      location: document.getElementById("equipment-location").value.trim(),
      purchaseDate: document.getElementById("equipment-purchase-date").value,
      price: Number(document.getElementById("equipment-price").value || 0),
      status: document.getElementById("equipment-status").value,
      remark: document.getElementById("equipment-remark").value.trim()
    };
    if (!data.name || !data.model) {
      window.GymUI.toast("请填写器材名称和型号", "warn");
      return;
    }
    if (id) {
      const index = equipment.findIndex(function (item) {
        return item.id === id;
      });
      if (index >= 0) {
        equipment[index] = Object.assign({}, equipment[index], data);
      }
      window.GymUI.toast("器材信息已更新");
    } else {
      const nextId = "E" + String(equipment.length + 1).padStart(2, "0");
      equipment.unshift(Object.assign({ id: nextId }, data));
      window.GymUI.toast("器材已新增");
    }
    window.GymUI.closeModal("equipment-modal");
    renderEquipment();
  }

  function openRepair(item) {
    currentEquipment = item;
    document.getElementById("repair-equipment-id").value = item.id;
    document.getElementById("repair-equipment-name").textContent = item.name;
    document.getElementById("repair-desc").value = "";
    document.getElementById("repair-cost").value = "";
    document.getElementById("repair-date").value = "";
    document.getElementById("repair-remark").value = "";
    window.GymUI.openModal("repair-modal");
  }

  function saveRepair() {
    if (!currentEquipment) {
      return;
    }
    const desc = document.getElementById("repair-desc").value.trim();
    const cost = Number(document.getElementById("repair-cost").value || 0);
    if (!desc) {
      window.GymUI.toast("请填写故障描述", "warn");
      return;
    }
    currentEquipment.status = "维修";
    window.GymUI.closeModal("repair-modal");
    window.GymUI.toast(currentEquipment.name + " 报修已登记");
    renderEquipment();
  }

  function openMaintenance(item) {
    currentEquipment = item;
    document.getElementById("maintenance-equipment-id").value = item.id;
    document.getElementById("maintenance-equipment-name").textContent = item.name;
    document.getElementById("maintenance-date").value = "";
    document.getElementById("maintenance-person").value = "";
    document.getElementById("maintenance-content").value = "";
    window.GymUI.openModal("maintenance-modal");
  }

  function saveMaintenance() {
    if (!currentEquipment) {
      return;
    }
    const date = document.getElementById("maintenance-date").value;
    const content = document.getElementById("maintenance-content").value.trim();
    if (!date || !content) {
      window.GymUI.toast("请填写保养时间和内容", "warn");
      return;
    }
    window.GymUI.closeModal("maintenance-modal");
    window.GymUI.toast(currentEquipment.name + " 保养记录已保存");
  }

  document.addEventListener("DOMContentLoaded", function () {
    renderEquipment();

    if (!canManage) {
      document.getElementById("add-equipment-btn").style.display = "none";
    }

    document.getElementById("add-equipment-btn").addEventListener("click", function () {
      openEquipmentModal(null);
    });
    document.getElementById("save-equipment-btn").addEventListener("click", saveEquipment);
    document.getElementById("save-repair-btn").addEventListener("click", saveRepair);
    document.getElementById("save-maintenance-btn").addEventListener("click", saveMaintenance);

    document.getElementById("equipment-search-btn").addEventListener("click", function () {
      page = 1;
      renderEquipment();
    });
    document.getElementById("equipment-reset-btn").addEventListener("click", function () {
      document.getElementById("equipment-keyword").value = "";
      document.getElementById("equipment-status-filter").value = "";
      document.getElementById("equipment-category-filter").value = "";
      page = 1;
      renderEquipment();
    });

    document.getElementById("equipment-table-body").addEventListener("click", function (event) {
      const btn = event.target.closest("[data-action]");
      if (!btn) {
        return;
      }
      const item = findEquipment(btn.getAttribute("data-id"));
      if (!item) {
        return;
      }
      const action = btn.getAttribute("data-action");
      if (action === "edit") {
        openEquipmentModal(item);
      } else if (action === "repair") {
        openRepair(item);
      } else if (action === "maintenance") {
        openMaintenance(item);
      } else if (action === "delete") {
        window.GymUI.confirmAction("确定删除器材 " + item.name + " 吗？", function () {
          equipment = equipment.filter(function (target) {
            return target.id !== item.id;
          });
          window.GymUI.toast("器材已删除");
          renderEquipment();
        });
      }
    });
  });
})();
