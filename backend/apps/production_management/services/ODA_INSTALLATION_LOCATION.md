# ODA File Converter 安装位置说明

## 📍 安装位置

**ODA File Converter 必须安装在运行Django应用的服务器上**，而不是用户的本机电脑。

## 🔍 为什么需要安装在服务器上？

### CAD解析流程

```
用户浏览器
    ↓ (上传CAD文件)
Django服务器
    ↓ (接收文件)
服务器端处理
    ↓ (调用ODA File Converter转换DWG)
    ↓ (调用ezdxf解析DXF)
    ↓ (提取信息)
数据库存储解析结果
    ↓ (返回结果)
用户浏览器显示结果
```

### 关键点

1. **文件上传到服务器**：用户通过浏览器上传CAD文件，文件被保存到Django服务器的文件系统中
2. **服务器端解析**：Django应用在服务器上调用CAD解析服务
3. **需要服务器工具**：ODA File Converter必须在服务器上可用，因为转换过程在服务器端执行

## 🖥️ 安装位置

### 开发环境

如果您在本地开发，需要安装在**您的开发机器**上：

```bash
# Linux/Mac
/opt/ODAFileConverter/bin/DWGConvert
# 或
/usr/local/bin/DWGConvert

# Windows
C:\Program Files\ODA\ODAFileConverter\bin\DWGConvert.exe
```

### 生产环境

如果部署到生产服务器，需要安装在**生产服务器**上：

- **Docker容器**：如果使用Docker，需要在Docker镜像中安装
- **云服务器**：安装在云服务器（如阿里云、腾讯云等）上
- **物理服务器**：安装在运行Django应用的物理服务器上

## 📋 检查当前环境

### 1. 检查服务器类型

```bash
# 查看当前运行的服务器信息
uname -a
hostname
```

### 2. 检查ODA File Converter是否已安装

```bash
# 检查命令是否在PATH中
which DWGConvert

# 检查常见安装位置
ls -la /opt/ODAFileConverter/bin/DWGConvert
ls -la /usr/local/bin/DWGConvert
```

### 3. 在Django中检查

访问Django管理界面或运行测试脚本：

```bash
python backend/apps/production_management/services/test_cad_dependencies.py
```

## 🚀 安装步骤

### 开发环境（本地）

1. **下载ODA File Converter**
   - 访问：https://www.opendesign.com/guestfiles
   - 注册账号并下载Linux版本

2. **安装到本地**
   ```bash
   sudo mkdir -p /opt/ODAFileConverter
   sudo tar -xzf ODAFileConverter_*.tar.gz -C /opt/ODAFileConverter --strip-components=1
   sudo chmod +x /opt/ODAFileConverter/bin/DWGConvert
   sudo ln -s /opt/ODAFileConverter/bin/DWGConvert /usr/local/bin/DWGConvert
   ```

### 生产环境（服务器）

#### 方式1：直接在服务器上安装

```bash
# SSH连接到服务器
ssh user@your-server.com

# 按照开发环境的步骤安装
```

#### 方式2：Docker容器中安装

在Dockerfile中添加：

```dockerfile
# 下载并安装ODA File Converter
RUN mkdir -p /opt/ODAFileConverter && \
    wget -q https://download.opendesign.com/guestfiles/ODAFileConverter_*.tar.gz && \
    tar -xzf ODAFileConverter_*.tar.gz -C /opt/ODAFileConverter --strip-components=1 && \
    chmod +x /opt/ODAFileConverter/bin/DWGConvert && \
    ln -s /opt/ODAFileConverter/bin/DWGConvert /usr/local/bin/DWGConvert
```

#### 方式3：使用配置的自定义路径

如果安装在非标准位置，在Django的`settings.py`中配置：

```python
# settings.py
ODA_FILE_CONVERTER_PATH = '/custom/path/to/DWGConvert'
```

## ⚠️ 重要提示

1. **不是浏览器插件**：ODA File Converter不是浏览器插件，不能安装在用户的电脑上
2. **服务器端工具**：它是服务器端的命令行工具，必须在Django应用运行的服务器上
3. **多服务器部署**：如果有多个服务器（如负载均衡），需要在每个服务器上都安装
4. **容器化部署**：如果使用Docker/Kubernetes，需要在容器镜像中包含ODA File Converter

## 🔧 验证安装

安装后，在服务器上运行：

```bash
# 测试命令是否可用
DWGConvert --version

# 测试转换功能
DWGConvert input.dwg output.dxf
```

## 📞 需要帮助？

如果遇到安装问题，请检查：
1. 服务器操作系统类型（Linux/Windows）
2. 服务器架构（x64/arm64）
3. 文件权限是否正确
4. PATH环境变量是否包含安装目录

