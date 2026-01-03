@echo off
REM ============================================================
REM 批量DWG转DXF转换脚本
REM 使用方法：将脚本放在包含DWG文件的文件夹中，双击运行
REM ============================================================

echo ============================================================
echo DWG批量转换为DXF工具
echo ============================================================
echo.

REM 查找DWGConvert.exe的路径
set "CONVERTER_PATH="

REM 方法1: 检查PATH中的命令
where DWGConvert.exe >nul 2>&1
if %errorlevel% == 0 (
    set "CONVERTER_PATH=DWGConvert.exe"
    echo [OK] 找到命令: DWGConvert.exe
    goto :found
)

REM 方法2: 检查常见安装路径（带版本号）
for /d %%i in ("C:\Program Files\ODA\ODAFileConverter*") do (
    if exist "%%i\bin\DWGConvert.exe" (
        set "CONVERTER_PATH=%%i\bin\DWGConvert.exe"
        echo [OK] 找到文件: %%i\bin\DWGConvert.exe
        goto :found
    )
)

REM 方法3: 检查固定路径
if exist "C:\Program Files\ODA\ODAFileConverter\bin\DWGConvert.exe" (
    set "CONVERTER_PATH=C:\Program Files\ODA\ODAFileConverter\bin\DWGConvert.exe"
    echo [OK] 找到文件: C:\Program Files\ODA\ODAFileConverter\bin\DWGConvert.exe
    goto :found
)

if exist "C:\Program Files (x86)\ODA\ODAFileConverter\bin\DWGConvert.exe" (
    set "CONVERTER_PATH=C:\Program Files (x86)\ODA\ODAFileConverter\bin\DWGConvert.exe"
    echo [OK] 找到文件: C:\Program Files (x86)\ODA\ODAFileConverter\bin\DWGConvert.exe
    goto :found
)

REM 未找到转换工具
echo [错误] 未找到DWGConvert.exe
echo.
echo 请确保已安装ODA File Converter，并：
echo 1. 添加到系统PATH，或
echo 2. 修改脚本中的CONVERTER_PATH变量
echo.
pause
exit /b 1

:found
echo.
echo ============================================================
echo 开始转换...
echo ============================================================
echo.

REM 统计文件数量
set /a count=0
set /a success=0
set /a failed=0

REM 遍历当前目录下的所有DWG文件
for %%f in (*.dwg) do (
    set /a count+=1
    echo [%count%] 正在转换: %%f
    
    REM 生成输出文件名（同名的DXF文件）
    set "output_file=%%~nf.dxf"
    
    REM 执行转换
    "%CONVERTER_PATH%" "%%f" "!output_file!" >nul 2>&1
    
    if exist "!output_file!" (
        echo      [成功] 已生成: !output_file!
        set /a success+=1
    ) else (
        echo      [失败] 转换失败: %%f
        set /a failed+=1
    )
    echo.
)

REM 显示统计结果
echo ============================================================
echo 转换完成！
echo ============================================================
echo 总计: %count% 个文件
echo 成功: %success% 个
echo 失败: %failed% 个
echo.

if %failed% gtr 0 (
    echo 注意：部分文件转换失败，请检查：
    echo 1. DWG文件是否损坏
    echo 2. 文件版本是否支持
    echo 3. 是否有足够的磁盘空间
    echo.
)

pause

