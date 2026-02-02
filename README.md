# AI 编程效率管理系统

本项目包含 AI 编程效率考核的完整解决方案，包括任务管理 Skill、效率追踪平台和工作流规范。

## 📁 目录结构

```
skills/
├── spec-task/              # 任务生命周期管理 Skill
│   ├── SKILL.md            # Skill 使用说明
│   └── sync.py             # 平台同步脚本
├── team-skill-platform/    # 效率追踪 Web 平台
│   ├── backend/            # FastAPI 后端
│   ├── frontend/           # React + Vite 前端
│   └── docker-compose.yml  # Docker 部署配置
├── openspec/               # 变更提案规范
│   ├── AGENTS.md           # OpenSpec 指南
│   └── changes/            # 变更提案目录
├── 任务清单.md              # 团队任务清单
└── AGENTS.md               # 项目开发规则
```

## 🚀 快速开始

### 1. 启动效率追踪平台

```bash
cd team-skill-platform

# Docker 方式（推荐）
docker-compose up -d

# 或本地开发
cd backend && pip install -r requirements.txt && uvicorn main:app --reload
cd frontend && npm install && npm run dev
```

访问：http://localhost:5174

### 2. 使用 spec-task Skill

AI 助手会自动识别并使用此 Skill 管理任务生命周期：

1. **规划阶段** - 创建变更提案 (`/openspec-proposal`)
2. **执行阶段** - 按提案实现功能
3. **验证阶段** - 测试并验收
4. **归档阶段** - 同步到平台

### 3. 同步任务到平台

```bash
# 首次运行会提示输入凭据
python spec-task/sync.py -f 任务清单.md
```

## 📊 效率指标

| 指标 | 说明 | 计算方式 |
|------|------|----------|
| **效率得分** | 综合评估 | `复杂度 / (交互轮次 × (1 + 返工次数)) × 100` |
| **首次通过率** | 无返工比例 | `无返工任务数 / 总任务数` |
| **交互轮次** | 用户干预次数 | 手动统计 |
| **返工次数** | 验收后修改次数 | 手动统计 |

## 📝 开发规范

详见 [AGENTS.md](AGENTS.md) 中的项目规则。

## 🔗 相关文档

- [spec-task Skill 说明](spec-task/SKILL.md)
- [平台 ROADMAP](team-skill-platform/ROADMAP.md)
- [OpenSpec 规范](openspec/AGENTS.md)
