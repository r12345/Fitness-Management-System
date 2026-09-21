import {defineStore } from 'pinia'
import {reactive, ref} from 'vue'

/** 本地时区的 "YYYY-MM-DD HH:mm:ss"。后端 DATETIME 列存的就是墙上时间，
    直接送 Date 对象会被 axios 转成 UTC ISO 串，早先靠 setHours(+8) 硬凑，
    浏览器一旦不在东八区就会偏 8 小时。 */
function nowLocalText() {
    const d = new Date()
    const pad = (n) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ` +
        `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

export const useCheckinStore = defineStore('checkin', () => {
    /** 是否已到店（库里还留着一条未离店的打卡记录）。

        必须存「后端状态」而不是纯内存标志：只放内存里的话，页面一刷新就丢，
        按钮会从「离店打卡」倒回「到店打卡」；再点一下「到店打卡」又会插入一条
        永远不闭合的新记录，只能靠手动离店才收得住。 */
    const checked_in = ref(false)
    // 下面两个只是提交接口时用的时间戳，不参与按钮显示
    const checkin_time = ref(null)
    const leave_time = ref(null)
    const checkin_info = reactive({
        checkin_id: null,
        checkin_date: '',
        checkin_time: ''
    })

    function checkin() {
        // 到店：只生成时间戳，真实状态等接口回来后由 set_checkin_state 覆盖
        checkin_time.value = nowLocalText()
        leave_time.value = null
    }

    function leave() {
        // 离店：只生成时间戳
        leave_time.value = nowLocalText()
    }

    /** 用 GET /training/checkin/current 的结果覆盖本地状态（刷新后恢复按钮就靠它） */
    function set_checkin_state(data) {
        checked_in.value = !!(data && data.checked_in)
        checkin_info.checkin_id = data?.checkin_id ?? null
        checkin_info.checkin_date = data?.checkin_date ?? ''
        checkin_info.checkin_time = data?.checkin_time ?? ''
        if (!checked_in.value) {
            checkin_time.value = null
            leave_time.value = null
        }
    }

    return {
        checked_in,
        checkin_time,
        leave_time,
        checkin,
        leave,
        set_checkin_state,
        checkin_info
    }
})
