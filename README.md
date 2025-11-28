# ToDoList 服务器

一个基于Flask的综合性服务器，为大学生项目组提供完整的协作管理解决方案。包括用户认证、项目组管理、任务管理、文件管理、日历事件、聊天功能和Widget数据接口等核心功能。

## 项目架构

```
ToDoListServer/
├── __init__.py          # 包入口文件
├── app.py              # 主应用文件
├── config.py           # 配置文件
├── models/             # 数据库模型模块
│   ├── __init__.py     # 统一导出
│   ├── base.py         # 数据库初始化
│   ├── user.py         # 用户和OAuth模型
│   ├── group.py        # 项目组模型
│   ├── chat.py         # 聊天消息模型
│   ├── task.py         # 任务模型
│   ├── file.py         # 文件模型
│   └── calendar.py     # 日历事件模型
├── auth.py             # 认证蓝图
├── user.py             # 用户资料蓝图
├── oauth.py            # OAuth认证蓝图
├── groups.py           # 项目组管理蓝图
├── tasks.py            # 任务管理蓝图
├── files.py            # 文件管理蓝图
├── chat.py             # 聊天功能蓝图
├── calendar.py         # 日历功能蓝图
├── widget.py           # Widget端点蓝图
├── start_server.sh     # 服务器管理脚本
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
- **任务注入**: 支持在聊天中引用任务
- **消息回复**: 支持消息回复功能，构建对话线程
- **消息状态**: 支持消息软删除和已读状态跟踪
- **已读管理**: 精确跟踪每个用户对每条消息的已读状态

### 4. 用户资料管理
- **资料查看**: 获取当前用户资料信息
- **资料更新**: 支持更新用户名、邮箱和密码
- **Token认证**: 基于Token的当前用户识别

### 5. OAuth第三方登录
- **Google登录**: 支持Google OAuth登录和账户绑定
- **GitHub登录**: 支持GitHub OAuth登录和账户绑定
- **账户绑定**: 可将第三方账户绑定到现有账户
- **自动注册**: 首次使用第三方登录自动创建账户

### 6. 任务管理系统
- **任务CRUD**: 完整的任务创建、读取、更新、删除功能
- **层级任务**: 支持父子任务的树形结构
- **任务筛选**: 支持按用户、项目组筛选任务
- **任务树**: 获取项目组的完整任务树结构
- **任务移动**: 支持移动任务到不同父任务或项目组
- **任务附件**: 支持为任务添加和删除附件

### 7. 文件管理系统
- **文件上传**: 支持多种文件类型上传（图片、视频、音频、文档等）
- **文件预览**: 支持文件预览和下载
- **文件分组**: 支持按项目组组织文件
- **文件管理**: 完整的文件信息查询和删除功能

### 8. 日历事件系统
- **事件管理**: 完整的日历事件CRUD功能
- **任务关联**: 支持从任务创建日历事件
- **日期筛选**: 支持按日期范围查询事件

### 9. Widget数据接口
- **今日任务**: 获取今日到期的任务列表
- **今日事件**: 获取今日的日历事件列表

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

#### 发送消息（支持多媒体和任务注入）
**POST** `/chat/rooms/{roomId}/messages`

请求体（支持多种消息类型）：
```json
{
    "messageType": "text",  // text, image, video, audio, file, task
    "content": "Hello, everyone!",
    "fileUrl": "file_id_or_url",  // 文件类型消息需要
    "taskId": "task_id"  // 任务类型消息需要
}
```

成功响应：
```json
{
    "id": "msg123",
    "roomId": "group123",
    "senderId": "user123",
    "senderName": "Jane Smith",
    "messageType": "text",
    "content": "Hello, everyone!",
    "fileUrl": null,
    "taskId": null,
    "timestamp": "2024-01-01 12:00:10"
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

### 用户资料管理

#### 获取当前用户资料
**GET** `/user/profile`

**需要认证**: `Authorization: Bearer <token>`

成功响应：
```json
{
    "success": true,
    "message": "Profile retrieved successfully",
    "user": {
        "id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "is_active": true
    }
}
```

#### 更新当前用户资料
**PUT** `/user/profile`

**需要认证**: `Authorization: Bearer <token>`

请求体（所有字段都是可选的）：
```json
{
    "username": "newusername",
    "email": "newemail@example.com",
    "password": "newpassword123"
}
```

成功响应：
```json
{
    "success": true,
    "message": "Profile updated successfully",
    "user": {
        "id": "user123",
        "username": "newusername",
        "email": "newemail@example.com",
        "is_active": true
    }
}
```

### OAuth第三方登录

#### Google登录/绑定
**POST** `/auth/google/login`

请求体：
```json
{
    "access_token": "google_access_token",
    "user_id": "existing_user_id"  // 可选，用于绑定到现有账户
}
```

成功响应（新账户）：
```json
{
    "success": true,
    "message": "Account created and logged in successfully",
    "user": {
        "id": "user123",
        "username": "google_user",
        "email": "user@gmail.com",
        "is_active": true
    },
    "token": "user123"
}
```

#### GitHub登录/绑定
**POST** `/auth/github/login`

请求体：
```json
{
    "access_token": "github_access_token",
    "user_id": "existing_user_id"  // 可选，用于绑定到现有账户
}
```

成功响应（绑定现有账户）：
```json
{
    "success": true,
    "message": "GitHub account linked successfully",
    "user": {
        "id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "is_active": true
    },
    "oauth_account": {
        "id": "oauth123",
        "provider": "github",
        "email": "user@github.com"
    }
}
```

### 任务管理系统

#### 获取任务列表
**GET** `/tasks?projectId={projectId}&userId={userId}`

**需要认证**: `Authorization: Bearer <token>`

成功响应：
```json
{
    "success": true,
    "message": "Tasks retrieved successfully",
    "tasks": [
        {
            "id": "task123",
            "user_id": "user123",
            "project_id": "group123",
            "parent_task_id": null,
            "title": "完成API设计",
            "description": "设计RESTful API",
            "status": "in_progress",
            "priority": "high",
            "due_date": "2024-12-31",
            "created_at": "2024-01-01 10:00:00",
            "updated_at": "2024-01-02 14:30:00",
            "completed_at": null,
            "is_deleted": false,
            "position": 0
        }
    ]
}
```

#### 创建任务
**POST** `/tasks`

**需要认证**: `Authorization: Bearer <token>`

请求体：
```json
{
    "title": "完成API设计",
    "description": "设计RESTful API",
    "project_id": "group123",
    "parent_task_id": null,
    "status": "pending",
    "priority": "high",
    "due_date": "2024-12-31"
}
```

成功响应：
```json
{
    "success": true,
    "message": "Task created successfully",
    "task": {
        "id": "task123",
        "title": "完成API设计",
        "status": "pending",
        "priority": "high",
        "due_date": "2024-12-31",
        ...
    }
}
```

#### 获取任务详情
**GET** `/tasks/{taskId}`

**需要认证**: `Authorization: Bearer <token>`

#### 更新任务
**PUT** `/tasks/{taskId}`

**需要认证**: `Authorization: Bearer <token>`

请求体（所有字段可选）：
```json
{
    "title": "更新后的任务标题",
    "status": "completed",
    "priority": "medium",
    "due_date": "2024-12-31"
}
```

#### 删除任务
**DELETE** `/tasks/{taskId}`

**需要认证**: `Authorization: Bearer <token>`

#### 获取任务树
**GET** `/tasks/tree/{groupId}`

**需要认证**: `Authorization: Bearer <token>`

成功响应：
```json
{
    "success": true,
    "message": "Task tree retrieved successfully",
    "tree": [
        {
            "id": "task123",
            "title": "父任务",
            "children": [
                {
                    "id": "task456",
                    "title": "子任务1",
                    "children": []
                }
            ]
        }
    ]
}
```

#### 移动任务
**PUT** `/tasks/{taskId}/move`

**需要认证**: `Authorization: Bearer <token>`

请求体：
```json
{
    "parent_task_id": "new_parent_id",  // 可选，null表示移到根级
    "project_id": "new_project_id",  // 可选
    "position": 0
}
```

### 任务附件系统

#### 添加任务附件
**POST** `/tasks/{taskId}/attachments`

**需要认证**: `Authorization: Bearer <token>`

请求体：
```json
{
    "file_id": "file123"
}
```

#### 获取任务附件列表
**GET** `/tasks/{taskId}/attachments`

**需要认证**: `Authorization: Bearer <token>`

成功响应：
```json
{
    "success": true,
    "message": "Attachments retrieved successfully",
    "attachments": [
        {
            "id": "file123",
            "filename": "document.pdf",
            "file_type": "document",
            "file_size": 1024000,
            ...
        }
    ]
}
```

#### 删除任务附件
**DELETE** `/tasks/{taskId}/attachments/{fileId}`

**需要认证**: `Authorization: Bearer <token>`

### 文件管理系统

#### 上传文件
**POST** `/files/upload`

**需要认证**: `Authorization: Bearer <token>`

**Content-Type**: `multipart/form-data`

表单字段：
- `file`: 文件（必需）
- `group_id`: 项目组ID（可选）

成功响应：
```json
{
    "success": true,
    "message": "File uploaded successfully",
    "file": {
        "id": "file123",
        "filename": "document.pdf",
        "file_path": "20240101120000_document.pdf",
        "file_type": "document",
        "file_size": 1024000,
        "mime_type": "application/pdf",
        "group_id": "group123",
        "created_at": "2024-01-01 12:00:00"
    }
}
```

#### 获取文件信息
**GET** `/files/{fileId}`

**需要认证**: `Authorization: Bearer <token>`

#### 删除文件
**DELETE** `/files/{fileId}`

**需要认证**: `Authorization: Bearer <token>`

#### 获取项目组文件列表
**GET** `/files/group/{groupId}`

**需要认证**: `Authorization: Bearer <token>`

#### 文件预览/下载
**GET** `/files/{fileId}/preview`

**需要认证**: `Authorization: Bearer <token>`

返回文件流，Content-Type 为文件的 MIME 类型。

### 日历事件系统

#### 获取日历事件列表
**GET** `/calendar/events?start_date=2024-01-01&end_date=2024-12-31`

**需要认证**: `Authorization: Bearer <token>`

成功响应：
```json
{
    "success": true,
    "message": "Events retrieved successfully",
    "events": [
        {
            "id": "event123",
            "user_id": "user123",
            "task_id": "task123",
            "title": "项目评审会议",
            "description": "讨论项目进度",
            "start_time": "2024-01-15 14:00:00",
            "end_time": "2024-01-15 16:00:00",
            "location": "会议室A",
            "created_at": "2024-01-01 10:00:00"
        }
    ]
}
```

#### 创建日历事件
**POST** `/calendar/events`

**需要认证**: `Authorization: Bearer <token>`

请求体：
```json
{
    "title": "项目评审会议",
    "description": "讨论项目进度",
    "start_time": "2024-01-15T14:00:00",
    "end_time": "2024-01-15T16:00:00",
    "location": "会议室A",
    "task_id": "task123"
}
```

#### 获取日历事件详情
**GET** `/calendar/events/{eventId}`

**需要认证**: `Authorization: Bearer <token>`

#### 更新日历事件
**PUT** `/calendar/events/{eventId}`

**需要认证**: `Authorization: Bearer <token>`

#### 删除日历事件
**DELETE** `/calendar/events/{eventId}`

**需要认证**: `Authorization: Bearer <token>`

#### 从任务创建日历事件
**POST** `/calendar/from-task/{taskId}`

**需要认证**: `Authorization: Bearer <token>`

请求体：
```json
{
    "start_time": "2024-01-15T14:00:00",
    "end_time": "2024-01-15T16:00:00",
    "location": "会议室A"
}
```

### Widget数据接口

#### 获取今日任务
**GET** `/widget/today-tasks`

**需要认证**: `Authorization: Bearer <token>`

成功响应：
```json
{
    "success": true,
    "message": "Today tasks retrieved successfully",
    "date": "2024-01-15",
    "tasks": [
        {
            "id": "task123",
            "title": "完成API设计",
            "status": "pending",
            "priority": "high",
            "due_date": "2024-01-15"
        }
    ],
    "count": 1
}
```

#### 获取今日事件
**GET** `/widget/today-events`

**需要认证**: `Authorization: Bearer <token>`

成功响应：
```json
{
    "success": true,
    "message": "Today events retrieved successfully",
    "date": "2024-01-15",
    "events": [
        {
            "id": "event123",
            "title": "项目评审会议",
            "start_time": "2024-01-15 14:00:00",
            "end_time": "2024-01-15 16:00:00"
        }
    ],
    "count": 1
}
```

### 项目组增强功能

#### 获取项目组成员列表
**GET** `/groups/{groupId}/members`

**需要认证**: `Authorization: Bearer <token>`

成功响应：
```json
{
    "success": true,
    "message": "Members retrieved successfully",
    "members": [
        {
            "id": "user123",
            "username": "member1",
            "email": "member1@example.com",
            "is_active": true,
            "is_leader": true
        }
    ],
    "count": 1
}
```

#### 获取项目组概览
**GET** `/groups/{groupId}/overview`

**需要认证**: `Authorization: Bearer <token>`

成功响应：
```json
{
    "success": true,
    "message": "Group overview retrieved successfully",
    "overview": {
        "group": {
            "id": "group123",
            "name": "AI项目组",
            ...
        },
        "statistics": {
            "members": 5,
            "tasks": {
                "total": 20,
                "completed": 10,
                "pending": 8,
                "in_progress": 2,
                "today": 3
            },
            "files": 15,
            "events_today": 2
        },
        "progress": {
            "task_completion_rate": 50.0
        }
    }
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
- `message_type`: 消息类型（text, image, video, audio, file, task）
- `content`: 消息内容（必填）
- `file_url`: 文件URL或文件ID（可选，用于文件分享）
- `task_id`: 关联的任务ID（可选，用于任务注入）
- `reply_to_id`: 回复消息ID（可选，外键关联GroupMessage表）
- `sent_at`: 发送时间（字符串格式YYYY-MM-DD HH:MM:SS）
- `is_deleted`: 软删除标记（布尔值）

### MessageReadStatus 模型（消息已读状态表）
- `id`: 主键（16位UUID）
- `message_id`: 消息ID（外键关联GroupMessage表）
- `user_id`: 用户ID（外键关联User表）
- `read_at`: 已读时间（字符串格式YYYY-MM-DD HH:MM:SS）
- 唯一约束：每个用户对每条消息只能有一个已读记录

### Task 模型（任务表）
- `id`: 主键（16位UUID）
- `user_id`: 用户ID（外键关联User表）
- `project_id`: 项目组ID（外键关联ProjectGroup表，可选）
- `parent_task_id`: 父任务ID（外键关联Task表，支持层级结构）
- `title`: 任务标题（必填）
- `description`: 任务描述（可选）
- `status`: 任务状态（pending, in_progress, completed, cancelled）
- `priority`: 优先级（low, medium, high, urgent）
- `due_date`: 截止日期（字符串格式YYYY-MM-DD，可选）
- `created_at`: 创建时间（字符串格式YYYY-MM-DD HH:MM:SS）
- `updated_at`: 更新时间（字符串格式YYYY-MM-DD HH:MM:SS）
- `completed_at`: 完成时间（字符串格式YYYY-MM-DD HH:MM:SS，可选）
- `is_deleted`: 软删除标记（布尔值）
- `position`: 排序位置（整数）

### TaskFile 模型（任务附件关联表）
- `id`: 主键（16位UUID）
- `task_id`: 任务ID（外键关联Task表）
- `file_id`: 文件ID（外键关联SharedFile表）
- `created_at`: 创建时间（字符串格式YYYY-MM-DD HH:MM:SS）
- 唯一约束：每个任务对每个文件只能有一个关联记录

### SharedFile 模型（共享文件表）
- `id`: 主键（16位UUID）
- `user_id`: 用户ID（外键关联User表）
- `group_id`: 项目组ID（外键关联ProjectGroup表，可选）
- `filename`: 文件名（必填）
- `file_path`: 文件存储路径（必填）
- `file_type`: 文件类型（image, video, audio, document, other）
- `file_size`: 文件大小（字节，整数）
- `mime_type`: MIME类型（可选）
- `thumbnail_path`: 缩略图路径（可选，用于图片/视频预览）
- `created_at`: 创建时间（字符串格式YYYY-MM-DD HH:MM:SS）
- `updated_at`: 更新时间（字符串格式YYYY-MM-DD HH:MM:SS）
- `is_deleted`: 软删除标记（布尔值）

### OAuthAccount 模型（OAuth账户绑定表）
- `id`: 主键（16位UUID）
- `user_id`: 用户ID（外键关联User表）
- `provider`: OAuth提供商（google, github）
- `provider_user_id`: OAuth提供商返回的用户ID
- `email`: 邮箱（可选）
- `access_token`: 访问令牌（加密存储，可选）
- `refresh_token`: 刷新令牌（加密存储，可选）
- `token_expires_at`: 令牌过期时间（字符串格式YYYY-MM-DD HH:MM:SS，可选）
- `created_at`: 创建时间（字符串格式YYYY-MM-DD HH:MM:SS）
- `updated_at`: 更新时间（字符串格式YYYY-MM-DD HH:MM:SS）
- 唯一约束：每个用户在同一个提供商只能绑定一个账户

### CalendarEvent 模型（日历事件表）
- `id`: 主键（16位UUID）
- `user_id`: 用户ID（外键关联User表）
- `task_id`: 任务ID（外键关联Task表，可选）
- `title`: 事件标题（必填）
- `description`: 事件描述（可选）
- `start_time`: 开始时间（字符串格式YYYY-MM-DD HH:MM:SS，必填）
- `end_time`: 结束时间（字符串格式YYYY-MM-DD HH:MM:SS，必填）
- `location`: 地点（可选）
- `created_at`: 创建时间（字符串格式YYYY-MM-DD HH:MM:SS）
- `updated_at`: 更新时间（字符串格式YYYY-MM-DD HH:MM:SS）
- `is_deleted`: 软删除标记（布尔值）

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

### 用户资料管理测试示例

#### 获取用户资料
```bash
curl -X GET http://localhost:5000/user/profile \
  -H "Authorization: Bearer user_token_here"
```

#### 更新用户资料
```bash
curl -X PUT http://localhost:5000/user/profile \
  -H "Authorization: Bearer user_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newusername",
    "email": "newemail@example.com"
  }'
```

### OAuth登录测试示例

#### Google登录
```bash
curl -X POST http://localhost:5000/auth/google/login \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "google_access_token_here"
  }'
```

#### GitHub登录
```bash
curl -X POST http://localhost:5000/auth/github/login \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "github_access_token_here"
  }'
```

### 任务管理测试示例

#### 创建任务
```bash
curl -X POST http://localhost:5000/tasks \
  -H "Authorization: Bearer user_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "完成API设计",
    "description": "设计RESTful API",
    "project_id": "group123",
    "priority": "high",
    "due_date": "2024-12-31"
  }'
```

#### 获取任务列表
```bash
curl -X GET "http://localhost:5000/tasks?projectId=group123" \
  -H "Authorization: Bearer user_token_here"
```

#### 获取任务树
```bash
curl -X GET http://localhost:5000/tasks/tree/group123 \
  -H "Authorization: Bearer user_token_here"
```

#### 更新任务
```bash
curl -X PUT http://localhost:5000/tasks/task123 \
  -H "Authorization: Bearer user_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "priority": "medium"
  }'
```

### 文件管理测试示例

#### 上传文件
```bash
curl -X POST http://localhost:5000/files/upload \
  -H "Authorization: Bearer user_token_here" \
  -F "file=@/path/to/file.pdf" \
  -F "group_id=group123"
```

#### 获取项目组文件列表
```bash
curl -X GET http://localhost:5000/files/group/group123 \
  -H "Authorization: Bearer user_token_here"
```

#### 文件预览
```bash
curl -X GET http://localhost:5000/files/file123/preview \
  -H "Authorization: Bearer user_token_here" \
  -o downloaded_file.pdf
```

### 日历事件测试示例

#### 创建日历事件
```bash
curl -X POST http://localhost:5000/calendar/events \
  -H "Authorization: Bearer user_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "项目评审会议",
    "start_time": "2024-01-15T14:00:00",
    "end_time": "2024-01-15T16:00:00",
    "location": "会议室A"
  }'
```

#### 从任务创建日历事件
```bash
curl -X POST http://localhost:5000/calendar/from-task/task123 \
  -H "Authorization: Bearer user_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "2024-01-15T14:00:00",
    "end_time": "2024-01-15T16:00:00"
  }'
```

### Widget测试示例

#### 获取今日任务
```bash
curl -X GET http://localhost:5000/widget/today-tasks \
  -H "Authorization: Bearer user_token_here"
```

#### 获取今日事件
```bash
curl -X GET http://localhost:5000/widget/today-events \
  -H "Authorization: Bearer user_token_here"
```

## 服务器管理脚本

项目提供了 `start_server.sh` 脚本用于服务器管理：

```bash
# 启动服务器
./start_server.sh start

# 停止服务器
./start_server.sh stop

# 重启服务器
./start_server.sh restart

# 查看服务器状态
./start_server.sh status

# 查看服务器日志
./start_server.sh logs

# 测试所有API端点
./start_server.sh test

# 显示帮助信息
./start_server.sh help
```

测试命令会自动检测所有49个API端点的连通性，包括原有端点和新增端点。

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

## 项目更新日志

### v2.0.0 - 功能扩展版本

#### 新增功能模块
- ✅ **用户资料管理**: 支持获取和更新当前用户资料
- ✅ **OAuth第三方登录**: 支持Google和GitHub OAuth登录和账户绑定
- ✅ **任务管理系统**: 完整的任务CRUD功能，支持层级任务结构
- ✅ **任务附件系统**: 支持为任务添加和管理附件
- ✅ **文件管理系统**: 支持文件上传、预览和管理，按项目组组织
- ✅ **日历事件系统**: 支持日历事件管理，可与任务关联
- ✅ **Widget数据接口**: 提供轻量级的今日任务和事件接口
- ✅ **项目组增强**: 新增成员列表和概览统计功能
- ✅ **聊天扩展**: 支持任务注入和多媒体消息类型

#### 代码结构优化
- ✅ **模型模块化**: 将数据库模型按功能模块拆分到 `models/` 目录
- ✅ **蓝图模块化**: 按功能模块创建独立的蓝图文件
- ✅ **API端点测试**: 在 `start_server.sh` 中添加了49个端点的自动化测试

#### 技术改进
- ✅ **权限控制**: 所有新增端点都使用Token认证
- ✅ **软删除机制**: 支持任务、文件、事件的软删除
- ✅ **数据验证**: 完善的数据验证和错误处理
- ✅ **RESTful设计**: 遵循RESTful API设计规范