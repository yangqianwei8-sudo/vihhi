# 首页CSS模块说明

## 目录结构

```
home/
├── _variables.css    # 首页专用变量
├── _layout.css       # 布局样式
├── _components.css   # 组件样式
├── _scenes.css       # 场景样式
├── _skeleton.css     # 骨架屏样式
└── home.css          # 主入口文件
```

## 模块说明

### _variables.css
定义首页专用的CSS变量，基于系统核心变量（`--vh-*`前缀）。

主要变量：
- `--home-gap`: 布局间距
- `--welcome-card-*`: 欢迎卡片相关变量
- `--quick-stat-*`: 快速统计卡片相关变量

### _layout.css
使用CSS Grid实现响应式布局：
- `.dashboard-layout`: 主布局容器
- `.dashboard-header`: 顶部区域（欢迎卡片 + 快速统计）
- `.dashboard-main`: 主内容区（左侧内容 + 右侧边栏）

响应式断点：
- `1400px`: 中等屏幕，切换为单列布局
- `768px`: 小屏幕，调整间距

### _components.css
组件样式：
- `.welcome-card`: 欢迎卡片（带光泽动画效果）
- `.quick-stats`: 快速统计卡片网格
- `.quick-stat-card`: 单个统计卡片

### _scenes.css
场景切换动画和场景特定样式。

### _skeleton.css
骨架屏加载状态的占位样式。

## 使用方式

在主入口文件 `home.css` 中使用 `@import` 导入：

```css
@import 'variables.css';
@import 'layout.css';
@import 'components.css';
@import 'scenes.css';
@import 'skeleton.css';
```

在模板中引入：

```html
<link rel="stylesheet" href="{% static 'css/home/home.css' %}">
```

## 变量命名规范

统一使用 `--vh-*` 前缀，与系统核心变量保持一致：
- `--vh-primary`: 主品牌色
- `--vh-text-muted`: 次要文本颜色
- `--vh-border`: 边框颜色
- `--shadow-lg`: 阴影（保持原命名）

## 响应式设计

- 使用CSS Grid实现灵活的布局
- 使用CSS变量实现主题切换
- 支持移动端、平板和桌面端

