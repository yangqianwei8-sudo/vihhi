#!/bin/bash
# 检查 Docker Hub 中的镜像信息

echo "🔍 检查 Docker Hub 镜像信息..."
echo ""

# 1. 检查当前容器使用的镜像
echo "1. 当前容器使用的镜像信息："
if [ -f /etc/os-release ]; then
    echo "   容器操作系统信息："
    cat /etc/os-release | grep -E "PRETTY_NAME|NAME" | head -2
fi

echo ""
echo "2. 检查镜像标签（如果可用）："
if [ -f /.dockerenv ]; then
    echo "   ✓ 运行在 Docker 容器中"
    # 尝试从环境变量或文件中获取镜像信息
    if [ -n "$IMAGE_NAME" ]; then
        echo "   镜像名称: $IMAGE_NAME"
    fi
    if [ -n "$IMAGE_TAG" ]; then
        echo "   镜像标签: $IMAGE_TAG"
    fi
else
    echo "   ⚠ 不在 Docker 容器中"
fi

echo ""
echo "3. 检查 GitHub Actions 配置："
echo "   根据 .github/workflows/build-and-push.yml："
echo "   镜像格式：<DOCKER_USERNAME>/backend:latest"
echo "   镜像格式：<DOCKER_USERNAME>/backend:<git-sha>"
echo ""
echo "   要查看实际的 Docker Hub 用户名，请："
echo "   1. 访问 GitHub 仓库设置："
echo "      https://github.com/<your-username>/<repo-name>/settings/secrets/actions"
echo "   2. 查看 DOCKER_USERNAME secret 的值"
echo "   3. 然后访问："
echo "      https://hub.docker.com/r/<DOCKER_USERNAME>/backend"

echo ""
echo "4. 检查 GitHub Actions 构建状态："
echo "   访问：https://github.com/<your-username>/<repo-name>/actions"
echo "   查看 'Build and Push Docker Image' 工作流的最新运行状态"
echo "   - ✅ 绿色 = 构建和推送成功"
echo "   - ❌ 红色 = 构建或推送失败"

echo ""
echo "5. 在 Sealos 中检查镜像配置："
echo "   - 进入应用详情页"
echo "   - 查看 '镜像配置' 或 'Image' 设置"
echo "   - 应该能看到类似：<username>/backend:latest 的镜像名称"

echo ""
echo "✅ 检查完成！"
echo ""
echo "💡 提示："
echo "   如果 GitHub Actions 显示构建成功，镜像应该已经在 Docker Hub 中了"
echo "   如果找不到，可能是："
echo "   1. Docker Hub 用户名配置错误"
echo "   2. 镜像设置为私有，需要登录才能查看"
echo "   3. 构建失败，镜像未推送"

