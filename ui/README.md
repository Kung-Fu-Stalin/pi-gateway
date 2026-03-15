# Pi-Gateway UI

React + TypeScript + Vite frontend for the Pi-Gateway proxy management system.

Modern, responsive admin dashboard built with **React 19**, **TypeScript**, and **Vite** for fast development and production builds.

## Table of Contents

- [Features](#features)
- [Local Development Setup](#local-development-setup)
- [Available Scripts](#available-scripts)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Building for Production](#building-for-production)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)
- [Performance Tips](#performance-tips)
- [Dependencies](#dependencies)
- [Resources](#resources)

## Features

- ⚡ **Fast Development** with Vite and Hot Module Replacement (HMR)
- 🎨 **Tailwind CSS** for responsive, utility-first styling
- 📱 **Responsive Design** - works on desktop, tablet, and mobile
- 🔐 **Authentication** - JWT-based session management
- 🌐 **Modern Stack** - React Router for navigation, Axios for API calls, TanStack Query for state management

## Local Development Setup

### Prerequisites

- **Node.js** 18+ (with npm)
- **API Server** running on `http://localhost:8000` (see [../README.md](../README.md#local-development) for API setup)

### Quick Start

#### 1. Install Dependencies

```bash
cd ui
npm install
```

#### 2. Start the Development Server

```bash
npm run dev
```

The application will be available at **http://localhost:5173**

#### 3. Access the UI

Open http://localhost:5173 in your browser. The dev server automatically:
- Proxies `/api/*` requests to `http://localhost:8000`
- Proxies `/ws/*` requests to `http://localhost:8000` (WebSocket support)
- Hot-reloads changes instantly

### Full Development Stack

To run the complete stack locally:

**Terminal 1: API Server**
```bash
cd api
export API_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=admin-password
export DB_URL="sqlite+aiosqlite:///./dev.db"
python -m uvicorn src.api.main:app --reload --port 8000
```

**Terminal 2: UI Development Server**
```bash
cd ui
npm run dev
```

**Terminal 3 (optional): Run Tests**
```bash
cd api
python -m pytest
```

## Available Scripts

### Development

- **`npm run dev`** - Start Vite dev server with hot module replacement
  - Runs on http://localhost:5173
  - Watches for file changes and auto-reloads

### Building

- **`npm run build`** - Build optimized production bundle
  - Compiles TypeScript and bundles with Vite
  - Output: `dist/` directory
  - Minified and optimized for production

- **`npm run preview`** - Preview production build locally
  - Serves the `dist/` directory
  - Useful for testing production build before deployment

### Code Quality

- **`npm run lint`** - Run ESLint to check code quality
  - Checks for TypeScript and React best practices
  - Identifies unused imports and potential bugs

## Project Structure

```
ui/
├── src/
│   ├── api/              # API client utilities
│   │   ├── client.ts     # Axios instance with base config
│   │   ├── domains.ts    # Domain management endpoints
│   │   └── users.ts      # User management endpoints
│   ├── components/       # Reusable React components
│   │   ├── Layout.tsx    # Main app layout
│   │   └── Toast.tsx     # Notification toast
│   ├── hooks/            # Custom React hooks
│   │   └── useAuth.ts    # Authentication hook
│   ├── pages/            # Page components
│   │   ├── LoginPage.tsx
│   │   ├── DomainsPage.tsx
│   │   ├── UsersPage.tsx
│   │   ├── LogsPage.tsx
│   │   └── ProfilePage.tsx
│   ├── store/            # State management (Zustand)
│   │   └── auth.ts       # Authentication state
│   ├── App.tsx           # Root component
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── public/               # Static assets
├── package.json
├── vite.config.ts        # Vite configuration
├── tsconfig.json         # TypeScript configuration
└── eslint.config.js      # ESLint configuration
```

## Configuration

### API Endpoint Configuration

The development server proxies API requests to `http://localhost:8000` via `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': 'http://localhost:8000',
    '/ws': 'http://localhost:8000',
  },
},
```

To change the API endpoint (e.g., for remote server testing):

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': 'http://your-api-server.com:8000',
  },
},
```

### Environment Variables

Create a `.env` file in the `ui/` directory if needed:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Reference in code:
```typescript
const apiUrl = import.meta.env.VITE_API_BASE_URL || '/api';
```

## Building for Production

### Create Production Build

```bash
npm run build
```

This generates optimized files in `dist/`:
- HTML, CSS, and JavaScript are minified
- Assets are hashed for cache busting
- Source maps are generated for debugging

### Deploy to Production

The Docker image is configured in [Dockerfile](./Dockerfile):

```bash
# Build Docker image
docker build -t pi-gateway-ui .

# Run container
docker run -p 80:80 pi-gateway-ui
```

Or use Docker Compose:

```bash
docker-compose up ui
```

## Development Workflow

### Adding a New Page

1. Create page component in `src/pages/YourPage.tsx`
2. Import in `src/App.tsx` and add route
3. Import styles or use Tailwind classes
4. Server automatically reloads on save

### Adding API Endpoints

1. Create API function in a file under `src/api/` (e.g., `src/api/logs.ts`)
2. Use the `client` instance from `src/api/client.ts`
3. Use TanStack Query hooks for caching/state management

Example:
```typescript
// src/api/logs.ts
import { client } from './client';

export const fetchLogs = async () => {
  const response = await client.get('/api/logs');
  return response.data;
};
```

### State Management

Uses **Zustand** for lightweight state management. Example auth store in `src/store/auth.ts`:

```typescript
import { create } from 'zustand';

interface AuthStore {
  token: string | null;
  setToken: (token: string) => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  token: null,
  setToken: (token: string) => set({ token }),
}));
```

## Troubleshooting

### Port 5173 Already in Use

```bash
# Find process using the port
lsof -i :5173

# Or run on different port
npm run dev -- --port 3000
```

### API Requests Failing

1. Check API server is running on `http://localhost:8000`
2. Verify proxy configuration in `vite.config.ts`
3. Check browser console for CORS errors
4. Verify API responds to `GET http://localhost:8000/healthz`

### Module Not Found Errors

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### TypeScript Errors After Change

```bash
# Rebuild TypeScript
npm run build

# Or check output
tsc -b
```

## Performance Tips

- Use `React.lazy()` for code splitting large components
- Leverage TanStack Query caching to minimize API calls
- Use Tailwind's JIT compilation (included by default)
- Profile with Chrome DevTools Performance tab

## Dependencies

| Package | Purpose |
|---------|---------|
| react | UI library |
| react-dom | DOM rendering |
| react-router-dom | Client-side routing |
| axios | HTTP client |
| @tanstack/react-query | Server state management |
| zustand | Client state management |
| tailwindcss | Utility-first CSS framework |
| vite | Build tool and dev server |
| typescript | Type safety |

## Resources

- [Vite Documentation](https://vitejs.dev/)
- [React Documentation](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [TanStack Query](https://tanstack.com/query/latest/)
- [Zustand](https://github.com/pmndrs/zustand)
