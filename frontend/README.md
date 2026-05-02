# Kortix Frontend

## Quick Setup

The easiest way to get your frontend configured is to use the setup wizard from the project root:

```bash
cd .. # Navigate to project root if you're in the frontend directory
python setup.py
```

This will configure all necessary environment variables automatically.

## Environment Configuration

Create a `.env.local` file with the following configuration:

```sh
# 后端API地址 (包含/api前缀)
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000/api

# 前端URL (用于回调)
NEXT_PUBLIC_URL=http://localhost:3000

# 环境模式
NEXT_PUBLIC_ENV_MODE=LOCAL

# 可选：Tolt推荐系统ID
NEXT_PUBLIC_TOLT_REFERRAL_ID=
```

**注意：此项目已移除Supabase依赖，使用自定义认证系统。**

## Getting Started

Install dependencies:

```bash
npm install
```

Run the development server:

```bash
npm run dev
```

Build for production:

```bash
npm run build
```

Run the production server:

```bash
npm run start
```

## Authentication System

This project uses a custom authentication system instead of Supabase:

### Frontend Features
- ✅ Email/password registration and login
- ✅ Session management with localStorage
- ✅ Automatic token refresh
- ✅ Protected routes
- ❌ Google/GitHub OAuth (removed)

### Required Backend Endpoints
Your backend needs to implement these authentication endpoints:

```typescript
POST /auth/login       // 用户登录
POST /auth/register    // 用户注册  
POST /auth/refresh     // 刷新token
POST /auth/logout      // 用户登出
GET  /auth/me          // 获取当前用户
```

### Expected Response Format
```typescript
// Login/Register success response
{
  "access_token": "jwt_token_here",
  "refresh_token": "refresh_token_here",
  "expires_at": 1640995200,
  "user": {
    "id": "123",
    "email": "user@example.com", 
    "name": "User Name"
  }
}
```

## Development Notes

- The frontend connects to the backend API at `http://localhost:8000/api`
- All API requests include `Authorization: Bearer <token>` header
- Custom authentication system replaces Supabase
- The app runs on `http://localhost:3000` by default
