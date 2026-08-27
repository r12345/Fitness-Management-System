/* 登录页演示交互，使用 Vue2 基础能力 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    const session = window.GymUI.getSession();
    if (session) {
      const config = window.GymUI.getRoleConfig(session.role);
      if (config) {
        window.location.replace(config.home);
        return;
      }
    }

    if (!window.Vue) {
      window.GymUI.toast("Vue2 未加载，请检查网络后刷新", "error");
      return;
    }

    new window.Vue({
      el: "#login-app",
      data: {
        roles: [
          { value: "admin", label: "超级管理员", icon: "管", desc: "全模块运营与权限管理" },
          { value: "reception", label: "前台运营", icon: "前", desc: "开卡、续费、预约与报修" },
          { value: "coach", label: "健身教练", icon: "教", desc: "排课、学员与训练计划" },
          { value: "member", label: "普通会员", icon: "会", desc: "预约、打卡与训练记录" }
        ],
        form: {
          role: "admin",
          username: "",
          password: ""
        },
        loading: false,
        notice: sessionStorage.getItem("gym_login_notice") || ""
      },
      computed: {
        currentRoleTip: function () {
          const current = this.roles.find(function (item) {
            return item.value === this.form.role;
          }, this);
          return current ? "当前选择：" + current.label + "，" + current.desc : "";
        }
      },
      methods: {
        selectRole: function (role) {
          this.form.role = role;
        },
        handleLogin: function () {
          if (this.loading) {
            return;
          }
          const username = this.form.username.trim();
          const password = this.form.password.trim();
          if (!username || !password) {
            window.GymUI.toast("请输入账号和密码", "warn");
            return;
          }
          if (username !== "admin" || password !== "123456") {
            window.GymUI.toast("账号或密码错误，请重新输入", "error");
            return;
          }

          const config = window.GymUI.getRoleConfig(this.form.role);
          const avatarText = this.form.role === "member" || this.form.role === "coach"
            ? username.slice(0, 1)
            : config.avatar;

          this.loading = true;
          window.GymUI.login(this.form.role, username, avatarText);
          sessionStorage.removeItem("gym_login_notice");
          window.GymUI.toast("登录成功，正在进入" + config.name);
          window.setTimeout(function () {
            window.location.href = config.home;
          }, 420);
        }
      }
    });
  });
})();
