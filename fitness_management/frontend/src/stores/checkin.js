import {defineStore } from 'pinia'
import {reactive, ref} from 'vue'
export const useCheckinStore = defineStore('checkin', () => {
    const checkin_time = ref(null)
    const leave_time = ref(null)
    const checkin_info = reactive({
  checkin_id: null,
  checkin_time: ''
})
    function checkin() {
        // checkin
        checkin_time.value = new Date()
        checkin_time.value.setHours(checkin_time.value.getHours() + 8)
        leave_time.value = null
    }
    function leave() {
        leave_time.value = new Date()
        leave_time.value.setHours(leave_time.value.getHours() + 8)
        checkin_time.value = null
    }

    function get_checkin_info(data){
        checkin_info.checkin_id = data.checkin_id
        checkin_info.checkin_time = data.checkin_time
    }
    return {
        checkin_time,
        leave_time,
        checkin,
        leave,
        get_checkin_info,
        checkin_info
    }
})