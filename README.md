# 智学工坊 - AI 英语学习智能体

## 当前流程

1. 注册账号：昵称、手机号、密码
2. 登录账号：昵称、手机号、密码、验证码
3. 基础信息页：AI 询问专业、年级、学习目标
4. 英语水平测试页：词汇、语法、阅读、写作测试
5. 英语水平总结页：后端根据测试结果返回等级、得分、薄弱项和维度分数
6. 每日学习时长页：用户填写每天计划学习几个小时
7. 生成学习方案：后端根据专业、年级、目标、测试结果和每日时长生成画像、任务、资源、路径

## 启动方式

后端：

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

前端：

```powershell
python -m http.server 5174 -d dist
```

前端访问：

```text
http://127.0.0.1:5174
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

## 主要接口

- `GET /api/captcha`
- `POST /api/register`
- `POST /api/login`
- `GET /api/diagnostic/questions`
- `POST /api/onboarding/basic`
- `POST /api/onboarding/quiz`
- `GET /api/onboarding/summary/{user_id}`
- `POST /api/onboarding/hours`
- `GET /api/state/{user_id}`
- `POST /api/chat`
- `POST /api/tasks/toggle`
- `POST /api/evaluate`

## 重新构建前端到根目录 dist

```powershell
npx vite build client --outDir ..\dist --emptyOutDir
```

## 模型 API 接入

后端会代理请求大模型服务，前端不要直接保存或暴露 API Key。

PowerShell 启动后端前先设置：

```powershell
$env:DEEPSEEK_API_KEY="你的模型 API Key"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

前端默认请求 `http://127.0.0.1:8000`，如需修改可设置：

```powershell
$env:VITE_API_BASE="http://127.0.0.1:8000"
npm run dev
```

新增接口：

- `POST /api/ai/chat`

请求体示例：

```json
{
  "message": "帮我制定一个英语阅读提升计划",
  "history": []
}
```


