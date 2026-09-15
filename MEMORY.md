# 持久记忆（跨会话）

## 部署偏好（用户明确要求，2026-09-15）

- **Vercel 如果关联了 GitHub 仓库，不要用上传包（CLI `vercel deploy` / `--archive` / API 上传文件）的方式部署；一律使用分支提交（push 到分支）触发部署。**
- 本项目当前实现：`.github/workflows/vercel-deploy.yml`（push `master` → 重建 → 部署，仓库 Secret `VERCEL_TOKEN`）。若项目改配 Vercel 官方 Git 集成，则直接 push 分支、由 Vercel 自动构建部署，不再走 CI 上传。
- 手动紧急部署例外：仅在 Git 链路不可用时才允许 CLI 上传方式，事后说明原因。
