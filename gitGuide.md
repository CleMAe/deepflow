# 团队协作 Git 速成指南 (Git Guild)

作为开发者，熟练掌握 Git 是高效团队协作的基石。本指南提炼了日常开发中最核心的 Git 操作，所有指令均可直接复制粘贴使用。

在多人协作项目中，核心原则是：**永远不要直接在 `main`（或 `master`）分支上开发，所有新功能都在独立分支上完成。**

## 1. 分支管理 (Branch & Checkout)

分支让你拥有一个独立的工作空间，不会影响主代码库和其他队友的代码。

### 创建并切换到新分支（最常用）

```bash
git checkout -b feature/your-module-name
```

注：现代 Git 也推荐使用：

```bash
git switch -c feature/your-module-name
```

### 查看所有本地分支

```bash
git branch
```

### 切换回已有分支（如主干）

```bash
git checkout main
```

### 删除本地已合并的分支（保持工作区整洁）

```bash
git branch -d feature/your-module-name
```

注：如果分支未合并但你确定要丢弃，使用大写 `-D` 强制删除。

## 2. 基础工作流 (Add & Commit)

当你在自己的分支上完成了代码修改，需要将它们保存（提交）到本地仓库。

### 查看当前修改状态

```bash
git status
```

### 将所有修改添加到暂存区

```bash
git add .
```

注：如果只想添加特定文件，可使用：

```bash
git add <文件名>
```

### 提交修改并添加描述信息

```bash
git commit -m "feat: 新增登录页面基础UI"
```

规范建议：

- `feat:` 表示新功能
- `fix:` 表示修复 bug
- `docs:` 表示文档修改

## 3. 团队同步与代码合并 (Pull & Merge)

在多人协作中，你需要不断拉取别人的最新代码，并合并自己的代码。

### 拉取远程仓库的最新代码（防冲突必备）

```bash
git pull origin main
```

注：在提交你自己的代码前，或者每天开始工作前，务必执行此操作，保持代码最新。

### 将自己的本地分支推送到远程仓库（供队友查看或提 PR）

```bash
git push -u origin feature/your-module-name
```

注：第一次推送新分支需加 `-u`，之后在该分支下只需执行：

```bash
git push
```

### 在本地合并分支（例如将队友完成的模块合并到你的分支）

```bash
git merge other-feature-branch
```

## 4. 标准多人协作最佳实践 (Copy & Paste 流)

这是你在团队中开发一个新功能的标准动作，严格按照此顺序可以避免 90% 的协作问题：

```bash
# 1. 确保你在主干分支，并拉取团队最新代码
git checkout main
git pull origin main

# 2. 基于最新的 main，创建你的开发分支
git checkout -b feat/my-new-task

# 3. ---> 这里是你写代码的时间 <---

# 4. 开发完成，保存你的工作
git add .
git commit -m "feat: 完成了模块X的核心功能"

# 5. 关键步骤：再次拉取主干最新代码，防止队友在此期间有新提交导致冲突
git pull origin main

# 6. 推送你的分支到云端
git push -u origin feat/my-new-task

# 7. 去 GitHub/GitLab 提交 Pull Request (PR) 申请合并到 main
```
