const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  outputDir: 'dist',
  publicPath: '/fincompassplugin/',
  devServer: {
    historyApiFallback: {
      index: '/fincompassplugin/index.html'
    },
    port: 8080,
    proxy: {
      '/fincompassplugin': {
        target: 'http://127.0.0.1:7000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
