# 首页模块化架构说明

## 目录结构

```
home/
├── core/                    # 核心模块
│   ├── EventBus.js         # 事件总线
│   └── StateManager.js     # 状态管理器
├── api/                     # API模块
│   └── DashboardAPI.js     # 仪表盘API封装
├── components/              # 组件模块
│   ├── DashboardCards.js   # 统计卡片组件
│   └── KanbanBoard.js      # 看板组件
├── utils/                   # 工具模块
│   ├── ErrorHandler.js     # 错误处理
│   ├── ResourceLoader.js   # 资源加载器
│   ├── SkeletonLoader.js   # 骨架屏加载器
│   └── PerformanceMonitor.js # 性能监控
├── config.js                # 配置文件
└── home.js                  # 主入口文件
```

## 模块说明

### 核心模块

#### EventBus.js
事件总线，用于组件间解耦通信。

```javascript
// 订阅事件
eventBus.on('dashboard:stats:updated', (data) => {
    console.log('统计数据已更新', data);
});

// 发布事件
eventBus.emit('dashboard:stats:updated', statsData);
```

#### StateManager.js
状态管理器，管理应用状态并支持状态订阅。

```javascript
const state = new StateManager({ stats: null, todos: [] });

// 订阅状态变化
state.subscribe((newState, prevState) => {
    console.log('状态已更新', newState);
});

// 更新状态
state.setState({ stats: newData });
```

### API模块

#### DashboardAPI.js
统一的API客户端，支持：
- 请求合并：单次请求获取所有数据
- 请求去重：相同请求在短时间内只发送一次
- 智能缓存：30秒TTL，支持手动刷新

```javascript
const api = new DashboardAPI({
    baseURL: '/api/admin/dashboard',
    errorHandler: errorHandler,
    cache: { ttl: 30000, enabled: true }
});

// 获取所有数据
const allData = await api.fetchAll(['stats', 'todos']);

// 获取统计数据
const stats = await api.fetchStats();
```

### 组件模块

#### DashboardCards.js
统计卡片组件，负责渲染数据概览卡片。

```javascript
const dashboardCards = new DashboardCards({
    container: document.getElementById('stats-cards-container'),
    skeletonLoader: SkeletonLoader,
    eventBus: eventBus
});

dashboardCards.render(statsData);
dashboardCards.showLoading();
```

#### KanbanBoard.js
看板组件，负责渲染任务看板。

```javascript
const kanbanBoard = new KanbanBoard({
    pendingContainer: document.getElementById('task-pending-container'),
    inProgressContainer: document.getElementById('task-in-progress-container'),
    completedContainer: document.getElementById('task-completed-container'),
    skeletonLoader: SkeletonLoader,
    eventBus: eventBus
});

kanbanBoard.render(todos);
kanbanBoard.showLoading();
```

### 工具模块

#### ErrorHandler.js
错误处理器，支持：
- 错误分类（network、timeout、server、auth）
- 自动重试（最多3次，指数退避）
- 友好的错误提示

#### SkeletonLoader.js
骨架屏加载器，生成加载状态的占位UI。

```javascript
SkeletonLoader.show(container, 'stats');
SkeletonLoader.hide(container);
```

#### PerformanceMonitor.js
性能监控工具，追踪：
- 页面加载时间
- API调用耗时
- 渲染性能

## 使用方式

### 在模板中引入

```html
<!-- 核心模块 -->
<script src="{% static 'js/home/core/EventBus.js' %}"></script>
<script src="{% static 'js/home/core/StateManager.js' %}"></script>

<!-- 工具模块 -->
<script src="{% static 'js/home/utils/ErrorHandler.js' %}"></script>
<script src="{% static 'js/home/utils/SkeletonLoader.js' %}"></script>

<!-- 配置 -->
<script src="{% static 'js/home/config.js' %}"></script>

<!-- API模块 -->
<script src="{% static 'js/home/api/DashboardAPI.js' %}"></script>

<!-- 组件模块 -->
<script src="{% static 'js/home/components/DashboardCards.js' %}"></script>
<script src="{% static 'js/home/components/KanbanBoard.js' %}"></script>

<!-- 主入口 -->
<script src="{% static 'js/home/home.js' %}"></script>
```

### 配置说明

在 `config.js` 中可以配置：
- API端点
- UI配置（刷新间隔、动画时长等）
- 功能开关（自动刷新、离线模式等）
- 主题配置

## 后端API

### 统一接口

`POST /api/admin/dashboard/all/`

请求体：
```json
{
    "include": ["stats", "todos"]
}
```

响应：
```json
{
    "success": true,
    "data": {
        "stats": { ... },
        "todos": { ... }
    }
}
```

## 兼容性

- 使用ES5语法，兼容所有现代浏览器
- 支持IE11+（需要polyfill）
- 使用全局变量方式，无需构建工具

## 迁移说明

原有的 `home.js` 文件仍然保留，新模块化代码会逐步替换旧代码。两者可以共存，新代码优先执行。

