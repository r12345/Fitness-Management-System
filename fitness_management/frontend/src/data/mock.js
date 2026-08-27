export const dashboardData = {
  stats: [
    { label: "会员总数", value: "1286", unit: "人", tone: "" },
    { label: "本期新增会员", value: "42", unit: "人", tone: "" },
    { label: "过期会员", value: "18", unit: "人", tone: "warn" },
    { label: "本期营收", value: "86,420", unit: "元", tone: "" },
    { label: "课程预约量", value: "326", unit: "次", tone: "danger" }
  ],
  recentReservations: [
    { member: "王琳", course: "哈他瑜伽", time: "今天 19:30", status: "已预约" },
    { member: "李强", course: "燃脂有氧操", time: "明天 18:00", status: "已预约" },
    { member: "赵敏", course: "动感单车", time: "明天 20:00", status: "已签到" },
    { member: "陈晨", course: "一对一塑形", time: "后天 15:00", status: "已预约" }
  ],
  activity: [
    { user: "前台小周", content: "会员王琳续费季卡", time: "10:24" },
    { user: "教练张昊", content: "更新课程时间", time: "09:48" },
    { user: "超级管理员", content: "处理跑步机报修", time: "09:12" },
    { user: "前台小周", content: "新会员李强开卡", time: "08:36" }
  ]
};

export const receptionData = {
  stats: [
    { label: "今日开卡", value: "12", unit: "人" },
    { label: "待处理预约", value: "8", unit: "条" },
    { label: "待报修器材", value: "3", unit: "台" },
    { label: "今日消费", value: "8,640", unit: "元" }
  ],
  actions: [
    { title: "会员开卡续费", desc: "新增会员、卡种配置、续费与消费记录", path: "/members", badge: "办理中", tone: "success" },
    { title: "课程预约处理", desc: "查看预约、处理冲突、确认签到", path: "/courses", badge: "待处理 8", tone: "info" },
    { title: "器材报修登记", desc: "登记故障、跟进维修、记录保养", path: "/equipment", badge: "待报修 3", tone: "warn" }
  ],
  business: [
    { time: "10:24", type: "会员续费", target: "王琳", content: "续费季卡，金额 1280 元", status: "已完成" },
    { time: "09:48", type: "课程预约", target: "李强", content: "预约燃脂有氧操", status: "待确认" },
    { time: "09:12", type: "器材报修", target: "动感单车", content: "座椅异响，需维修", status: "处理中" },
    { time: "08:36", type: "会员开卡", target: "李强", content: "新办季卡，金额 1980 元", status: "已完成" }
  ]
};

export const members = [
  { id: "M1001", name: "王琳", phone: "13800000001", gender: "女", age: 29, cardType: "年卡", expire: "2027-08-20", balance: 1280, status: "正常" },
  { id: "M1002", name: "李强", phone: "13800000002", gender: "男", age: 34, cardType: "季卡", expire: "2026-11-12", balance: 680, status: "正常" },
  { id: "M1003", name: "赵敏", phone: "13800000003", gender: "女", age: 26, cardType: "月卡", expire: "2026-09-27", balance: 320, status: "正常" },
  { id: "M1004", name: "陈晨", phone: "13800000004", gender: "男", age: 41, cardType: "年卡", expire: "2027-03-15", balance: 2200, status: "正常" },
  { id: "M1005", name: "孙悦", phone: "13800000005", gender: "女", age: 23, cardType: "次卡", expire: "2026-12-01", balance: 0, status: "正常" },
  { id: "M1006", name: "刘洋", phone: "13800000006", gender: "男", age: 38, cardType: "月卡", expire: "2026-08-31", balance: 120, status: "过期" },
  { id: "M1007", name: "周琪", phone: "13800000007", gender: "女", age: 31, cardType: "季卡", expire: "2026-12-20", balance: 860, status: "暂停" },
  { id: "M1008", name: "王哲", phone: "13800000008", gender: "男", age: 28, cardType: "年卡", expire: "2027-06-10", balance: 1560, status: "正常" }
];

export const coaches = [
  { name: "张昊", phone: "13900000001", specialty: "增肌、减脂", status: "在职", hireDate: "2023-03-12", hours: 42, score: 4.9 },
  { name: "刘洋", phone: "13900000002", specialty: "瑜伽、普拉提", status: "在职", hireDate: "2022-09-05", hours: 38, score: 4.8 },
  { name: "周琪", phone: "13900000003", specialty: "瑜伽、减脂", status: "休假", hireDate: "2024-01-18", hours: 24, score: 4.7 },
  { name: "王哲", phone: "13900000004", specialty: "增肌、康复", status: "在职", hireDate: "2021-06-10", hours: 46, score: 4.9 },
  { name: "孙悦", phone: "13900000005", specialty: "搏击、减脂", status: "在职", hireDate: "2023-11-02", hours: 29, score: 4.6 },
  { name: "马涛", phone: "13900000007", specialty: "减脂、搏击", status: "在职", hireDate: "2024-05-16", hours: 31, score: 4.7 }
];

export const groupCourses = [
  { id: "G01", name: "哈他瑜伽", category: "瑜伽", coach: "刘洋", time: "周一 19:30", duration: "60 分钟", max: 20, booked: 16, status: "已上架" },
  { id: "G02", name: "燃脂有氧操", category: "有氧操", coach: "孙悦", time: "周三 18:00", duration: "60 分钟", max: 24, booked: 24, status: "已满员" },
  { id: "G03", name: "搏击基础课", category: "搏击操", coach: "马涛", time: "周五 20:00", duration: "60 分钟", max: 18, booked: 12, status: "已上架" },
  { id: "G04", name: "动感单车", category: "动感单车", coach: "王哲", time: "周二 20:00", duration: "45 分钟", max: 20, booked: 14, status: "已上架" }
];

export const privateCourses = [
  { id: "P01", name: "一对一塑形", coach: "张昊", duration: "60 分钟", price: 300, capacity: 10, status: "已上架" },
  { id: "P02", name: "普拉提体态调整", coach: "刘洋", duration: "60 分钟", price: 280, capacity: 8, status: "已上架" },
  { id: "P03", name: "产后修复训练", coach: "郑雪", duration: "60 分钟", price: 320, capacity: 6, status: "已上架" },
  { id: "P04", name: "搏击一对一", coach: "马涛", duration: "45 分钟", price: 260, capacity: 12, status: "已下架" }
];

export const equipment = [
  { name: "商用跑步机", model: "YJ-8000", category: "有氧器械", location: "有氧区 A1", purchaseDate: "2024-06-10", price: 12800, status: "正常" },
  { name: "椭圆机", model: "BH-520", category: "有氧器械", location: "有氧区 A2", purchaseDate: "2024-06-10", price: 9600, status: "正常" },
  { name: "动感单车", model: "SPIN-X", category: "有氧器械", location: "单车房 B1", purchaseDate: "2023-11-20", price: 4200, status: "维修" },
  { name: "卧推架", model: "Power-01", category: "力量器械", location: "力量区 C1", purchaseDate: "2023-08-15", price: 8800, status: "正常" },
  { name: "哑铃组", model: "DB-2.5-30", category: "自由重量", location: "自由力量区 D1", purchaseDate: "2022-03-01", price: 7600, status: "正常" },
  { name: "普拉提核心床", model: "PL-REFO", category: "瑜伽普拉提", location: "私教室 E2", purchaseDate: "2024-09-12", price: 15600, status: "正常" }
];

export const memberAppointments = [
  { course: "哈他瑜伽", time: "今天 19:30", coach: "刘洋", status: "已预约" },
  { course: "一对一塑形", time: "08月29日 15:00", coach: "张昊", status: "已预约" },
  { course: "燃脂有氧操", time: "08月24日 18:00", coach: "孙悦", status: "已完成" },
  { course: "肩颈放松瑜伽", time: "08月20日 10:00", coach: "郑雪", status: "已取消" }
];

export const trainingRecords = [
  { date: "2026-08-26", content: "肩背力量训练", weight: "45kg", duration: "83 分钟", fat: "21.8%" },
  { date: "2026-08-24", content: "瑜伽核心训练", weight: "自重", duration: "90 分钟", fat: "22.1%" },
  { date: "2026-08-22", content: "下肢力量训练", weight: "60kg", duration: "85 分钟", fat: "22.0%" }
];

export const coachSchedules = [
  { date: "2026-08-27", time: "09:00 - 10:00", course: "增肌基础课", location: "力量区 C1", booked: 8, status: "未开始" },
  { date: "2026-08-28", time: "19:00 - 20:00", course: "一对一塑形", location: "私教室 1", booked: 1, status: "已预约" },
  { date: "2026-08-29", time: "15:00 - 17:00", course: "肩颈力量训练", location: "团课教室 E1", booked: 12, status: "已预约" },
  { date: "2026-08-30", time: "10:00 - 11:00", course: "增肌基础课", location: "力量区 C1", booked: 6, status: "已签到" }
];

export const coachStudents = [
  { name: "王琳", phone: "13800000001", goal: "塑形", plan: "肩背训练计划", recent: "2026-08-26" },
  { name: "陈晨", phone: "13800000004", goal: "增肌", plan: "全身力量计划", recent: "2026-08-25" },
  { name: "郑雪", phone: "13800000011", goal: "减脂", plan: "核心燃脂计划", recent: "2026-08-24" }
];

export const coachPlans = [
  { student: "王琳", goal: "塑形", part: "肩背、核心", action: "哑铃划船、平板支撑", sets: "4 组 × 12 次", frequency: "每周 3 次" },
  { student: "陈晨", goal: "增肌", part: "胸、背、腿", action: "卧推、深蹲、硬拉", sets: "5 组 × 8 次", frequency: "每周 4 次" }
];
