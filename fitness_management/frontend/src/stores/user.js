import {defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('users', ()=>{
  const token = ref('')
  const role = ref('')
  const role_name = ref('')
  const user_id = ref(null)
  const role_id = ref(null)

  function set_role_id(value){
    role_id.value = value
  }
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
  function setUserId(value){
    user_id.value = value
  }
  return {token, role,role_name,role_id,setRole,setRoleName, setToken,setUserId ,set_role_id}
},{
  persist: true
}
)
