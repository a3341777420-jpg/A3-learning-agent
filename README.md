# A3 - 基于大模型的个性化资源生成与学习多智能体系统

## 📌 项目简介

本项目为第十五届中国软件杯 A3 赛题实现方案，构建一个基于大语言模型（LLM）的多智能体（Multi-Agent）学习系统。

系统面向英语学习场景，通过多个智能体协同工作，实现学习资源生成、个性化推荐、学习路径规划与答疑辅助，提升学习效率与个性化体验。


## 🚀 核心功能

- 🎯 个性化学习内容生成（词汇 / 阅读 / 写作）
- 🤖 多智能体协同（规划 Agent / 生成 Agent / 评估 Agent）
- 📚 学习路径自动规划
- 🧠 基于用户水平动态调整学习难度
- 📊 学习记录与反馈分析


## 🧩 系统架构

系统采用多 Agent 协作架构：

- **Planner Agent（规划智能体）**
  - 负责分析用户需求并拆解学习任务

- **Generator Agent（生成智能体）**
  - 负责生成学习内容（题目、文章、练习等）

- **Evaluator Agent（评估智能体）**
  - 对用户答案进行评分与反馈

- **Memory / RAG 模块（知识增强）**
  - 提供上下文记忆与知识检索能力


## 🛠️ 技术栈

- Backend：FastAPI / Python
- LLM：OpenAI API / DeepSeek API
- Frontend：Vue / React（可选）
- Database：MySQL / SQLite
- Vector DB：FAISS / Chroma（可选）
- Version Control：Git + GitHub

## 📂 项目结构示例
