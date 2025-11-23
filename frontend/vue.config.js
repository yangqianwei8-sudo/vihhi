const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    host: '0.0.0.0',
    port: 8080,
    client: {
      webSocketURL: {
        hostname: 'localhost',
        pathname: '/ws',
        protocol: 'ws',
        port: 8080
      }
    },
    // 如果需要完全禁用 WebSocket，取消下面的注释
    // webSocketServer: false,
    // hot: false,
  },
  // 配置代理（如果需要）
  // proxy: {
  //   '/api': {
  //     target: 'http://localhost:8000',
  //     changeOrigin: true
  //   }
  // }
})

