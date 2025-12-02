import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    vue(),
    visualizer({
      open: false,
      gzipSize: true,
      brotliSize: true
    })
  ],

  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    }
  },

  build: {
    // ============================================
    // Performance Optimization
    // ============================================
    target: 'ES2020',
    minify: 'terser',
    sourcemap: false, // Disable in production
    
    rollupOptions: {
      output: {
        // Code splitting
        manualChunks: {
          'vendor': ['vue', 'vue-router', 'pinia'],
          'charts': ['chart.js', 'vue-chartjs'],
          'utils': ['date-fns', 'axios']
        },
        // Optimize chunk names
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: ({ name }) => {
          if (/\.css$/.test(name ?? '')) {
            return 'css/[name]-[hash][extname]'
          }
          if (/\.(png|jpg|jpeg|gif|svg|webp)$/.test(name ?? '')) {
            return 'images/[name]-[hash][extname]'
          }
          if (/\.(woff|woff2|eot|ttf|otf)$/.test(name ?? '')) {
            return 'fonts/[name]-[hash][extname]'
          }
          return '[name]-[hash][extname]'
        }
      }
    },

    // ============================================
    // CSS Code Splitting
    // ============================================
    cssCodeSplit: true,
    cssMinify: true,

    // ============================================
    // Terser Options
    // ============================================
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.debug']
      },
      mangle: {
        properties: {
          regex: /^_/
        }
      }
    }
  },

  // ============================================
  // Optimization Options
  // ============================================
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'pinia',
      'axios',
      'date-fns',
      'chart.js'
    ]
  }
})