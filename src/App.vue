<script setup>
import { computed, reactive, ref } from 'vue'
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
  Send,
  ShieldCheck,
  Sparkles,
  UserRound
} from 'lucide-vue-next'

const signedIn = ref(false)
const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
const active = ref('home')
const loading = ref(false)
const streamText = ref('')
const loginForm = reactive({
  name: '林同学',
  goal: '三个月内通过六级，并把阅读和写作提升到雅思 6.5 水平'
})
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
const selectedCourses = ref(['大学英语六级', '雅思 IELTS', '阅读提速'])
const chatInput = ref('我六级 480 分，阅读比较慢，写作句子不够高级。每天能学 1 小时。')
const learningStats = [
  { label: '今日完成', value: '62%', detail: '4 个任务中的 2.5 个' },
  { label: '目标周期', value: '90 天', detail: '六级到雅思 6.5' },
  { label: 'AI 反馈', value: '24h', detail: '持续更新学习画像' }
]

const navItems = [
  { id: 'home', label: '今日学习', icon: Home },
  { id: 'chat', label: 'AI 导师', icon: MessageCircle },
  { id: 'path', label: '学习路径', icon: Map },
  { id: 'resources', label: '资源库', icon: BookOpen },
  { id: 'practice', label: '练习评测', icon: ListChecks },
  { id: 'profile', label: '学习画像', icon: UserRound }
]

const messages = ref([
  {
    role: 'assistant',
    text: '欢迎回来。我会根据你的学习状态推荐今天的任务。你可以直接告诉我哪里卡住了，我会同步更新学习画像。'
  },
  {
    role: 'assistant',
    text: '今天建议先背 20 个高频词，再做 1 篇段落定位阅读和 1 段 Task 2 写作开头。'
  }
])

const profile = reactive({
  knowledge: 'CET-6 480 分左右，基础语法较稳，词汇量和长难句理解还有提升空间。',
  weakness: '阅读定位速度、长难句拆解、学术词汇、写作论证展开。',
  style: '更适合例句对比、结构化模板、语境记忆和短练即时反馈。',
  pace: '每天 1 小时，适合 20 分钟词汇 + 25 分钟阅读/听力 + 15 分钟输出。',
  mistakes: '阅读同义替换识别慢，写作句式重复，介词和冠词错误较多。',
  goal: '三个月内通过六级，并冲刺雅思 6.5，重点提升阅读和写作。'
})

const todayTasks = ref([
  { title: '高频学术词 20 个', type: '词汇表', time: '15 分钟', done: false },
  { title: '阅读定位技巧微课', type: '讲解文档', time: '18 分钟', done: true },
  { title: '同义替换专项 8 题', type: '练习题库', time: '20 分钟', done: false },
  { title: 'Task 2 开头段改写', type: '写作训练', time: '22 分钟', done: false }
])

const resources = [
  { title: '阅读段落定位讲义', tag: '课程讲解文档', desc: '用题干关键词、同义替换和段落功能句训练定位速度。', icon: FileText },
  { title: '英语能力思维导图', tag: '知识点思维导图', desc: '把词汇、语法、阅读、听力、写作和口语串成能力图谱。', icon: BrainCircuit },
  { title: '同义替换专项题库', tag: '练习题库', desc: '按易错原因生成基础、提升、冲刺三档题目。', icon: ListChecks },
  { title: '写作句式升级案例', tag: '写作实操案例', desc: '把普通句改写成适合六级和雅思 Task 2 的表达。', icon: PenLine },
  { title: '听说跟读脚本', tag: '多模态教学脚本', desc: '包含听力关键词、跟读停顿、口语复述和课堂展示脚本。', icon: PlayCircle },
  { title: '核心词汇清单', tag: '个性化词汇表', desc: '结合目标考试和薄弱主题生成每日词汇与例句。', icon: Languages }
]

const featureCards = [
  { title: '学习画像', desc: '根据目标、薄弱点和对话更新你的能力结构。', icon: UserRound },
  { title: '资源推荐', desc: '把讲义、题库、词汇和写作案例匹配到当前阶段。', icon: Sparkles },
  { title: '练习反馈', desc: '根据练习结果给出下一步修正建议。', icon: BrainCircuit }
]

const path = [
  { day: '今天', title: '高频词汇 + 阅读定位', progress: 62, active: true },
  { day: '明天', title: '长难句拆解 + 同义替换', progress: 0, active: false },
  { day: '第 3 天', title: '听力关键词捕捉', progress: 0, active: false },
  { day: '第 4 天', title: '写作开头段与论点展开', progress: 0, active: false },
  { day: '第 5 天', title: '阶段测评与错题回收', progress: 0, active: false }
]

const practice = reactive({
  question: '请把下面句子升级成更适合英语写作的表达，重点使用更自然的动词和连接结构。',
  code: 'Many students use online learning. It is convenient. But it also has some problems.',
  answer: '',
  result: ''
})

const completion = computed(() => {
  const done = todayTasks.value.filter((item) => item.done).length
  return Math.round((done / todayTasks.value.length) * 100)
})

function signIn() {
  if (loginForm.name.trim()) signedIn.value = true
}

function toggleCourse(option) {
  if (selectedCourses.value.includes(option)) {
    selectedCourses.value = selectedCourses.value.filter((item) => item !== option)
  } else {
    selectedCourses.value = [...selectedCourses.value, option]
  }
}

function toggleTask(task) {
  task.done = !task.done
}

function updateProfileFromText(text) {
  if (text.includes('阅读')) profile.weakness = '阅读定位、同义替换识别、长难句主干提取。'
  if (text.includes('写作')) profile.mistakes = '句式重复、论证展开不足、连接词使用单一。'
  if (text.includes('听力')) profile.weakness = '听力关键词捕捉、数字信息、转折信号识别。'
  if (text.includes('雅思') || text.includes('六级')) profile.goal = '三个月内完成六级提分，并逐步过渡到雅思 6.5 能力要求。'
}

async function sendMessage() {
  if (loading.value || !chatInput.value.trim()) return
  const text = chatInput.value.trim()
  messages.value.push({ role: 'user', text })
  updateProfileFromText(text)
  chatInput.value = ''
  loading.value = true
  streamText.value = '正在生成学习建议...'

  try {
    const history = messages.value.slice(-10).map((msg) => ({
      role: msg.role === 'assistant' ? 'assistant' : 'user',
      content: msg.text
    }))
    const response = await fetch(`${API_BASE}/api/ai/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, history })
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(data.detail || 'AI 服务暂时不可用')
    messages.value.push({ role: 'assistant', text: data.reply })
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      text: `AI 导师暂时没有返回结果：${error.message || '请检查后端服务配置'}`
    })
  } finally {
    loading.value = false
    streamText.value = ''
  }
}
function submitPractice() {
  const answer = practice.answer.toLowerCase()
  if (answer.includes('although') || answer.includes('while') || answer.includes('however') || answer.includes('nevertheless')) {
    practice.result = '不错。你已经加入让步或转折结构，表达更像正式写作。下一步可以补充具体原因或例子。'
    profile.mistakes = '写作衔接有所改善，仍需增加具体论据和高级替换词。'
  } else {
    practice.result = '还可以再升级。试着用 although、while、however 连接观点，并把 convenient 换成 flexible 或 accessible。'
    profile.mistakes = '写作句式仍偏简单，需要继续练习转折结构和词汇替换。'
  }
}
</script>

<template>
  <section v-if="!signedIn" class="login-page">
    <div class="login-panel">
      <div class="login-copy">
        <div class="brand-line"><GraduationCap :size="26" />智学工坊</div>
        <h1>让 AI 英语导师按你的节奏安排学习</h1>
        <p>告诉我你的英语水平、薄弱项和目标考试，我会生成学习画像、每日任务、学习路径、资源推荐和练习反馈。</p>
      </div>
      <form class="login-card" @submit.prevent="signIn">
        <label>昵称<input v-model="loginForm.name" class="input" placeholder="请输入昵称" /></label>
        <div class="field-block">
          <div class="field-label">正在学习的方向（可多选）</div>
          <div class="option-grid">
            <button
              v-for="option in learningOptions"
              :key="option"
              type="button"
              class="option-chip"
              :class="{ selected: selectedCourses.includes(option) }"
              @click="toggleCourse(option)"
            >
              <CheckCircle2 :size="16" />
              {{ option }}
            </button>
          </div>
        </div>
        <label>近期目标<textarea v-model="loginForm.goal" class="textarea small" placeholder="例如 三个月内通过六级并提升阅读" /></label>
        <button class="btn primary" type="submit">进入学习 <ChevronRight :size="17" /></button>
      </form>
    </div>
  </section>

  <div v-else class="student-shell">
    <aside class="student-sidebar">
      <div class="brand">
        <div class="brand-mark">智</div>
        <div>
          <h1>智学工坊</h1>
          <p>{{ selectedCourses.join(' / ') }}</p>
        </div>
      </div>
      <nav class="menu">
        <button v-for="item in navItems" :key="item.id" :class="{ active: active === item.id }" @click="active = item.id">
          <span><component :is="item.icon" :size="17" />{{ item.label }}</span>
        </button>
      </nav>
      <div class="sidebar-card">
        <h3>今日进度</h3>
        <div class="big-progress">{{ completion }}%</div>
        <div class="bar"><span :style="{ width: completion + '%' }"></span></div>
      </div>
    </aside>

    <main class="student-main">
      <header class="student-header">
        <div>
          <p class="eyebrow">你好，{{ loginForm.name }}</p>
          <h2>{{ active === 'home' ? '今天从这里开始' : navItems.find((item) => item.id === active)?.label }}</h2>
        </div>
        <div class="safe-chip"><ShieldCheck :size="16" />内容已通过安全校验</div>
      </header>

      <section v-if="active === 'home'" class="page-view grid">
        <div class="hero-stage">
          <div class="hero-copy">
            <div class="hero-kicker"><Sparkles :size="16" />智能学习引擎</div>
            <h3>把英语学习变成一套会自我调整的系统。</h3>
            <p>智学工坊会根据你的目标、练习结果和对话反馈，持续生成任务、资源和下一步建议。今天先把阅读定位和写作表达拉到更稳定的节奏。</p>
            <div class="hero-actions">
              <button class="btn primary hero-cta" @click="active = 'chat'"><MessageCircle :size="17" />询问 AI 导师</button>
              <button class="btn" @click="active = 'practice'"><ListChecks :size="17" />开始练习</button>
            </div>
          </div>
          <div class="hero-console">
            <div class="console-top">
              <span></span><span></span><span></span>
            </div>
            <div class="console-card">
              <small>Today's focus</small>
              <strong>高频词汇 + 阅读定位</strong>
              <div class="meter"><span :style="{ width: completion + '%' }"></span></div>
            </div>
            <div class="console-grid">
              <article v-for="stat in learningStats" :key="stat.label">
                <span>{{ stat.label }}</span>
                <strong>{{ stat.value }}</strong>
                <small>{{ stat.detail }}</small>
              </article>
            </div>
          </div>
        </div>

        <div class="feature-grid">
          <article v-for="feature in featureCards" :key="feature.title" class="feature-card">
            <component :is="feature.icon" :size="22" />
            <h4>{{ feature.title }}</h4>
            <p>{{ feature.desc }}</p>
          </article>
        </div>

        <div class="grid cols-2">
          <section class="card">
            <div class="card-header">
              <div><h3>今日任务</h3><p>按顺序完成，系统会记录学习效果。</p></div>
              <Flame class="hot-icon" :size="22" />
            </div>
            <div class="card-body task-list">
              <button v-for="task in todayTasks" :key="task.title" class="task-item" :class="{ done: task.done }" @click="toggleTask(task)">
                <CheckCircle2 :size="19" />
                <div>
                  <strong>{{ task.title }}</strong>
                  <span>{{ task.type }} · {{ task.time }}</span>
                </div>
              </button>
            </div>
          </section>

          <section class="card">
            <div class="card-header">
              <div><h3>AI 推送资源</h3><p>根据薄弱点自动推荐最合适的资源类型。</p></div>
              <Sparkles :size="22" />
            </div>
            <div class="card-body compact-resources">
              <article v-for="res in resources.slice(0, 3)" :key="res.title">
                <component :is="res.icon" :size="19" />
                <div><strong>{{ res.title }}</strong><span>{{ res.tag }}</span></div>
              </article>
            </div>
          </section>
        </div>
      </section>

      <section v-if="active === 'chat'" class="card learning-chat">
        <div class="card-header">
          <div><h3>AI 英语导师</h3><p>直接说你哪里不会，我会边聊边更新你的学习画像和资源推荐。</p></div>
          <div class="model-chip"><Sparkles :size="15" />智能引擎已连接</div>
        </div>
        <div class="card-body chat">
          <div class="chat-log">
            <div v-for="(msg, index) in messages" :key="index" class="msg" :class="msg.role">
              <div class="meta">{{ msg.role === 'user' ? loginForm.name : 'AI 英语导师' }}</div>
              <div>{{ msg.text }}</div>
            </div>
            <div v-if="loading" class="msg assistant">
              <div class="meta">AI 英语导师</div>
              <div>{{ streamText }}</div>
            </div>
          </div>
          <div class="chat-input-row">
            <textarea v-model="chatInput" class="textarea" placeholder="例如：我阅读定位慢，写作句式也比较单一..." @keydown.ctrl.enter="sendMessage" />
            <button class="btn primary send-btn" @click="sendMessage"><Send :size="18" />发送</button>
          </div>
        </div>
      </section>

      <section v-if="active === 'path'" class="card">
        <div class="card-header"><div><h3>学习路径</h3><p>路径会根据练习结果自动调整。</p></div></div>
        <div class="card-body plan">
          <article v-for="item in path" :key="item.day" class="plan-item" :class="{ current: item.active }">
            <div class="meta"><strong>{{ item.day }}</strong><span>{{ item.progress }}%</span></div>
            <strong>{{ item.title }}</strong>
            <div class="meter"><span :style="{ width: item.progress + '%' }"></span></div>
          </article>
        </div>
      </section>

      <section v-if="active === 'resources'" class="card">
        <div class="card-header"><div><h3>我的资源库</h3><p>讲解文档、思维导图、题库、写作案例、听说脚本和词汇表都会按你的画像生成。</p></div></div>
        <div class="card-body">
          <div class="resource-grid">
            <article v-for="res in resources" :key="res.title" class="resource">
              <component :is="res.icon" :size="22" />
              <h4>{{ res.title }}</h4>
              <small>{{ res.tag }}</small>
              <p>{{ res.desc }}</p>
              <button class="btn">开始学习</button>
            </article>
          </div>
        </div>
      </section>

      <section v-if="active === 'practice'" class="grid cols-2">
        <div class="card">
          <div class="card-header"><div><h3>专项练习</h3><p>做题结果会回写画像，并影响后续推荐。</p></div></div>
          <div class="card-body practice-box">
            <p>{{ practice.question }}</p>
            <pre>{{ practice.code }}</pre>
            <input v-model="practice.answer" class="input" placeholder="写出你的升级表达" />
            <button class="btn primary" @click="submitPractice">提交答案</button>
            <div v-if="practice.result" class="feedback"><Lightbulb :size="18" />{{ practice.result }}</div>
          </div>
        </div>
        <div class="card">
          <div class="card-header"><div><h3>最近表现</h3><p>系统会持续记录正确率、耗时和错误类型。</p></div></div>
          <div class="card-body">
            <table class="table">
              <thead><tr><th>知识点</th><th>正确率</th><th>建议</th></tr></thead>
              <tbody>
                <tr><td>阅读定位</td><td>62%</td><td>继续专项</td></tr>
                <tr><td>同义替换</td><td>74%</td><td>增加语境练习</td></tr>
                <tr><td>基础语法</td><td>91%</td><td>保持</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section v-if="active === 'profile'" class="card">
        <div class="card-header"><div><h3>我的学习画像</h3><p>画像来自你的对话、任务完成情况和练习表现，会随学随更。</p></div></div>
        <div class="card-body">
          <div class="profile-grid">
            <div class="profile"><div class="label">知识基础</div><div class="value">{{ profile.knowledge }}</div></div>
            <div class="profile"><div class="label">薄弱知识点</div><div class="value">{{ profile.weakness }}</div></div>
            <div class="profile"><div class="label">认知风格</div><div class="value">{{ profile.style }}</div></div>
            <div class="profile"><div class="label">学习节奏</div><div class="value">{{ profile.pace }}</div></div>
            <div class="profile"><div class="label">易错题型</div><div class="value">{{ profile.mistakes }}</div></div>
            <div class="profile"><div class="label">学习目标</div><div class="value">{{ profile.goal }}</div></div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

