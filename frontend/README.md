# InFynd Company Intelligence AI - React Frontend

## Setup

1. Install dependencies:
```bash
npm install
```

## Development

Run the development server (with hot reload):
```bash
npm run dev
```

The React dev server will run on `http://localhost:3000` and proxy API requests to the Flask backend at `http://localhost:5000`.

Make sure the Flask backend is running:
```bash
cd ..
python run_backend.py
```

## Production Build

Build the React app for production:
```bash
npm run build
```

This creates a `dist` folder with the optimized production build. The Flask backend will automatically serve this build when it detects the `dist` folder exists.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── pages/          # Page components
│   │   ├── Sidebar.jsx     # Navigation sidebar
│   │   ├── MainContent.jsx # Main content area
│   │   └── ChatPanel.jsx   # Chat interface
│   ├── services/
│   │   └── api.js          # API service layer
│   ├── App.jsx             # Main app component
│   ├── App.css
│   ├── main.jsx            # Entry point
│   └── index.css           # Global styles
├── index.html              # HTML template
├── package.json
├── vite.config.js          # Vite configuration
└── dist/                   # Production build (generated)
```

## Features

- React-based UI with component architecture
- API integration with Flask backend
- Real-time chat interface
- Company profile viewing
- Multiple analysis modules
- Responsive design

