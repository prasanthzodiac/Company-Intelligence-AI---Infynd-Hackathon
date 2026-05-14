# InFynd Company Intelligence AI - React Frontend Setup

## Quick Start

### Development Mode

1. **Install Frontend Dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start React Development Server:**
   ```bash
   npm run dev
   ```
   This starts the React dev server on `http://localhost:3000` with hot reload.

3. **Start Flask Backend (in a separate terminal):**
   ```bash
   cd ..
   python run_backend.py
   ```
   This starts the Flask API server on `http://localhost:5000`.

4. **Access the Application:**
   - React UI: `http://localhost:3000`
   - Flask API: `http://localhost:5000/api`

The React dev server is configured to proxy API requests to the Flask backend.

### Production Mode

1. **Build React App:**
   ```bash
   cd frontend
   npm run build
   ```

2. **Start Flask Backend:**
   ```bash
   cd ..
   python run_backend.py
   ```

3. **Access the Application:**
   - Full application: `http://localhost:5000`
   - The Flask backend automatically serves the React build when `frontend/dist` exists.

## Project Structure

```
company_intel/
├── backend/
│   ├── api/
│   │   └── app.py              # Flask API server (serves React in production)
│   └── services/               # Backend services
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── pages/         # Page components
│   │   │   ├── Sidebar.jsx
│   │   │   ├── MainContent.jsx
│   │   │   └── ChatPanel.jsx
│   │   ├── services/
│   │   │   └── api.js          # API service layer
│   │   ├── App.jsx             # Main app component
│   │   └── main.jsx            # Entry point
│   ├── dist/                   # Production build (generated)
│   ├── package.json
│   └── vite.config.js
└── run_backend.py              # Backend entry point
```

## Features

- ✅ React 18 with modern hooks
- ✅ Component-based architecture
- ✅ API integration with Flask backend
- ✅ Real-time chat interface
- ✅ Company profile viewing
- ✅ Multiple analysis modules
- ✅ Responsive design
- ✅ Development hot reload
- ✅ Production build optimization

## API Endpoints

The frontend communicates with the Flask backend via these endpoints:

- `GET /api/companies` - List all companies
- `GET /api/companies/<domain>/profile` - Get company profile
- `GET /api/companies/<domain>/chunks` - Get company chunks
- `POST /api/chat` - Send chat message
- `GET /api/proofs/<domain>` - Get proofs for a query

## Troubleshooting

### Port Already in Use
If port 3000 or 5000 is already in use:
- React: Change port in `vite.config.js`
- Flask: Change port in `run_backend.py` or set `PORT` environment variable

### CORS Issues
CORS is enabled in the Flask backend. If you encounter CORS errors, ensure:
- Flask backend is running
- React dev server proxy is configured correctly in `vite.config.js`

### Build Issues
If the production build fails:
- Ensure all dependencies are installed: `npm install`
- Check Node.js version (recommended: 18+)
- Clear cache: `rm -rf node_modules package-lock.json && npm install`

