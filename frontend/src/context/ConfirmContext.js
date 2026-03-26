import React, { createContext, useContext, useState, useCallback, useRef } from 'react';
import './ConfirmModal.css';

const ConfirmContext = createContext({
  confirm: () => Promise.resolve(false),
});

export const useConfirm = () => useContext(ConfirmContext);

export function ConfirmProvider({ children }) {
  const [modal, setModal] = useState(null);
  const resolveRef = useRef(null);

  const confirm = useCallback(({
    title = 'Are you sure?',
    message = '',
    confirmText = 'Yes',
    cancelText = 'Cancel',
    variant = 'danger', // 'danger' | 'warning' | 'info'
  } = {}) => {
    return new Promise((resolve) => {
      resolveRef.current = resolve;
      setModal({ title, message, confirmText, cancelText, variant });
    });
  }, []);

  const handleConfirm = () => {
    setModal(null);
    resolveRef.current?.(true);
  };

  const handleCancel = () => {
    setModal(null);
    resolveRef.current?.(false);
  };

  return (
    <ConfirmContext.Provider value={{ confirm }}>
      {children}
      {modal && (
        <div className="confirm-overlay" onClick={handleCancel}>
          <div
            className={`confirm-modal confirm-${modal.variant}`}
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="confirm-title"
          >
            <div className="confirm-icon-wrapper">
              <span className="confirm-icon">
                {modal.variant === 'danger' ? '🗑️' : modal.variant === 'warning' ? '⚠️' : 'ℹ️'}
              </span>
            </div>
            <h3 id="confirm-title" className="confirm-title">{modal.title}</h3>
            {modal.message && <p className="confirm-message">{modal.message}</p>}
            <div className="confirm-actions">
              <button className="confirm-btn confirm-btn-cancel" onClick={handleCancel}>
                {modal.cancelText}
              </button>
              <button
                className={`confirm-btn confirm-btn-ok confirm-btn-${modal.variant}`}
                onClick={handleConfirm}
                autoFocus
              >
                {modal.confirmText}
              </button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  );
}

export default ConfirmContext;
