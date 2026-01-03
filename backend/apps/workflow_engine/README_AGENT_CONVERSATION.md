# Agent对话云端存储功能

## 功能说明

本功能允许将Agent对话内容上传到云端数据库，以便在不同电脑上继续对话。所有对话数据存储在PostgreSQL数据库中，支持跨设备同步。

## 数据库模型

### AgentConversation（对话会话）
- `title`: 对话标题
- `description`: 对话描述
- `user`: 关联的用户
- `metadata`: JSON格式的元数据（可存储模型类型、参数等）
- `is_active`: 是否活跃
- `is_archived`: 是否归档
- `created_time`: 创建时间
- `updated_time`: 更新时间
- `last_message_time`: 最后消息时间

### AgentMessage（对话消息）
- `conversation`: 所属对话会话
- `role`: 消息角色（user/assistant/system）
- `content`: 消息内容
- `metadata`: JSON格式的元数据
- `sequence`: 消息顺序
- `created_time`: 创建时间

## API接口

### 基础URL
```
/api/workflow/
```

### 对话管理接口

#### 1. 获取对话列表
```
GET /api/workflow/conversations/
```

查询参数：
- `is_active`: 是否活跃（true/false）
- `is_archived`: 是否归档（true/false）
- `search`: 搜索关键词（搜索标题和描述）

响应示例：
```json
[
  {
    "id": 1,
    "title": "Python编程问题",
    "description": "关于Python的讨论",
    "user": 1,
    "user_name": "admin",
    "is_active": true,
    "is_archived": false,
    "created_time": "2025-01-20T10:00:00Z",
    "updated_time": "2025-01-20T11:00:00Z",
    "last_message_time": "2025-01-20T11:00:00Z",
    "message_count": 10,
    "last_message_preview": "这是一个关于Python的问题..."
  }
]
```

#### 2. 创建新对话
```
POST /api/workflow/conversations/
```

请求体：
```json
{
  "title": "新对话",
  "description": "对话描述",
  "metadata": {
    "model": "gpt-4",
    "temperature": 0.7
  }
}
```

#### 3. 获取对话详情（包含所有消息）
```
GET /api/workflow/conversations/{id}/
```

#### 4. 更新对话
```
PUT /api/workflow/conversations/{id}/
PATCH /api/workflow/conversations/{id}/
```

#### 5. 删除对话
```
DELETE /api/workflow/conversations/{id}/
```

#### 6. 归档对话
```
POST /api/workflow/conversations/{id}/archive/
```

#### 7. 取消归档对话
```
POST /api/workflow/conversations/{id}/unarchive/
```

#### 8. 获取对话的所有消息
```
GET /api/workflow/conversations/{id}/messages/
```

#### 9. 向对话添加消息
```
POST /api/workflow/conversations/{id}/add_message/
```

请求体：
```json
{
  "role": "user",
  "content": "用户的消息内容",
  "metadata": {
    "tokens": 50
  }
}
```

#### 10. 获取最近的对话
```
GET /api/workflow/conversations/recent/
```

### 消息管理接口

#### 1. 获取消息列表
```
GET /api/workflow/messages/?conversation={conversation_id}
```

#### 2. 创建消息
```
POST /api/workflow/messages/
```

请求体：
```json
{
  "conversation": 1,
  "role": "assistant",
  "content": "助手的回复",
  "metadata": {
    "tokens": 100
  }
}
```

#### 3. 获取消息详情
```
GET /api/workflow/messages/{id}/
```

#### 4. 更新消息
```
PUT /api/workflow/messages/{id}/
PATCH /api/workflow/messages/{id}/
```

#### 5. 删除消息
```
DELETE /api/workflow/messages/{id}/
```

## 使用示例

### Python示例

```python
import requests

# 配置
BASE_URL = "http://localhost:8001/api/workflow"
headers = {
    "Authorization": "Bearer YOUR_TOKEN",  # 如果使用Token认证
    "Content-Type": "application/json"
}

# 1. 创建新对话
response = requests.post(
    f"{BASE_URL}/conversations/",
    json={
        "title": "Python编程问题",
        "description": "讨论Python相关的问题",
        "metadata": {
            "model": "gpt-4",
            "temperature": 0.7
        }
    },
    headers=headers
)
conversation = response.json()
conversation_id = conversation["id"]

# 2. 添加用户消息
response = requests.post(
    f"{BASE_URL}/conversations/{conversation_id}/add_message/",
    json={
        "role": "user",
        "content": "如何学习Python？",
        "metadata": {}
    },
    headers=headers
)

# 3. 添加助手回复
response = requests.post(
    f"{BASE_URL}/conversations/{conversation_id}/add_message/",
    json={
        "role": "assistant",
        "content": "学习Python可以从基础语法开始...",
        "metadata": {
            "tokens": 150
        }
    },
    headers=headers
)

# 4. 获取对话详情（包含所有消息）
response = requests.get(
    f"{BASE_URL}/conversations/{conversation_id}/",
    headers=headers
)
conversation_data = response.json()
messages = conversation_data["messages"]

# 5. 获取所有对话列表
response = requests.get(
    f"{BASE_URL}/conversations/",
    headers=headers
)
conversations = response.json()
```

### JavaScript示例

```javascript
const BASE_URL = 'http://localhost:8001/api/workflow';

// 1. 创建新对话
async function createConversation(title, description) {
  const response = await fetch(`${BASE_URL}/conversations/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // 如果使用Session认证，浏览器会自动处理Cookie
    },
    credentials: 'include',  // 包含Cookie
    body: JSON.stringify({
      title: title,
      description: description,
      metadata: {
        model: 'gpt-4',
        temperature: 0.7
      }
    })
  });
  return await response.json();
}

// 2. 添加消息
async function addMessage(conversationId, role, content) {
  const response = await fetch(
    `${BASE_URL}/conversations/${conversationId}/add_message/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        role: role,
        content: content,
        metadata: {}
      })
    }
  );
  return await response.json();
}

// 3. 获取对话详情
async function getConversation(conversationId) {
  const response = await fetch(
    `${BASE_URL}/conversations/${conversationId}/`,
    {
      credentials: 'include'
    }
  );
  return await response.json();
}

// 4. 获取对话列表
async function getConversations() {
  const response = await fetch(`${BASE_URL}/conversations/`, {
    credentials: 'include'
  });
  return await response.json();
}

// 使用示例
(async () => {
  // 创建对话
  const conversation = await createConversation(
    'Python学习',
    '讨论Python编程'
  );
  
  // 添加用户消息
  await addMessage(conversation.id, 'user', '如何学习Python？');
  
  // 添加助手回复
  await addMessage(conversation.id, 'assistant', '学习Python可以从基础语法开始...');
  
  // 获取完整对话
  const fullConversation = await getConversation(conversation.id);
  console.log('对话消息:', fullConversation.messages);
})();
```

## 数据库迁移

运行以下命令来创建数据库表：

```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
python manage.py migrate workflow_engine
```

## 权限说明

- 所有API接口都需要用户登录（`IsAuthenticated`权限）
- 用户只能访问自己创建的对话
- 用户只能向自己的对话添加消息

## 注意事项

1. **数据同步**：由于数据存储在云端数据库，所有设备访问的是同一份数据，可以实现实时同步。

2. **性能优化**：
   - 列表接口默认不返回消息内容，只返回消息数量
   - 使用`/conversations/{id}/messages/`接口单独获取消息列表
   - 使用`/conversations/recent/`获取最近的对话（不包含消息）

3. **元数据字段**：`metadata`字段可以存储任意JSON数据，建议存储：
   - 模型类型和参数
   - Token使用量
   - 其他自定义信息

4. **归档功能**：归档的对话不会出现在默认列表中，但可以通过`is_archived=true`参数查询。

## 故障排查

如果遇到问题，请检查：
1. 数据库连接是否正常
2. 用户是否已登录
3. 是否有权限访问对话
4. API URL是否正确

