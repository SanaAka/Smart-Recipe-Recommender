import React, { createContext, useContext, useState, useCallback, useRef } from 'react';
import './Toast.css';

const ToastContext = createContext({
  addToast: () => {},
  removeToast: () => {},
});

export const useToast = () => useContext(ToastContext);

let toastId = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const timersRef = useRef({});

  const removeToast = useCallback((id) => {
    // Mark as exiting first for animation
    setToasts(prev => prev.map(t => t.id === id ? { ...t, exiting: true } : t));
    // Remove after animation
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
      if (timersRef.current[id]) {
        clearTimeout(timersRef.current[id]);
        delete timersRef.current[id];
      }
    }, 300);
  }, []);

  const addToast = useCallback((message, type = 'info', duration = 3500) => {
    const id = ++toastId;
    const toast = { id, message, type, exiting: false, createdAt: Date.now() };

    setToasts(prev => {
      // Keep max 5 toasts
      const updated = prev.length >= 5 ? prev.slice(1) : prev;
      return [...updated, toast];
    });

    if (duration > 0) {
      timersRef.current[id] = setTimeout(() => removeToast(id), duration);
    }

    return id;
  }, [removeToast]);

  // Convenience methods
  const toast = {
    success: (msg, duration) => addToast(msg, 'success', duration),
    error: (msg, duration) => addToast(msg, 'error', duration || 5000),
    warning: (msg, duration) => addToast(msg, 'warning', duration),
    info: (msg, duration) => addToast(msg, 'info', duration),
  };

  return (
    <ToastContext.Provider value={{ addToast, removeToast, toast }}>
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  );
}

/* ── Inline Toast Container ── */
function ToastContainer({ toasts, removeToast }) {
  if (toasts.length === 0) return null;

  return (
    <div className="toast-container" role="alert" aria-live="polite">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`toast toast-${t.type} ${t.exiting ? 'toast-exit' : 'toast-enter'}`}
        >
          <span className="toast-icon">{getIcon(t.type)}</span>
          <span className="toast-message">{t.message}</span>
          <button className="toast-close" onClick={() => removeToast(t.id)} aria-label="Close">
            ×
          </button>
        </div>
      ))}
    </div>
  );
}

function getIcon(type) {
  switch (type) {
    case 'success': return '✓';
    case 'error':   return '✕';
    case 'warning': return '⚠';
    case 'info':    return 'ℹ';
    default:        return 'ℹ';
  }
}

export default ToastContext;
