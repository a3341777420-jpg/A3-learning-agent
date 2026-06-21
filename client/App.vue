<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import {
  BookOpen,
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  FileText,
  Flame,
  GraduationCap,
  Home,
  Languages,
  Lightbulb,
  ListChecks,
  Map,
  MessageCircle,
  PenLine,
  PlayCircle,
  RefreshCw,
  Send,
  ShieldCheck,
  Sparkles,
  UserRound
} from 'lucide-vue-next'

const API_BASE = 'http://127.0.0.1:8000'
const stage = ref('register')
const active = ref('home')
const loading = ref(false)
const error = ref('')
const captcha = reactive({ id: '', code: '' })
const registerForm = reactive({ nickname: '林同学', phone: '13800000000', password: '123456' })
const loginForm = reactive({ nickname: '林同学', phone: '13800000000', password: '123456', captchaCode: '' })
const intakeForm = reactive({ major: '计算机科学与技术', grade: '大二', daily_hours: 1 })
const learningOptions = [
  '大学英语四级',
  '大学英语六级',
  '雅思 IELTS',
  '托福 TOEFL',
  '考研英语',
  '商务英语',
  '学术写作',
  '英语口语',
  '听力提升',
  '阅读提速'
]
const selectedGoals = ref(['大学英语六级', '阅读提速', '学术写作'])
const quizQuestions = ref([])
const quizAnswers = reactive({})
const userId = ref(localStorage.getItem('english_learning_user_id') || '')
const user = reactive({ nickname: '', major: '', grade: '', goal: '', course: '', daily_hours: 0, onboarded: false })
const profile = reactive({ knowledge: '', weakness: '', style: '', pace: '', mistakes: '', goal: '' })
const summary = reactive({ level: '', score: 0, skill_scores: {}, weak_skills: [], summary_lines: [] })
const messages = ref([])
const todayTasks = ref([])
const resources = ref([])
const path = ref([])
const performance = ref([])
const safetyChecks = ref([])
const practice = reactive({ question: '', prompt: '', answer: '', result: '' })
const chatInput = ref('我阅读定位比较慢，写作句式也比较单一。')

const navItems = [
  { id: 'home', label: '今日学习', icon: Home },
  { id: 'chat', label: 'AI 导师', icon: MessageCircle },
  { id: 'path', label: '学习路径', icon: Map },
  { id: 'resources', label: '资源库', icon: BookOpen },
  { id: 'practice', label: '练习评测', icon: ListChecks },
  { id: 'profile', label: '学习画像', icon: UserRound }
]

const iconMap = {
  课程讲解文档: FileText,
  知识点思维导图: BrainCircuit,
  练习题库: ListChecks,
  写作实操案例: PenLine,
  多模态教学脚本: PlayCircle,
  个性化词汇表: Languages
}

const completion = computed(() => {
  if (!todayTasks.value.length) return 0
  return Math.round((todayTasks.value.filter((item) => item.done).length / todayTasks.value.length) * 100)
})

async function request(path, options = {}) {
  error.value = ''
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options
  })
  if (!res.ok) {
    let message = await res.text()
    try {
      message = JSON.parse(message).detail || message
    } catch {}
    throw new Error(message)
  }
  return res.json()
}

function applyState(data) {
  if (!data) return
  Object.assign(user, data.user || {})
  Object.assign(profile, data.profile || {})
  Object.assign(summary, data.summary || {})
  Object.assign(practice, data.practice || {})
  messages.value = data.messages || []
  todayTasks.value = data.tasks || []
  resources.value = data.resources || []
  path.value = data.path || []
  performance.value = data.performance || []
  safetyChecks.value = data.safety?.checks || []
  if (data.user?.id) {
    userId.value = data.user.id
    localStorage.setItem('english_learning_user_id', data.user.id)
  }
}

async function run(action) {
  loading.value = true
  error.value = ''
  try {
    await action()
  } catch (err) {
    error.value = err.message || '操作失败'
  } finally {
    loading.value = false
  }
}

async function refreshCaptcha() {
  const data = await request('/api/captcha')
  captcha.id = data.captcha_id
  captcha.code = data.code
  loginForm.captchaCode = data.code
}

async function register() {
  await run(async () => {
    await request('/api/register', { method: 'POST', body: JSON.stringify(registerForm) })
    loginForm.nickname = registerForm.nickname
    loginForm.phone = registerForm.phone
    loginForm.password = registerForm.password
    stage.value = 'login'
    await refreshCaptcha()
  })
}

async function login() {
  await run(async () => {
    const data = await request('/api/login', {
      method: 'POST',
      body: JSON.stringify({
        nickname: loginForm.nickname,
        phone: loginForm.phone,
        password: loginForm.password,
        captcha_id: captcha.id,
        captcha_code: loginForm.captchaCode
      })
    })
    applyState(data)
    stage.value = data.user?.onboarded ? 'dashboard' : 'basic-info'
  })
}

async function submitBasicInfo() {
  await run(async () => {
    if (!selectedGoals.value.length) throw new Error('请至少选择一个学习方向')
    await request('/api/onboarding/basic', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId.value, major: intakeForm.major, grade: intakeForm.grade, goal: selectedGoals.value.join('、') })
    })
    const data = await request('/api/diagnostic/questions')
    quizQuestions.value = data.questions || []
    stage.value = 'english-test'
  })
}

function toggleGoal(option) {
  if (selectedGoals.value.includes(option)) {
    selectedGoals.value = selectedGoals.value.filter((item) => item !== option)
  } else {
    selectedGoals.value = [...selectedGoals.value, option]
  }
}

async function submitQuiz() {
  await run(async () => {
    const data = await request('/api/onboarding/quiz', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId.value, quiz_answers: quizAnswers })
    })
    Object.assign(summary, data.summary || {})
    stage.value = 'level-summary'
  })
}

async function submitHours() {
  await run(async () => {
    const data = await request('/api/onboarding/hours', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId.value, daily_hours: Number(intakeForm.daily_hours) })
    })
    applyState(data)
    stage.value = 'dashboard'
  })
}

async function sendMessage() {
  if (!chatInput.value.trim()) return
  await run(async () => {
    const data = await request('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId.value, message: chatInput.value.trim() })
    })
    chatInput.value = ''
    applyState(data.state)
  })
}

async function toggleTask(task) {
  await run(async () => {
    const data = await request('/api/tasks/toggle', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId.value, task_id: task.id })
    })
    applyState(data)
  })
}

async function submitPractice() {
  await run(async () => {
    const data = await request('/api/evaluate', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId.value, answer: practice.answer })
    })
    applyState(data.state)
  })
}

async function loadState() {
  if (!userId.value) {
    await refreshCaptcha()
    return
  }
  try {
    const data = await request(`/api/state/${userId.value}`)
    applyState(data)
    stage.value = data.user?.onboarded ? 'dashboard' : 'basic-info'
  } catch {
    localStorage.removeItem('english_learning_user_id')
    userId.value = ''
    stage.value = 'register'
    await refreshCaptcha()
  }
}

function resourceIcon(res) {
  return iconMap[res.tag] || FileText
}

onMounted(loadState)
</script>

<template>
  <section v-if="stage === 'register'" class="auth-page">
    <div class="auth-card auth-hero">
      <div class="brand-line"><GraduationCap :size="26" />智学工坊</div>
      <div>
        <h1>先注册账号，再生成你的英语学习方案</h1>
        <p>注册登录用于保存学习画像、测试结果、每日任务、AI 对话和练习反馈。</p>
      </div>
    </div>
    <form class="auth-card auth-form" @submit.prevent="register">
      <h2>注册账号</h2>
      <label>昵称<input v-model="registerForm.nickname" class="input" /></label>
      <label>手机号<input v-model="registerForm.phone" class="input" /></label>
      <label>密码<input v-model="registerForm.password" type="password" class="input" /></label>
      <p v-if="error" class="feedback">{{ error }}</p>
      <button class="btn primary" type="submit" :disabled="loading">注册并进入登录 <ChevronRight :size="17" /></button>
      <button class="btn ghost" type="button" @click="stage = 'login'; refreshCaptcha()">已有账号，去登录</button>
    </form>
  </section>

  <section v-else-if="stage === 'login'" class="auth-page">
    <div class="auth-card auth-hero login-side">
      <div class="brand-line"><GraduationCap :size="26" />智学工坊</div>
      <div>
        <h1>登录后继续你的个性化学习流程</h1>
        <p>登录成功后，系统会进入基础信息、英语测试、学习时长和学习方案生成流程。</p>
      </div>
    </div>
    <form class="auth-card auth-form" @submit.prevent="login">
      <h2>登录</h2>
      <label>昵称<input v-model="loginForm.nickname" class="input" /></label>
      <label>手机号<input v-model="loginForm.phone" class="input" /></label>
      <label>密码<input v-model="loginForm.password" type="password" class="input" /></label>
      <div class="captcha-row">
        <label class="captcha-input">验证码<input v-model="loginForm.captchaCode" class="input" /></label>
        <button class="captcha-box" type="button" @click="refreshCaptcha">
          <span>{{ captcha.code || '----' }}</span>
          <small><RefreshCw :size="14" />刷新</small>
        </button>
      </div>
      <p v-if="error" class="feedback">{{ error }}</p>
      <button class="btn primary" type="submit" :disabled="loading">登录进入 <ChevronRight :size="17" /></button>
      <button class="btn ghost" type="button" @click="stage = 'register'">没有账号，去注册</button>
    </form>
  </section>

  <section v-else-if="stage === 'basic-info'" class="onboard-page single-step">
    <div class="onboard-head"><h1>基础信息</h1><p>这些信息会影响资源主题、学习路径和练习难度。</p></div>
    <div class="card step-card">
      <div class="card-header"><div><h3>第 1 步：告诉 AI 你的学习背景</h3><p>填写专业、年级，并选择一个或多个学习方向。</p></div></div>
      <div class="card-body onboard-form">
        <label>专业<input v-model="intakeForm.major" class="input" /></label>
        <label>年级<input v-model="intakeForm.grade" class="input" /></label>
        <div class="field-block">
          <div class="field-label">正在学习的方向（可多选）</div>
          <div class="option-grid">
            <button
              v-for="option in learningOptions"
              :key="option"
              type="button"
              class="option-chip"
              :class="{ selected: selectedGoals.includes(option) }"
              @click="toggleGoal(option)"
            >
              <CheckCircle2 :size="16" />
              {{ option }}
            </button>
          </div>
        </div>
        <p v-if="error" class="feedback">{{ error }}</p>
        <button class="btn primary" :disabled="loading" @click="submitBasicInfo">下一步：英语水平测试</button>
      </div>
    </div>
  </section>

  <section v-else-if="stage === 'english-test'" class="onboard-page single-step">
    <div class="onboard-head"><h1>英语水平测试</h1><p>测试会用于生成学习画像。</p></div>
    <div class="card step-card wide-step">
      <div class="card-body quiz-list">
        <article v-for="q in quizQuestions" :key="q.id" class="quiz-item">
          <strong>{{ q.skill }} · {{ q.question }}</strong>
          <template v-if="q.type === 'choice'">
            <button v-for="opt in q.options" :key="opt" class="choice-btn" :class="{ selected: quizAnswers[q.id] === opt }" type="button" @click="quizAnswers[q.id] = opt">{{ opt }}</button>
          </template>
          <textarea v-else v-model="quizAnswers[q.id]" class="textarea" placeholder="输入你的改写答案"></textarea>
        </article>
        <p v-if="error" class="feedback">{{ error }}</p>
        <button class="btn primary" :disabled="loading" @click="submitQuiz">提交测试并查看总结</button>
      </div>
    </div>
  </section>

  <section v-else-if="stage === 'level-summary'" class="onboard-page single-step">
    <div class="onboard-head"><h1>英语水平总结</h1><p>后端根据测试结果生成诊断。</p></div>
    <div class="card step-card">
      <div class="card-body summary-panel">
        <div class="summary-score"><strong>{{ summary.level }}</strong><span>综合得分 {{ summary.score }}</span></div>
        <div class="summary-lines"><p v-for="line in summary.summary_lines" :key="line">{{ line }}</p></div>
        <div class="skill-bars">
          <div v-for="(score, skill) in summary.skill_scores" :key="skill" class="skill-row">
            <span>{{ skill }}</span><div class="meter"><span :style="{ width: score + '%' }"></span></div><strong>{{ score }}%</strong>
          </div>
        </div>
        <button class="btn primary" @click="stage = 'daily-hours'">下一步：填写每日学习时长</button>
      </div>
    </div>
  </section>

  <section v-else-if="stage === 'daily-hours'" class="onboard-page single-step">
    <div class="onboard-head"><h1>每日学习时长</h1><p>系统会按可用时间控制任务数量和资源密度。</p></div>
    <div class="card step-card">
      <div class="card-body onboard-form">
        <label>每天学习时长（小时）<input v-model="intakeForm.daily_hours" type="number" min="0.25" step="0.25" class="input" /></label>
        <p v-if="error" class="feedback">{{ error }}</p>
        <button class="btn primary" :disabled="loading" @click="submitHours">生成我的学习方案</button>
      </div>
    </div>
  </section>

  <div v-else class="student-shell">
    <aside class="student-sidebar">
      <div class="brand"><div class="brand-mark">智</div><div><h1>智学工坊</h1><p>{{ user.course }}</p></div></div>
      <nav class="menu">
        <button v-for="item in navItems" :key="item.id" :class="{ active: active === item.id }" @click="active = item.id">
          <span><component :is="item.icon" :size="17" />{{ item.label }}</span>
        </button>
      </nav>
      <div class="sidebar-card"><h3>今日进度</h3><div class="big-progress">{{ completion }}%</div><div class="bar"><span :style="{ width: completion + '%' }"></span></div></div>
    </aside>

    <main class="student-main">
      <header class="student-header">
        <div><p class="eyebrow">你好，{{ user.nickname }} · {{ user.grade }}</p><h2>{{ active === 'home' ? '学习主页' : navItems.find((item) => item.id === active)?.label }}</h2></div>
        <div class="safe-chip"><ShieldCheck :size="16" />内容已通过安全校验</div>
      </header>

      <section v-if="active === 'home'" class="grid">
        <div class="welcome-band"><div><h3>你的个性化英语学习方案已经生成</h3><p>系统会按专业、年级、测试水平、目标和每日时长调整任务、资源和路径。</p></div><button class="btn primary" @click="active = 'chat'"><MessageCircle :size="17" />继续和 AI 导师对话</button></div>
        <div class="grid cols-2">
          <section class="card"><div class="card-header"><div><h3>今日任务</h3><p>任务会根据你的画像动态变化。</p></div><Flame class="hot-icon" :size="22" /></div><div class="card-body task-list"><button v-for="task in todayTasks" :key="task.id" class="task-item" :class="{ done: task.done }" @click="toggleTask(task)"><CheckCircle2 :size="19" /><div><strong>{{ task.title }}</strong><span>{{ task.type }} · {{ task.time }}</span></div></button></div></section>
          <section class="card"><div class="card-header"><div><h3>AI 推送资源</h3><p>由学习方案和测试结果实时生成。</p></div><Sparkles :size="22" /></div><div class="card-body compact-resources"><article v-for="res in resources.slice(0, 3)" :key="res.id"><component :is="resourceIcon(res)" :size="19" /><div><strong>{{ res.title }}</strong><span>{{ res.tag }}</span></div></article></div></section>
        </div>
      </section>

      <section v-if="active === 'chat'" class="card learning-chat"><div class="card-header"><div><h3>AI 导师</h3><p>继续更新专业、目标、学习节奏和薄弱项。</p></div></div><div class="card-body chat"><div class="chat-log"><div v-for="(msg, index) in messages" :key="index" class="msg" :class="msg.role"><div class="meta">{{ msg.role === 'user' ? user.nickname : 'AI 英语导师' }}</div><div>{{ msg.text }}</div></div></div><div class="chat-input-row"><textarea v-model="chatInput" class="textarea" @keydown.ctrl.enter="sendMessage" /><button class="btn primary send-btn" @click="sendMessage"><Send :size="18" />发送</button></div><p v-if="error" class="feedback">{{ error }}</p></div></section>

      <section v-if="active === 'path'" class="card"><div class="card-header"><div><h3>学习路径</h3><p>根据任务完成情况动态调整。</p></div></div><div class="card-body plan"><article v-for="item in path" :key="item.id" class="plan-item" :class="{ current: item.active }"><div class="meta"><strong>{{ item.day }}</strong><span>{{ item.progress }}%</span></div><strong>{{ item.title }}</strong><div class="meter"><span :style="{ width: item.progress + '%' }"></span></div></article></div></section>

      <section v-if="active === 'resources'" class="card"><div class="card-header"><div><h3>我的资源库</h3><p>讲解、导图、题库、案例和脚本。</p></div></div><div class="card-body"><div class="resource-grid"><article v-for="res in resources" :key="res.id" class="resource"><component :is="resourceIcon(res)" :size="22" /><h4>{{ res.title }}</h4><small>{{ res.tag }}</small><p>{{ res.desc }}</p><button class="btn">开始学习</button></article></div></div></section>

      <section v-if="active === 'practice'" class="grid cols-2"><div class="card"><div class="card-header"><div><h3>专项练习</h3><p>练习结果会回写画像。</p></div></div><div class="card-body practice-box"><p>{{ practice.question }}</p><pre>{{ practice.prompt }}</pre><input v-model="practice.answer" class="input" placeholder="写出你的答案" /><button class="btn primary" @click="submitPractice">提交答案</button><div v-if="practice.result" class="feedback"><Lightbulb :size="18" />{{ practice.result }}</div></div></div><div class="card"><div class="card-header"><div><h3>最近表现</h3><p>由测试和练习结果生成。</p></div></div><div class="card-body"><table class="table"><thead><tr><th>维度</th><th>正确率</th><th>建议</th></tr></thead><tbody><tr v-for="item in performance" :key="item.topic"><td>{{ item.topic }}</td><td>{{ item.accuracy }}%</td><td>{{ item.suggestion }}</td></tr></tbody></table></div></div></section>

      <section v-if="active === 'profile'" class="card"><div class="card-header"><div><h3>学习画像</h3><p>来自注册、测试、对话和练习结果。</p></div></div><div class="card-body"><div class="profile-grid"><div class="profile"><div class="label">知识基础</div><div class="value">{{ profile.knowledge }}</div></div><div class="profile"><div class="label">薄弱知识点</div><div class="value">{{ profile.weakness }}</div></div><div class="profile"><div class="label">认知风格</div><div class="value">{{ profile.style }}</div></div><div class="profile"><div class="label">学习节奏</div><div class="value">{{ profile.pace }}</div></div><div class="profile"><div class="label">易错题型</div><div class="value">{{ profile.mistakes }}</div></div><div class="profile"><div class="label">学习目标</div><div class="value">{{ profile.goal }}</div></div></div><div class="safety-box"><h4>安全校验</h4><span v-for="item in safetyChecks" :key="item.name">{{ item.name }}：{{ item.status }}</span></div></div></section>
    </main>
  </div>
</template>
