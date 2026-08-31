import request from "./request.js";

export function login(role, username, password) {
    return request({
      url: "/auth/login/",
      method: "post",
      data: {
        role,
        username,
        password
      }
    })
}