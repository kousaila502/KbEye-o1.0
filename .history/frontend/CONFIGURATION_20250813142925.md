# KbEye Frontend Configuration Guide

## 🎯 Quick Setup

**For most users**: Just change these two lines in `frontend/.env.local`:

```bash
# Change these URLs to match your backend:
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

That's it! Everything else works automatically.

## 🏗️ How It Works

**One Central Config**: All settings are managed in `frontend/src/config/config.js`

**Environment Variables**: Override settings using `frontend/.env.local`

**Smart Defaults**: Comes with presets for development, staging, production

## 🔧 Environment Switching

### Development (Default)
```bash
VITE_APP_ENV=development
# Uses: http://localhost:8000
```

### Production
```bash
VITE_APP_ENV=production
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_WS_BASE_URL=wss://api.yourdomain.com
```

### Docker
```bash
VITE_APP_ENV=docker
# Uses: http://kbeye-backend:8000
```

### Custom URLs
```bash
VITE_APP_ENV=development
VITE_API_BASE_URL=http://192.168.1.100:8000
VITE_WS_BASE_URL=ws://192.168.1.100:8000
```

## 📁 File Structure

```
frontend/src/config/
├── config.js           ← 🎯 MAIN CONFIG (central source of truth)
├── api.config.js       ← Uses config.js
└── app.config.js       ← Uses config.js
```

**Only edit**: `frontend/.env.local` for your environment
**Don't edit**: The `.js` config files (unless adding features)

## ⚙️ Common Settings

### Basic URLs
```bash
# Backend API
VITE_API_BASE_URL=http://localhost:8000

# WebSocket  
VITE_WS_BASE_URL=ws://localhost:8000

# Environment
VITE_APP_ENV=development
```

### Enable/Disable Features
```bash
# Features (true/false)
VITE_ENABLE_WEBSOCKET=true
VITE_ENABLE_AUTO_REFRESH=true
VITE_ENABLE_NOTIFICATIONS=true
VITE_ENABLE_DARK_MODE=true
```

### Debug Settings
```bash
# Debug mode
VITE_DEBUG_MODE=true
VITE_LOG_LEVEL=info

# API call logging
VITE_LOG_API_CALLS=true
```

### Timing Settings
```bash
# Refresh intervals (milliseconds)
VITE_REFRESH_INTERVAL_SERVICES=5000
VITE_REFRESH_INTERVAL_LOGS=10000
VITE_REFRESH_INTERVAL_ALERTS=15000

# WebSocket settings
VITE_WS_RECONNECT_ATTEMPTS=5
VITE_WS_RECONNECT_INTERVAL=3000
VITE_WS_HEARTBEAT_INTERVAL=25000
```

## 🚀 Quick Examples

### Example 1: Local Development
```bash
# frontend/.env.local
VITE_APP_ENV=development
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
VITE_DEBUG_MODE=true
```

### Example 2: Production Deployment
```bash
# frontend/.env.local
VITE_APP_ENV=production
VITE_API_BASE_URL=https://api.mycompany.com
VITE_WS_BASE_URL=wss://api.mycompany.com
VITE_DEBUG_MODE=false
VITE_LOG_LEVEL=error
```

### Example 3: Custom Server
```bash
# frontend/.env.local
VITE_APP_ENV=development
VITE_API_BASE_URL=http://192.168.1.50:8000
VITE_WS_BASE_URL=ws://192.168.1.50:8000
VITE_DEBUG_MODE=true
```

### Example 4: Docker Compose
```bash
# frontend/.env.local
VITE_APP_ENV=docker
VITE_API_BASE_URL=http://kbeye-backend:8000
VITE_WS_BASE_URL=ws://kbeye-backend:8000
```

## 🔍 Testing Your Configuration

1. **Start the frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

2. **Check the browser console** - you'll see:
   ```
   🔧 KbEye Frontend Configuration
   Environment: development
   API URL: http://localhost:8000
   WebSocket URL: ws://localhost:8000/ws
   ```

3. **Verify connection** - Dashboard should show "Live Connected"

## ❗ Troubleshooting

### Problem: "Backend connection failed"
**Solution**: Check your `VITE_API_BASE_URL` in `.env.local`

### Problem: WebSocket not connecting  
**Solution**: Check your `VITE_WS_BASE_URL` in `.env.local`

### Problem: Changes not working
**Solution**: Restart the dev server after changing `.env.local`

### Problem: CORS errors
**Solution**: Make sure your backend allows your frontend URL

## 🎯 Best Practices

1. **Copy the example**: Start with `.env.example` and modify
2. **Keep it simple**: Only change what you need
3. **Use presets**: Stick to `development`, `production`, `staging`
4. **Test locally first**: Always test with `localhost` before deploying
5. **Check console**: Look for configuration logs in browser console

## 🔄 Migration from Old Config

If you're updating from the old configuration system:

1. **Backup** your current `.env.local`
2. **Replace** `api.config.js` with the new version
3. **Update** your `.env.local` with the new format
4. **Test** that everything still works

The new system is backward compatible - your old environment variables will still work!