# ToDoList 服务器

一个基于Flask的综合性服务器，为大学生项目组提供用户认证、项目组管理和聊天功能的完整解决方案。

## 项目架构

```
ToDoListServer/
├── __init__.py          # 包入口文件
├── app.py              # 主应用文件
├── config.py           # 配置文件
├── models.py           # 数据库模型
├── auth.py             # 认证蓝图
├── groups.py           # 项目组管理蓝图
├── requirements.txt    # 依赖包列表
└── README.md          # 项目文档
```

## 核心功能

### 1. 用户认证系统
#### 用户注册 (`POST /auth/register`)
- 用户名唯一性验证
- 邮箱可选提供（如提供则验证唯一性）
- 密码bcrypt加密存储
- 无输入验证（不检查用户名和密码是否为空）

#### 用户登录 (`POST /auth/login`)
- 支持用户名或邮箱登录
- 密码验证
- 账户状态检查
- 无输入验证（不检查用户名和密码是否为空）

#### 服务状态 (`GET /auth/status`)
- 服务健康检查
- 运行状态监控

### 2. 项目组管理系统
- **项目组创建**: 支持创建大学生项目组，包含项目信息和时间管理
- **成员管理**: 通过负责人ID关联用户，支持项目组成员管理
- **项目信息**: 包含项目标题、描述、开始日期和截止日期
- **状态管理**: 通过is_active字段进行项目组状态控制
- **联系信息**: 支持项目组联系方式存储

### 3. 聊天功能系统
- **消息发送**: 支持项目组内成员间的消息交流
- **多媒体支持**: 支持文本消息和文件分享（通过file_url）
- **消息回复**: 支持消息回复功能，构建对话线程
- **消息状态**: 支持消息软删除和已读状态跟踪
- **已读管理**: 精确跟踪每个用户对每条消息的已读状态

## 技术栈

- **Web框架**: Flask 2.3.3
- **数据库ORM**: SQLAlchemy 3.0.5
- **密码加密**: bcrypt 1.0.1
- **跨域支持**: Flask-CORS 4.0.0
- **数据库**: SQLite（可配置其他数据库）

## 安装和运行

### 1. 安装依赖
```bash
cd /root/ToDoListServer
pip install -r requirements.txt
```

### 2. 启动服务器
```bash
python app.py
```

服务器将在 `http://0.0.0.0:5000` 启动

## API 接口文档

### 用户注册
**POST** `/auth/register`

请求体：
```json
{
    "username": "testuser",
    "email": "test@example.com",  // 可选字段
    "password": "password123"
}
```

或者不提供邮箱：
```json
{
    "username": "testuser",
    "password": "password123"
}
```

成功响应（提供邮箱）：
```json
{
    "success": true,
    "message": "Registration successful",
    "user": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "is_active": true
    }
}
```

成功响应（不提供邮箱）：
```json
{
    "success": true,
    "message": "Registration successful",
    "user": {
        "id": 1,
        "username": "testuser",
        "email": null,
        "is_active": true
    }
}
```

### 用户登录
**POST** `/auth/login`

请求体：
```json
{
    "username": "testuser",  // 或使用邮箱
    "password": "password123"
}
```

成功响应：
```json
{
    "success": true,
    "message": "Login successful",
    "user": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",  // 如果用户注册时未提供邮箱，此字段为null
        "is_active": true
    }
}
```

### 用户登出
**POST** `/auth/logout`

请求体：
```json
{
    "username": "testuser"  // 或使用邮箱
}
```

成功响应：
```json
{
    "success": true,
    "message": "Logout successful",
    "user": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",  // 如果用户注册时未提供邮箱，此字段为null
        "is_active": true
    }
}
```

### 服务状态
**GET** `/auth/status`

响应：
```json
{
    "success": true,
    "message": "Auth service running",
    "service": "ToDoList Auth Service"
}
```

### 项目组管理

#### 创建项目组
**POST** `/groups/create`

请求体：
```json
{
    "leader_id": "abc123def456",
    "name": "AI项目组",
    "project_title": "智能聊天机器人",
    "description": "开发一个基于AI的聊天机器人",
    "due_date": "2024-12-31T23:59:59"
}
```

成功响应：
```json
{
    "success": true,
    "message": "Group created successfully",
    "group": {
        "id": "xyz789abc123",
        "name": "AI项目组",
        "project_title": "智能聊天机器人",
        "description": "开发一个基于AI的聊天机器人",
        "leader_id": "abc123def456",
        "start_date": null,
        "due_date": "2024-12-31",
        "is_active": true,
        "contact_info": null,
        "invite_code": "xXfqA9rP"
    }
}
```

#### 加入项目组
**POST** `/groups/join`

请求体：
```json
{
    "user_id": "def456ghi789",
    "group_id": "xyz789abc123"
}
```

成功响应：
```json
{
    "success": true,
    "message": "Successfully joined the group",
    "group": {
        "id": "xyz789abc123",
        "name": "AI项目组",
        "project_title": "智能聊天机器人",
        "description": "开发一个基于AI的聊天机器人",
        "leader_id": "abc123def456",
        "start_date": null,
        "due_date": "2024-12-31",
        "is_active": true,
        "contact_info": null
    },
    "user": {
        "id": "def456ghi789",
        "username": "member1",
        "email": "member1@example.com",
        "is_active": true
    }
}
```

#### 通过邀请码加入项目组
**POST** `/groups/join-by-code`

请求体：
```json
{
    "user_id": "def456ghi789",
    "invite_code": "xXfqA9rP"
}
```

成功响应：
```json
{
    "success": true,
    "message": "Successfully joined the group",
    "group": {
        "id": "xyz789abc123",
        "name": "AI项目组",
        "project_title": "智能聊天机器人",
        "description": "开发一个基于AI的聊天机器人",
        "leader_id": "abc123def456",
        "start_date": null,
        "due_date": "2024-12-31",
        "is_active": true,
        "contact_info": null,
        "invite_code": "xXfqA9rP"
    },
    "user": {
        "id": "def456ghi789",
        "username": "member1",
        "email": "member1@example.com",
        "is_active": true
    }
}
```

失败响应示例：
```json
{
    "success": false,
    "message": "Invalid invite code format"
}
```

```json
{
    "success": false,
    "message": "Invalid invite code"
}
```

```json
{
    "success": false,
    "message": "User is already a member of this group"
}
```

#### 获取用户项目组列表
**GET** `/groups/list/<user_id>`

成功响应：
```json
{
    "success": true,
    "message": "Successfully retrieved group list",
    "groups": [
        {
            "id": "xyz789abc123",
            "name": "AI项目组",
            "project_title": "智能聊天机器人",
            "description": "开发一个基于AI的聊天机器人",
            "leader_id": "abc123def456",
            "start_date": null,
            "due_date": "2024-12-31",
            "is_active": true,
            "contact_info": null,
            "invite_code": "xXfqA9rP"
        }
    ]
}
```

#### 获取项目组详细信息
**GET** `/groups/info/<group_id>`

成功响应：
```json
{
    "success": true,
    "message": "Successfully retrieved group information",
    "group": {
        "id": "xyz789abc123",
        "name": "AI项目组",
        "project_title": "智能聊天机器人",
        "description": "开发一个基于AI的聊天机器人",
        "leader_id": "abc123def456",
        "start_date": null,
        "due_date": "2024-12-31T23:59:59",
        "is_active": true,
        "contact_info": null,
        "invite_code": "xXfqA9rP",
        "members": [
            {
                "id": "def456ghi789",
                "username": "member1",
                "email": "member1@example.com"
            }
        ]
    }
}
```

#### 更新项目组信息
**PUT** `/groups/update/<group_id>`

请求体（所有字段都是可选的，只更新提供的字段）：
```json
{
    "name": "AI项目组-升级版",
    "project_title": "智能聊天机器人2.0",
    "description": "开发一个更智能的AI聊天机器人",
    "due_date": "2025-06-30T23:59:59",
    "contact_info": "联系邮箱: ai-team@example.com",
    "is_active": true
}
```

成功响应：
```json
{
    "success": true,
    "message": "Group updated successfully",
    "group": {
        "id": "xyz789abc123",
        "name": "AI项目组-升级版",
        "project_title": "智能聊天机器人2.0",
        "description": "开发一个更智能的AI聊天机器人",
        "leader_id": "abc123def456",
        "start_date": null,
        "due_date": "2025-06-30",
        "is_active": true,
        "contact_info": "联系邮箱: ai-team@example.com",
        "updated_at": "2024-01-15 14:30:25"
    }
}
```

#### 删除项目组
**DELETE** `/groups/delete/<group_id>`

成功响应：
```json
{
    "success": true,
    "message": "Group deleted successfully"
}
```

失败响应：
```json
{
    "success": false,
    "message": "Group not found"
}
```

### 聊天模块

#### 获取用户的聊天室列表
**GET** `/chat/rooms`

成功响应：
```json
[
    {
        "id": 1,
        "name": "General",
        "lastMessage": "Hello, world!",
        "lastMessageTimestamp": "2024-01-01T12:00:00Z",
        "unreadCount": 2
    }
]
```

#### 分页获取历史消息
**GET** `/chat/rooms/{roomId}/messages`

成功响应：
```json
{
    "messages": [
        {
            "id": 1,
            "roomId": 1,
            "senderId": "user1",
            "senderName": "John Doe",
            "content": "This is an old message.",
            "timestamp": "2024-01-01T11:59:00Z"
        }
    ],
    "page": 1,
    "pages": 1,
    "total": 1
}
```

#### 发送消息
**POST** `/chat/rooms/{roomId}/messages`

请求体：
```json
{
    "content": "Hello, everyone!"
}
```

成功响应：
```json
{
    "id": 2,
    "roomId": 1,
    "senderId": "user2",
    "senderName": "Jane Smith",
    "content": "Hello, everyone!",
    "timestamp": "2024-01-01T12:00:10Z"
}
```

#### WebSocket 协议

- **订阅房间**: 客户端连接后，发送以下消息来订阅房间：
  ```json
  {
      "type": "subscribe",
      "roomId": 101
  }
  ```

- **新消息广播**: 当有新消息时，服务器向所有订阅者广播以下消息：
  ```json
  {
      "type": "new_message",
      "payload": { ... } // 完整的消息对象
  }
  ```

## 安全特性

1. **密码加密**: 使用bcrypt算法加密存储密码
2. **Token认证**: 所有聊天模块的端点都需要Token认证
3. **输入验证**: 基础的用户输入验证和清理
4. **错误处理**: 完善的错误处理和响应
5. **数据库安全**: 使用ORM防止SQL注入
6. **灵活注册**: 支持邮箱可选的用户注册

## 配置说明

### 环境变量
- `SECRET_KEY`: Flask应用密钥
- `DATABASE_URL`: 数据库连接URL
- `FLASK_ENV`: 运行环境（development/production）

### 配置类
- `DevelopmentConfig`: 开发环境配置
- `ProductionConfig`: 生产环境配置

## 数据库模型

### 数据库兼容性说明
为了确保与SQLite数据库的完全兼容性，本项目将所有日期和时间字段设计为字符串类型：
- **日期字段**：使用YYYY-MM-DD格式存储（如：2024-12-31）
- **时间字段**：使用YYYY-MM-DD HH:MM:SS格式存储（如：2024-12-31 23:59:59）

这种设计的优势：
1. **跨数据库兼容**：避免不同数据库系统对日期时间类型的差异处理
2. **简化部署**：无需考虑时区配置和日期格式转换
3. **易于调试**：日期时间以可读字符串形式直接存储和显示
4. **灵活处理**：应用层可以根据需要灵活解析和格式化日期

### User 模型
- `id`: 主键（16位UUID）
- `username`: 用户名（唯一，必填）
- `email`: 邮箱（可选，如提供则唯一）
- `password_hash`: 加密后的密码
- `is_active`: 账户状态

### ProjectGroup 模型（项目组表）
- `id`: 主键（16位UUID）
- `name`: 项目组名称（唯一，必填）
- `project_title`: 项目标题（必填）
- `description`: 项目描述（可选）
- `leader_id`: 项目组负责人ID（外键关联User表）
- `start_date`: 项目开始日期（字符串格式YYYY-MM-DD，可选）
- `due_date`: 项目截止日期（字符串格式YYYY-MM-DD，必填）
- `is_active`: 项目组状态（布尔值）
- `contact_info`: 联系信息（可选）

### GroupMessage 模型（聊天消息表）
- `id`: 主键（16位UUID）
- `group_id`: 项目组ID（外键关联ProjectGroup表）
- `sender_id`: 发送者ID（外键关联User表）
- `message_type`: 消息类型（text/file/image等）
- `content`: 消息内容（必填）
- `file_url`: 文件URL（可选，用于文件分享）
- `reply_to_id`: 回复消息ID（可选，外键关联GroupMessage表）
- `sent_at`: 发送时间（字符串格式YYYY-MM-DD HH:MM:SS）
- `is_deleted`: 软删除标记（布尔值）

### MessageReadStatus 模型（消息已读状态表）
- `id`: 主键（16位UUID）
- `message_id`: 消息ID（外键关联GroupMessage表）
- `user_id`: 用户ID（外键关联User表）
- `read_at`: 已读时间（字符串格式YYYY-MM-DD HH:MM:SS）
- 唯一约束：每个用户对每条消息只能有一个已读记录

## 测试示例

### 注册用户（提供邮箱）
```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 注册用户（不提供邮箱）
```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser2",
    "password": "password123"
  }'
```

### 使用curl测试登录
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

### 使用curl测试登出
```bash
curl -X POST http://localhost:5000/auth/logout \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser"
  }'
```

### 项目组管理测试示例

#### 创建项目组
```bash
curl -X POST http://localhost:5000/groups/create \
  -H "Content-Type: application/json" \
  -d '{
    "leader_id": "abc123def456",
    "name": "AI项目组",
    "project_title": "智能聊天机器人",
    "description": "开发一个基于AI的聊天机器人",
    "due_date": "2024-12-31T23:59:59"
  }'
```

#### 更新项目组信息
```bash
curl -X PUT http://localhost:5000/groups/update/xyz789abc123 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AI项目组-升级版",
    "project_title": "智能聊天机器人2.0",
    "description": "开发一个更智能的AI聊天机器人",
    "due_date": "2025-06-30T23:59:59",
    "contact_info": "联系邮箱: ai-team@example.com"
  }'
```

#### 删除项目组
```bash
curl -X DELETE http://localhost:5000/groups/delete/xyz789abc123
```

#### 加入项目组
```bash
curl -X POST http://localhost:5000/groups/join \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "def456ghi789",
    "group_id": "xyz789abc123"
  }'
```

#### 获取用户项目组列表
```bash
curl -X GET http://localhost:5000/groups/list/def456ghi789
```

#### 获取项目组详细信息
```bash
curl -X GET http://localhost:5000/groups/info/xyz789abc123
```

## 扩展建议

### 用户认证扩展
1. **JWT认证**: 添加JWT token支持
2. **邮箱验证**: 注册后邮箱验证功能
3. **密码重置**: 忘记密码重置功能
4. **用户角色**: 用户权限和角色管理

### 项目组管理扩展
5. **成员邀请**: 项目组成员邀请和加入机制
6. **权限管理**: 项目组内角色权限分配
7. **项目进度**: 项目进度跟踪和里程碑管理
8. **文件管理**: 项目文件上传和版本控制

### 聊天功能扩展
9. **实时通信**: WebSocket支持实时消息推送
10. **消息搜索**: 聊天记录搜索功能
11. **消息通知**: 未读消息提醒和推送
12. **表情和富文本**: 支持表情符号和富文本消息

### 系统优化
13. **API限流**: 防止暴力破解和滥用
14. **日志记录**: 详细的操作日志
15. **单元测试**: 完整的测试覆盖
16. **性能优化**: 数据库查询优化和缓存机制