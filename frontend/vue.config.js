const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  outputDir: 'dist',
  publicPath: '/fincompass/',
  devServer: {
    historyApiFallback: {
      index: '/fincompass/index.html'
    },
    port: 8080,
    proxy: {
      '/fincompass': {
        target: 'http://127.0.0.1:7000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
