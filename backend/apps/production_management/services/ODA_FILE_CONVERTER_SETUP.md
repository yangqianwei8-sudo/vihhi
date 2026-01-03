# ODA File Converter 安装指南

ODA File Converter 是用于将DWG文件转换为DXF格式的工具，这是解析DWG格式CAD文件所必需的。

## 安装步骤

### 方法1：手动安装（推荐）

1. **访问ODA官网**
   - 网址：https://www.opendesign.com/guestfiles
   - 注册一个免费账号（如果还没有）

2. **下载ODA File Converter**
   - 选择 Linux 版本
   - 根据系统架构选择 x64 或 arm64
   - 下载 tar.gz 压缩包

3. **解压安装**
   ```bash
   # 创建安装目录
   sudo mkdir -p /opt/ODAFileConverter
   
   # 解压文件（假设下载的文件名为 ODAFileConverter_*.tar.gz）
   sudo tar -xzf ODAFileConverter_*.tar.gz -C /opt/ODAFileConverter --strip-components=1
   
   # 设置执行权限
   sudo chmod +x /opt/ODAFileConverter/bin/DWGConvert
   
   # 创建符号链接到系统PATH
   sudo ln -s /opt/ODAFileConverter/bin/DWGConvert /usr/local/bin/DWGConvert
   ```

4. **验证安装**
   ```bash
   DWGConvert --version
   ```

### 方法2：使用安装脚本

如果您已经下载了安装包，可以使用提供的安装脚本：

```bash
cd /path/to/downloaded/file
cp ODAFileConverter*.tar.gz /home/devbox/project/vihhi/weihai_tech_production_system/backend/apps/production_management/services/
cd /home/devbox/project/vihhi/weihai_tech_production_system/backend/apps/production_management/services/
./install_oda_converter.sh
```

## 配置Django设置（可选）

如果ODA File Converter安装在非标准位置，可以在Django的settings.py中配置：

```python
# settings.py
ODA_FILE_CONVERTER_PATH = '/opt/ODAFileConverter/bin/DWGConvert'
```

## 验证安装

运行以下Python代码验证安装：

```python
from backend.apps.production_management.services.cad_parser_service import CADParserService

parser = CADParserService()
if parser.cad2image_available:
    print("✓ ODA File Converter 已安装")
else:
    print("✗ ODA File Converter 未安装")
```

## 故障排除

### 问题1：找不到DWGConvert命令

**解决方案：**
- 检查是否在PATH中：`which DWGConvert`
- 检查符号链接：`ls -la /usr/local/bin/DWGConvert`
- 手动添加到PATH：`export PATH=$PATH:/opt/ODAFileConverter/bin`

### 问题2：权限不足

**解决方案：**
```bash
sudo chmod +x /opt/ODAFileConverter/bin/DWGConvert
```

### 问题3：依赖库缺失

**解决方案：**
```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install libc6 libstdc++6

# CentOS/RHEL
sudo yum install glibc libstdc++
```

## 注意事项

1. ODA File Converter是免费工具，但需要注册ODA账号才能下载
2. 如果没有安装ODA File Converter，系统仍然可以解析DXF和PDF格式的CAD文件
3. DWG文件需要先转换为DXF才能解析，如果没有ODA File Converter，DWG文件解析功能将不可用

## 相关链接

- ODA官网：https://www.opendesign.com/
- 下载页面：https://www.opendesign.com/guestfiles
- 文档：https://www.opendesign.com/files/guestdownloads/ODAFileConverter/ODAFileConverter_ReadMe.txt
