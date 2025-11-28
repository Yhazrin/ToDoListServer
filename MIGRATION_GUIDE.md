# Flask-Migrate 使用指南

## ✅ 配置已完成

Flask-Migrate 已成功集成到项目中！

## 📁 文件说明

- `app.py` - 已集成 Flask-Migrate
- `manage.py` - Flask CLI 管理脚本
- `migrations/` - 迁移脚本目录（自动生成）

## 🚀 快速开始

### 1. 标记现有数据库（首次使用，只需一次）

由于数据库已经存在，需要标记为当前版本：

```bash
python3 manage.py db stamp head
```

这会将现有数据库标记为"已迁移"状态。

### 2. 以后修改模型时的流程

```bash
# 1. 修改模型文件（比如 models/user.py）

# 2. 生成迁移脚本
python3 manage.py db migrate -m "添加email字段"

# 3. 查看生成的迁移脚本（可选）
# 编辑 migrations/versions/xxx_add_email.py

# 4. 执行迁移
python3 manage.py db upgrade

# ✅ 完成！
```

## 📝 常用命令

### 查看当前版本
```bash
python3 manage.py db current
```

### 查看迁移历史
```bash
python3 manage.py db history
```

### 生成迁移脚本
```bash
python3 manage.py db migrate -m "描述你的改动"
```

### 执行迁移（升级）
```bash
python3 manage.py db upgrade
```

### 回退迁移（降级）
```bash
# 回退到上一个版本
python3 manage.py db downgrade

# 回退到指定版本
python3 manage.py db downgrade <revision>
```

### 查看迁移详情
```bash
python3 manage.py db show <revision>
```

## 💡 使用示例

### 示例1：添加新字段

```python
# 1. 修改 models/user.py
class User(db.Model):
    username = db.Column(...)
    password = db.Column(...)
    email = db.Column(db.String(120))  # 新增字段

# 2. 生成迁移
python3 manage.py db migrate -m "添加email字段到User表"

# 3. 执行迁移
python3 manage.py db upgrade
```

### 示例2：添加新表

```python
# 1. 创建新模型 models/notification.py
class Notification(db.Model):
    id = db.Column(...)
    message = db.Column(...)

# 2. 在 models/__init__.py 中导出
from .notification import Notification

# 3. 生成迁移
python3 manage.py db migrate -m "添加Notification表"

# 4. 执行迁移
python3 manage.py db upgrade
```

### 示例3：修改字段类型

```python
# 1. 修改模型
class Task(db.Model):
    status = db.Column(db.Integer)  # 从String改为Integer

# 2. 生成迁移
python3 manage.py db migrate -m "将Task.status改为Integer"

# 3. 检查生成的迁移脚本（可能需要手动调整数据转换逻辑）

# 4. 执行迁移
python3 manage.py db upgrade
```

## ⚠️ 注意事项

### 1. 首次使用

如果数据库已经存在（有数据），需要先标记：

```bash
python3 manage.py db stamp head
```

### 2. 迁移前备份

在生产环境执行迁移前，**务必备份数据库**！

```bash
# SQLite 备份
cp instance/todolist.db instance/todolist.db.backup
```

### 3. 检查生成的迁移脚本

执行 `migrate` 后，**检查生成的迁移脚本**，确保：
- ✅ 没有遗漏的字段
- ✅ 数据转换逻辑正确（如果需要）
- ✅ 没有破坏性变更

### 4. 测试环境先验证

在生产环境执行前，**先在测试环境验证**迁移脚本。

## 🔧 故障排除

### 问题：迁移时出现错误

```bash
# 查看详细错误信息
python3 manage.py db upgrade --sql

# 手动检查迁移脚本
cat migrations/versions/<latest_revision>.py
```

### 问题：迁移版本不同步

```bash
# 查看当前版本
python3 manage.py db current

# 手动标记版本
python3 manage.py db stamp <revision>
```

### 问题：需要重置迁移

```bash
# ⚠️ 危险操作！仅在开发环境使用
rm -rf migrations/
python3 manage.py db init
python3 manage.py db migrate -m "初始迁移"
python3 manage.py db upgrade
```

## 📚 与 db.create_all() 的关系

**现在不再需要 `db.create_all()`！**

迁移系统会自动管理数据库结构。

### 建议修改

在 `app.py` 中，可以移除或注释掉：

```python
# 旧方式（不推荐）
# with app.app_context():
#     db.create_all()

# 新方式（推荐）
# 使用迁移系统：python3 manage.py db upgrade
```

## 🎯 工作流程建议

### 开发新功能时

1. 修改模型定义
2. 生成迁移：`python3 manage.py db migrate -m "功能描述"`
3. 检查迁移脚本
4. 执行迁移：`python3 manage.py db upgrade`
5. 测试功能
6. 提交代码（包括迁移脚本）

### 部署到生产环境时

1. 备份数据库
2. 拉取最新代码（包括迁移脚本）
3. 执行迁移：`python3 manage.py db upgrade`
4. 验证数据库结构
5. 重启应用

## 📞 帮助

```bash
# 查看所有可用命令
python3 manage.py db --help

# 查看特定命令帮助
python3 manage.py db migrate --help
```

## ✅ 完成！

现在你可以：
- ✅ 安全地修改数据库结构
- ✅ 保留现有数据
- ✅ 追踪所有数据库变更
- ✅ 回滚错误的更改

开始使用吧！

