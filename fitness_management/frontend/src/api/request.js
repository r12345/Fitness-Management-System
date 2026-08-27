const BASE_URL = "/api";

export function request(path, options = {}) {
  const token = localStorage.getItem("gym_token");
  const headers = Object.assign({
    "Content-Type": "application/json"
  }, options.headers || {});
  if (token) {
    headers.Authorization = "Bearer " + token;
  }
  return fetch(BASE_URL + path, Object.assign({}, options, { headers })).then(async (response) => {
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || "请求失败");
    }
    return response.json();
  });
}
