import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import * as serviceWorkerRegistration from './serviceWorkerRegistration';
import { logWebVitals } from './reportWebVitals';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Register service worker for offline capability
serviceWorkerRegistration.register({
  onUpdate: (registration) => {
    if (window.confirm('New version available! Reload to update?')) {
      window.location.reload();
    }
  },
  onSuccess: () => {
    console.log('App is ready for offline use');
  }
});

// Measure and report performance metrics
logWebVitals();
