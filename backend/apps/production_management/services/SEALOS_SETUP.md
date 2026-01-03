# Sealos 开发环境配置 ODA File Converter

## 环境说明

- **开发环境**: Sealos (Linux)
- **生产环境**: Windows
- **需要**: 在两个环境都配置 ODA File Converter

## Sealos 开发环境配置

### 1. 下载 Linux 版本

访问：https://www.opendesign.com/guestfiles
下载：`ODAFileConverter_XX.X.X_lnxX64_qt5.tar.gz`

### 2. 上传到 Sealos

通过 Sealos 的文件上传功能或使用 `scp` 命令上传文件。

### 3. 解压和安装

```bash
# 解压
tar -xzf ODAFileConverter_XX.X.X_lnxX64_qt5.tar.gz

# 进入目录
cd ODAFileConverter_XX.X.X_lnxX64_qt5

# 查找可执行文件
find . -name "DWGConvert" -type f

# 通常位于 bin 目录
ls -la bin/DWGConvert
```

### 4. 配置方式

#### 方式A：添加到用户 PATH（推荐，无需 root）

```bash
# 创建用户bin目录
mkdir -p ~/bin

# 创建符号链接
ln -s $(pwd)/bin/DWGConvert ~/bin/DWGConvert

# 添加到PATH
echo 'export PATH=$PATH:~/bin' >> ~/.bashrc
source ~/.bashrc

# 验证
DWGConvert --version
```

#### 方式B：使用环境变量配置（推荐用于Sealos）

在 Sealos 的环境变量中设置：

```bash
# 在 settings.py 或环境变量中设置
ODA_FILE_CONVERTER_PATH=/path/to/ODAFileConverter/bin/DWGConvert
```

或在 Sealos 控制台设置环境变量：
- 变量名：`ODA_FILE_CONVERTER_PATH`
- 变量值：`/path/to/ODAFileConverter/bin/DWGConvert`

#### 方式C：Docker 镜像打包（如果使用 Docker）

在 Dockerfile 中添加：

```dockerfile
# 下载并安装 ODA File Converter
RUN wget https://www.opendesign.com/guestfiles/ODAFileConverter_XX.X.X_lnxX64_qt5.tar.gz && \
    tar -xzf ODAFileConverter_XX.X.X_lnxX64_qt5.tar.gz && \
    mv ODAFileConverter_XX.X.X_lnxX64_qt5 /opt/ODAFileConverter && \
    ln -s /opt/ODAFileConverter/bin/DWGConvert /usr/local/bin/DWGConvert && \
    rm ODAFileConverter_XX.X.X_lnxX64_qt5.tar.gz

ENV PATH="/opt/ODAFileConverter/bin:${PATH}"
```

### 5. 验证安装

```bash
# 方法1: 直接测试命令
DWGConvert --version

# 方法2: 使用Django管理命令
python manage.py check_oda_converter
```

## Windows 生产环境配置

### 1. 安装（已完成）

已安装到：`C:\Program Files\ODA\ODAFileConverter 26.10.0\`

### 2. 配置方式

#### 方式A：添加到系统 PATH（推荐）

1. 右键"此电脑" → 属性
2. 高级系统设置 → 环境变量
3. 系统变量 → Path → 编辑
4. 新建，添加：`C:\Program Files\ODA\ODAFileConverter 26.10.0\bin`
5. 确定保存

#### 方式B：使用环境变量配置

在 Windows 环境变量或 settings.py 中设置：

```python
# settings.py
ODA_FILE_CONVERTER_PATH = r'C:\Program Files\ODA\ODAFileConverter 26.10.0\bin\DWGConvert.exe'
```

或在 Windows 系统环境变量中：
- 变量名：`ODA_FILE_CONVERTER_PATH`
- 变量值：`C:\Program Files\ODA\ODAFileConverter 26.10.0\bin\DWGConvert.exe`

### 3. 验证安装

```cmd
# 在CMD或PowerShell中测试
DWGConvert --version

# 或使用Django管理命令
python manage.py check_oda_converter
```

## 代码配置

代码已支持通过 `settings.py` 或环境变量配置路径：

```python
# settings.py
ODA_FILE_CONVERTER_PATH = os.getenv('ODA_FILE_CONVERTER_PATH', None)
```

优先级：
1. `ODA_FILE_CONVERTER_PATH` 环境变量/设置
2. 系统 PATH 中的命令
3. 常见安装路径

## Sealos 环境变量配置

在 Sealos 控制台中：

1. 进入应用配置
2. 环境变量设置
3. 添加：
   - **名称**: `ODA_FILE_CONVERTER_PATH`
   - **值**: `/path/to/ODAFileConverter/bin/DWGConvert`
   - **类型**: 普通变量

## 常见问题

### Q: Sealos 上找不到命令
**A**: 使用环境变量方式配置，指定完整路径。

### Q: Windows 上路径包含版本号
**A**: 代码已自动支持带版本号的路径，或使用环境变量指定完整路径。

### Q: 两个环境路径不同
**A**: 使用环境变量分别配置，代码会自动读取。

## 验证清单

- [ ] Sealos: 已下载 Linux 版本
- [ ] Sealos: 已解压并配置路径
- [ ] Sealos: `DWGConvert --version` 可用
- [ ] Windows: 已安装并添加到 PATH
- [ ] Windows: `DWGConvert --version` 可用
- [ ] 两个环境: `python manage.py check_oda_converter` 通过

