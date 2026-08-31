import {defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', ()=>{
  const token = ref('')
  const role = ref('')
  const role_name = ref('')

  function setToken(value){
    token.value = value
    localStorage.setItem('token', value)
  }
  function setRole(value){
    role.value = value
  }
  function setRoleName(value){
    role_name.value = value
  }
  function setUserInfo(value){
    userInfo.value = value
  }
  return {token, role,role_name,setRole,setRoleName, setToken, }
},{
  persist: true
}
)
