import React, { useState } from 'react';
import { FaFlag, FaTimes } from 'react-icons/fa';
import api from '../utils/axios';
import { useToast } from '../context/ToastContext';
import './ReportModal.css';

const REASONS = [
  { value: 'spam', label: 'Spam', desc: 'Posting repetitive or irrelevant content' },
  { value: 'harassment', label: 'Harassment', desc: 'Bullying, threats, or targeted abuse' },
  { value: 'inappropriate_content', label: 'Inappropriate Content', desc: 'Offensive recipes, images, or comments' },
  { value: 'fake_account', label: 'Fake Account', desc: 'Impersonation or bot account' },
  { value: 'other', label: 'Other', desc: 'Other violation not listed above' },
];

function ReportModal({ username, onClose }) {
  const { toast } = useToast();
  const [reason, setReason] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!reason) {
      toast.warning('Please select a reason');
      return;
    }

    setSubmitting(true);
    try {
      await api.post(`/api/user/${username}/report`, { reason, description });
      toast.success('Report submitted. An admin will review it.');
      onClose();
    } catch (err) {
      const msg = err.response?.data?.error || 'Failed to submit report';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="report-modal-overlay" onClick={onClose}>
      <div className="report-modal" onClick={(e) => e.stopPropagation()}>
        <div className="report-modal-header">
          <h2><FaFlag /> Report {username}</h2>
          <button className="close-btn" onClick={onClose}><FaTimes /></button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="report-section">
            <label className="report-label">Why are you reporting this user?</label>
            <div className="reason-list">
              {REASONS.map((r) => (
                <label
                  key={r.value}
                  className={`reason-option ${reason === r.value ? 'selected' : ''}`}
                >
                  <input
                    type="radio"
                    name="reason"
                    value={r.value}
                    checked={reason === r.value}
                    onChange={() => setReason(r.value)}
                  />
                  <div className="reason-content">
                    <span className="reason-title">{r.label}</span>
                    <span className="reason-desc">{r.desc}</span>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div className="report-section">
            <label className="report-label" htmlFor="report-desc">
              Additional details <span className="optional">(optional)</span>
            </label>
            <textarea
              id="report-desc"
              className="report-textarea"
              placeholder="Describe the issue in more detail..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={1000}
              rows={3}
            />
            <div className="char-count">{description.length}/1000</div>
          </div>

          <div className="report-actions">
            <button type="button" className="btn btn-cancel" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-report"
              disabled={!reason || submitting}
            >
              <FaFlag />
              {submitting ? 'Submitting...' : 'Submit Report'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ReportModal;
