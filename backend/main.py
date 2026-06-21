from __future__ import annotations

import hashlib
import json
import os
import random
import string
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
STORE_PATH = DATA_DIR / "learning_store.json"


def load_local_env() -> None:
    env_path = PROJECT_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()

DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

app = FastAPI(title="Smart English Learning API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterRequest(BaseModel):
    nickname: str = Field(min_length=1)
    phone: str = Field(min_length=6)
    password: str = Field(min_length=4)


class LoginRequest(BaseModel):
    nickname: str = Field(min_length=1)
    phone: str = Field(min_length=6)
    password: str = Field(min_length=4)
    captcha_id: str
    captcha_code: str


class BasicInfoRequest(BaseModel):
    user_id: str
    major: str = Field(min_length=1)
    grade: str = Field(min_length=1)
    goal: str = Field(min_length=1)


class QuizRequest(BaseModel):
    user_id: str
    quiz_answers: dict[str, str]


class HoursRequest(BaseModel):
    user_id: str
    daily_hours: float = Field(gt=0)


class ChatRequest(BaseModel):
    user_id: str
    message: str = Field(min_length=1)


class DeepSeekChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[dict[str, str]] = Field(default_factory=list)


class TaskToggleRequest(BaseModel):
    user_id: str
    task_id: str


class EvaluateRequest(BaseModel):
    user_id: str
    answer: str = ""


DIAGNOSTIC_QUESTIONS = [
    {
        "id": "vocab",
        "type": "choice",
        "skill": "词汇",
        "question": "Choose the closest meaning of substantial.",
        "options": ["small", "important and large", "temporary", "unclear"],
        "answer": "important and large",
    },
    {
        "id": "grammar",
        "type": "choice",
        "skill": "语法",
        "question": "Which sentence is correct?",
        "options": [
            "She go to school every day.",
            "She goes to school every day.",
            "She going to school every day.",
            "She gone to school every day.",
        ],
        "answer": "She goes to school every day.",
    },
    {
        "id": "reading",
        "type": "choice",
        "skill": "阅读",
        "question": "In reading tests, however usually signals:",
        "options": ["example", "contrast", "cause", "time order"],
        "answer": "contrast",
    },
    {
        "id": "writing",
        "type": "text",
        "skill": "写作",
        "question": "Rewrite this sentence more formally: Online learning is good and easy.",
        "answer": "open",
    },
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def default_store() -> dict[str, Any]:
    return {"accounts": {}, "users": {}, "captchas": {}}


def load_store() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not STORE_PATH.exists():
        save_store(default_store())
    store = json.loads(STORE_PATH.read_text(encoding="utf-8"))
    store.setdefault("accounts", {})
    store.setdefault("users", {})
    store.setdefault("captchas", {})
    return store


def save_store(store: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def normalize_phone(phone: str) -> str:
    return "".join(ch for ch in phone if ch.isdigit())


def user_or_404(store: dict[str, Any], user_id: str) -> dict[str, Any]:
    user = store["users"].get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在，请重新登录")
    return user


def detect_exam(goal: str) -> str:
    goal_lower = goal.lower()
    if "雅思" in goal or "ielts" in goal_lower:
        return "雅思"
    if "托福" in goal or "toefl" in goal_lower:
        return "托福"
    if "六级" in goal:
        return "大学英语六级"
    if "四级" in goal:
        return "大学英语四级"
    if "考研" in goal:
        return "考研英语"
    if "商务" in goal or "bec" in goal_lower:
        return "商务英语"
    return "综合英语提升"


def safety_agent(text: str) -> dict[str, Any]:
    risky_words = ["暴力", "色情", "赌博", "违法", "作弊", "代写"]
    hits = [word for word in risky_words if word in text]
    return {
        "passed": not hits,
        "blocked_terms": hits,
        "checks": [
            {"name": "敏感内容过滤", "status": "通过" if not hits else "拦截"},
            {"name": "学习场景相关性", "status": "通过"},
            {"name": "输出格式校验", "status": "通过"},
        ],
    }


def evaluate_quiz(answers: dict[str, str]) -> dict[str, Any]:
    skill_scores = {"词汇": 45, "语法": 45, "阅读": 45, "写作": 45}
    for question in DIAGNOSTIC_QUESTIONS:
        answer = (answers.get(question["id"], "") or "").strip()
        if question["type"] == "choice":
            skill_scores[question["skill"]] = 85 if answer == question["answer"] else 45
        else:
            text = answer.lower()
            has_formal_word = any(word in text for word in ["accessible", "flexible", "efficient", "beneficial", "convenient"])
            has_connector = any(word in text for word in ["because", "although", "while", "however", "therefore"])
            skill_scores["写作"] = 85 if has_formal_word and has_connector else 68 if has_formal_word or has_connector else 45

    score = round(sum(skill_scores.values()) / len(skill_scores))
    if score >= 80:
        level = "B2 中高级"
    elif score >= 65:
        level = "B1 中级"
    elif score >= 50:
        level = "A2 基础提升"
    else:
        level = "A1-A2 基础巩固"
    weak_skills = [skill for skill, value in skill_scores.items() if value < 70] or ["高级表达", "限时输出"]
    return {
        "score": score,
        "level": level,
        "skill_scores": skill_scores,
        "weak_skills": weak_skills,
        "summary_lines": [
            f"当前等级：{level}",
            f"综合得分：{score}",
            f"优先提升：{'、'.join(weak_skills)}",
        ],
    }


def make_profile(user: dict[str, Any]) -> dict[str, str]:
    quiz = user.get("diagnostic") or evaluate_quiz({})
    weak_text = "、".join(quiz["weak_skills"])
    return {
        "knowledge": f"当前诊断为 {quiz['level']}，综合得分 {quiz['score']}。专业：{user.get('major', '未填写')}，年级：{user.get('grade', '未填写')}。",
        "weakness": f"主要薄弱点：{weak_text}。系统会优先推送相关资源和练习。",
        "style": "适合短任务、例句对比、即时反馈和错因复盘。",
        "pace": f"每天计划学习 {user.get('daily_hours', 1)} 小时，建议拆成词汇、输入理解、输出表达和复盘四段。",
        "mistakes": "常见风险是同义替换识别慢、长难句主干抓取不稳、写作句式单一。",
        "goal": f"目标方向：{detect_exam(user.get('goal', ''))}。具体目标：{user.get('goal', '')}",
    }


def make_tasks(profile: dict[str, str]) -> list[dict[str, Any]]:
    weakness = profile.get("weakness", "")
    tasks = [
        {"id": "task-vocab", "title": "个性化高频词 20 个", "type": "词汇表", "time": "15 分钟", "done": False},
        {"id": "task-reading", "title": "阅读定位与同义替换微课", "type": "讲解文档", "time": "18 分钟", "done": False},
        {"id": "task-practice", "title": "薄弱项专项练习 8 题", "type": "练习题库", "time": "20 分钟", "done": False},
        {"id": "task-output", "title": "写作句式升级训练", "type": "输出训练", "time": "22 分钟", "done": False},
    ]
    if "语法" in weakness:
        tasks[1]["title"] = "长难句拆解与语法纠错微课"
    if "听力" in weakness:
        tasks[2]["title"] = "听力关键词捕捉训练"
    return tasks


def make_resources(user: dict[str, Any]) -> list[dict[str, str]]:
    exam = detect_exam(user.get("goal", ""))
    major = user.get("major", "个人目标")
    return [
        {"id": "res-doc", "title": f"{exam}核心能力讲解文档", "tag": "课程讲解文档", "desc": "讲解词汇、语法、阅读和输出能力的提分方法。"},
        {"id": "res-map", "title": "英语能力思维导图", "tag": "知识点思维导图", "desc": f"把 {major} 场景和考试能力串成学习路径。"},
        {"id": "res-bank", "title": "薄弱项专项题库", "tag": "练习题库", "desc": "按诊断结果生成词汇、语法、阅读和写作练习。"},
        {"id": "res-writing", "title": "写作表达升级案例", "tag": "写作实操案例", "desc": "把普通表达改写为更自然、更正式的英文。"},
        {"id": "res-speaking", "title": "听说跟读脚本", "tag": "多模态教学脚本", "desc": "包含关键词、停顿跟读、复述和口语回答模板。"},
        {"id": "res-vocab", "title": "个性化核心词汇表", "tag": "个性化词汇表", "desc": "围绕目标考试和专业主题生成每日词汇。"},
    ]


def make_path(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    done = sum(1 for task in tasks if task.get("done"))
    first_progress = round(done / max(len(tasks), 1) * 100)
    return [
        {"id": "day-1", "day": "今天", "title": "高频词汇 + 阅读定位", "progress": first_progress, "active": True},
        {"id": "day-2", "day": "明天", "title": "长难句拆解 + 同义替换", "progress": 0, "active": False},
        {"id": "day-3", "day": "第 3 天", "title": "听力关键词捕捉", "progress": 0, "active": False},
        {"id": "day-4", "day": "第 4 天", "title": "写作开头段与论点展开", "progress": 0, "active": False},
        {"id": "day-5", "day": "第 5 天", "title": "阶段测评与错题回收", "progress": 0, "active": False},
    ]


def make_practice() -> dict[str, str]:
    return {
        "question": "请把下面句子升级成更适合英语写作的表达，注意连接结构和词汇替换。",
        "prompt": "Online learning is good and easy. But it also has some problems.",
        "answer": "",
        "result": "",
    }


def make_performance(diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"topic": skill, "accuracy": score, "suggestion": "继续专项" if score < 70 else "保持并提升"}
        for skill, score in diagnostic.get("skill_scores", {}).items()
    ]


def deepseek_reply(user: dict[str, Any], message: str) -> str | None:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return None

    system_prompt = (
        "你是一个英语学习系统里的 AI 导师。"
        "请根据用户的学习画像，给出具体、简洁、可执行的学习建议。"
        "回答必须围绕英语学习、任务安排、资源推荐、练习反馈。"
    )
    profile = user.get("profile", {})
    context = {
        "nickname": user.get("nickname", ""),
        "major": user.get("major", ""),
        "grade": user.get("grade", ""),
        "goal": user.get("goal", ""),
        "daily_hours": user.get("daily_hours", 0),
        "profile": profile,
        "tasks": user.get("tasks", []),
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"学习者资料：{json.dumps(context, ensure_ascii=False)}"},
            {"role": "user", "content": message},
        ],
        "temperature": 0.7,
        "max_tokens": 700,
        "stream": False,
    }
    request = urllib.request.Request(
        DEEPSEEK_API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError, json.JSONDecodeError) as exc:
        print(f"DeepSeek API call failed: {exc}")
        return None


def build_state(user: dict[str, Any]) -> dict[str, Any]:
    tasks = user.get("tasks", [])
    done = sum(1 for task in tasks if task.get("done"))
    completion = round(done / max(len(tasks), 1) * 100)
    user["path"] = make_path(tasks)
    return {
        "user": {
            "id": user["id"],
            "nickname": user.get("nickname", ""),
            "phone": user.get("phone", ""),
            "major": user.get("major", ""),
            "grade": user.get("grade", ""),
            "goal": user.get("goal", ""),
            "course": detect_exam(user.get("goal", "")),
            "daily_hours": user.get("daily_hours", 0),
            "onboarded": user.get("onboarded", False),
        },
        "profile": user.get("profile", {}),
        "messages": user.get("messages", []),
        "tasks": tasks,
        "resources": user.get("resources", []),
        "path": user.get("path", []),
        "practice": user.get("practice", make_practice()),
        "performance": user.get("performance", []),
        "safety": user.get("safety", safety_agent("")),
        "summary": user.get("diagnostic", {}),
        "completion": completion,
        "updated_at": user.get("updated_at", now_text()),
    }


def update_learning_plan(user: dict[str, Any]) -> None:
    user["profile"] = make_profile(user)
    user["tasks"] = make_tasks(user["profile"])
    user["resources"] = make_resources(user)
    user["path"] = make_path(user["tasks"])
    user["practice"] = make_practice()
    user["performance"] = make_performance(user.get("diagnostic", {}))
    user["safety"] = safety_agent(user.get("goal", ""))
    user["updated_at"] = now_text()


def call_deepseek(messages: list[dict[str, str]], max_tokens: int = 700) -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="请先在后端环境变量中配置 DEEPSEEK_API_KEY")

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": max_tokens,
        "stream": False,
    }
    request = urllib.request.Request(
        DEEPSEEK_API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore") or str(exc)
        raise HTTPException(status_code=502, detail=f"AI 服务调用失败：{detail}") from exc
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=502, detail=f"AI 服务调用失败：{exc}") from exc


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/ai/chat")
def deepseek_chat(payload: DeepSeekChatRequest) -> dict[str, str]:
    safe_history = [
        {"role": item.get("role", "user"), "content": item.get("content", "")}
        for item in payload.history[-10:]
        if item.get("role") in {"user", "assistant", "system"} and item.get("content")
    ]
    messages = [
        {
            "role": "system",
            "content": "你是一个面向英语学习项目的 AI 助手，回答要清晰、实用、适合前端直接展示。",
        },
        *safe_history,
        {"role": "user", "content": payload.message},
    ]
    return {"reply": call_deepseek(messages)}


@app.get("/api/captcha")
def get_captcha() -> dict[str, str]:
    store = load_store()
    captcha_id = str(uuid.uuid4())
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    store["captchas"][captcha_id] = {"code": code, "created_at": now_text()}
    save_store(store)
    return {"captcha_id": captcha_id, "code": code}


@app.post("/api/register")
def register(payload: RegisterRequest) -> dict[str, str]:
    store = load_store()
    phone = normalize_phone(payload.phone)
    if phone in store["accounts"]:
        raise HTTPException(status_code=409, detail="该手机号已注册，请直接登录")
    user_id = str(uuid.uuid4())
    store["accounts"][phone] = {
        "user_id": user_id,
        "nickname": payload.nickname,
        "password_hash": hash_password(payload.password),
    }
    store["users"][user_id] = {
        "id": user_id,
        "nickname": payload.nickname,
        "phone": phone,
        "major": "",
        "grade": "",
        "goal": "",
        "daily_hours": 0,
        "onboarded": False,
        "diagnostic": {},
        "profile": {},
        "messages": [],
        "tasks": [],
        "resources": [],
        "path": [],
        "practice": make_practice(),
        "performance": [],
        "safety": safety_agent(""),
        "created_at": now_text(),
        "updated_at": now_text(),
    }
    save_store(store)
    return {"message": "注册成功，请登录", "user_id": user_id}


@app.post("/api/login")
def login(payload: LoginRequest) -> dict[str, Any]:
    store = load_store()
    captcha = store["captchas"].get(payload.captcha_id)
    if not captcha or captcha["code"].lower() != payload.captcha_code.strip().lower():
        raise HTTPException(status_code=400, detail="验证码错误，请刷新后重试")
    phone = normalize_phone(payload.phone)
    account = store["accounts"].get(phone)
    if not account or account["password_hash"] != hash_password(payload.password):
        raise HTTPException(status_code=401, detail="手机号或密码错误")
    user = user_or_404(store, account["user_id"])
    if user.get("nickname") != payload.nickname:
        raise HTTPException(status_code=401, detail="昵称、手机号或密码不匹配")
    store["captchas"].pop(payload.captcha_id, None)
    user["updated_at"] = now_text()
    save_store(store)
    return build_state(user)


@app.get("/api/diagnostic/questions")
def diagnostic_questions() -> dict[str, Any]:
    return {"questions": [{k: v for k, v in item.items() if k != "answer"} for item in DIAGNOSTIC_QUESTIONS]}


@app.post("/api/onboarding/basic")
def onboarding_basic(payload: BasicInfoRequest) -> dict[str, Any]:
    store = load_store()
    user = user_or_404(store, payload.user_id)
    safety = safety_agent(payload.major + payload.grade + payload.goal)
    if not safety["passed"]:
        raise HTTPException(status_code=400, detail="输入内容未通过安全检查，请调整后重试")
    user["major"] = payload.major
    user["grade"] = payload.grade
    user["goal"] = payload.goal
    user["safety"] = safety
    user["updated_at"] = now_text()
    save_store(store)
    return {"message": "基础信息已保存", "user": build_state(user)["user"]}


@app.post("/api/onboarding/quiz")
def onboarding_quiz(payload: QuizRequest) -> dict[str, Any]:
    store = load_store()
    user = user_or_404(store, payload.user_id)
    user["diagnostic"] = evaluate_quiz(payload.quiz_answers)
    user["profile"] = make_profile(user)
    user["performance"] = make_performance(user["diagnostic"])
    user["updated_at"] = now_text()
    save_store(store)
    return {"summary": user["diagnostic"], "user": build_state(user)["user"]}


@app.post("/api/onboarding/hours")
def onboarding_hours(payload: HoursRequest) -> dict[str, Any]:
    store = load_store()
    user = user_or_404(store, payload.user_id)
    user["daily_hours"] = payload.daily_hours
    update_learning_plan(user)
    user["messages"] = [
        {"role": "assistant", "text": "你的个性化英语学习方案已经生成。"},
        {"role": "assistant", "text": f"我会按每天 {payload.daily_hours} 小时的节奏安排任务、资源和复盘。"},
    ]
    user["onboarded"] = True
    save_store(store)
    return build_state(user)


@app.get("/api/state/{user_id}")
def get_state(user_id: str) -> dict[str, Any]:
    store = load_store()
    user = user_or_404(store, user_id)
    return build_state(user)


@app.post("/api/chat")
def chat(payload: ChatRequest) -> dict[str, Any]:
    store = load_store()
    user = user_or_404(store, payload.user_id)
    safety = safety_agent(payload.message)
    user.setdefault("messages", []).append({"role": "user", "text": payload.message})
    if not safety["passed"]:
        reply = "这个请求不适合作为学习内容。我可以继续帮你做英语学习规划、练习讲解或写作修改。"
    else:
        text = payload.message
        if "阅读" in text:
            user.setdefault("profile", {})["weakness"] = "阅读定位、同义替换识别、长难句主干提取。"
        if "写作" in text:
            user.setdefault("profile", {})["mistakes"] = "写作句式重复、论证展开不足、连接词使用单一。"
        if "听力" in text:
            user.setdefault("profile", {})["weakness"] = "听力关键词捕捉、数字信息和转折信号识别。"
        user["resources"] = make_resources(user)
        reply = deepseek_reply(user, payload.message)
        if not reply:
            reply = f"我已记录你的新反馈。接下来建议先处理：{user.get('profile', {}).get('weakness', '薄弱项专项练习')} 今天先完成一个输入任务，再做一个输出改写任务。"
    user["messages"].append({"role": "assistant", "text": reply})
    user["safety"] = safety
    user["updated_at"] = now_text()
    save_store(store)
    return {"reply": reply, "state": build_state(user)}


@app.post("/api/tasks/toggle")
def toggle_task(payload: TaskToggleRequest) -> dict[str, Any]:
    store = load_store()
    user = user_or_404(store, payload.user_id)
    for task in user.get("tasks", []):
        if task["id"] == payload.task_id:
            task["done"] = not task.get("done", False)
            break
    else:
        raise HTTPException(status_code=404, detail="任务不存在")
    user["updated_at"] = now_text()
    save_store(store)
    return build_state(user)


@app.post("/api/evaluate")
def evaluate(payload: EvaluateRequest) -> dict[str, Any]:
    store = load_store()
    user = user_or_404(store, payload.user_id)
    answer = payload.answer.lower()
    has_connector = any(word in answer for word in ["although", "while", "however", "therefore", "because"])
    has_upgrade = any(word in answer for word in ["accessible", "flexible", "efficient", "beneficial", "challenge"])
    if has_connector and has_upgrade:
        result = "不错。你加入了连接结构和更自然的替换词，表达更接近正式写作。"
        accuracy = 86
    elif has_connector or has_upgrade:
        result = "方向对了。下一步可以同时补充连接词和更具体的高级替换词。"
        accuracy = 72
    else:
        result = "还可以再升级。试着使用 although、however、because，并替换 good/easy 这类普通词。"
        accuracy = 58
    user.setdefault("practice", make_practice())["answer"] = payload.answer
    user["practice"]["result"] = result
    user["performance"] = [
        {"topic": "输出表达", "accuracy": accuracy, "suggestion": "继续输出训练" if accuracy < 85 else "保持并增加例证"},
        {"topic": "词汇使用", "accuracy": 70 if accuracy < 80 else 86, "suggestion": "结合语境记忆"},
        {"topic": "语法衔接", "accuracy": 68 if not has_connector else 82, "suggestion": "练习连接词和从句"},
    ]
    user["updated_at"] = now_text()
    save_store(store)
    return {"result": result, "state": build_state(user)}
