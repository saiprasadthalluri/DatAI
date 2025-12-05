# ChatApp Frontend

React + Vite + TypeScript frontend for ChatGPT-like application.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
Create `.env` file:
```
VITE_API_URL=http://localhost:8000/api/v1
VITE_FIREBASE_API_KEY=your-firebase-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id
```

3. Start development server:
```bash
npm run dev
```

## Build

```bash
npm run build
```

## Testing

```bash
npm test
npm run test:e2e  # Playwright E2E tests
```

## Linting

```bash
npm run lint
npm run format
```




