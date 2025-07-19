/*
  Tana Helper React App Entry Point
  
  Modern React 18 setup with Vite and Tailwind CSS
*/
import { createRoot } from 'react-dom/client'
import App from './App'
import './globals.css'
import { ReactScan } from './components/ReactScan';

// Development tools
if (import.meta.env.DEV) {
  // Enable React DevTools in development
  if (typeof window !== 'undefined') {
    window.__REACT_DEVTOOLS_GLOBAL_HOOK__?.onCommitFiberRoot
  }
}

const rootElement = document.getElementById('root')
if (!rootElement) {
  throw new Error('Failed to find the root element')
}

const root = createRoot(rootElement)

root.render(
  // <StrictMode>
  <>
    <ReactScan/>
      <App />
  </>
  // </StrictMode>
)

// Hot module replacement for better development experience
if (import.meta.hot) {
  import.meta.hot.accept()
}