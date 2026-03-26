import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaLock, FaEnvelope, FaPen, FaTrash, FaArrowLeft, FaCheck, FaExclamationTriangle, FaUserEdit } from 'react-icons/fa';
import api from '../utils/axios';
import { AuthContext } from '../App';
import { useToast } from '../context/ToastContext';
import { useConfirm } from '../context/ConfirmContext';
import UserAvatar from '../components/UserAvatar';
import './AccountSettings.css';

function AccountSettings() {
  const navigate = useNavigate();
  const { user, login: authLogin, logout, token } = useContext(AuthContext);
  const { toast } = useToast();
  const { confirm } = useConfirm();

  // Bio state
  const [bio, setBio] = useState(user?.bio || '');
  const [bioSaving, setBioSaving] = useState(false);

  // Email state
  const [email, setEmail] = useState(user?.email || '');
  const [emailPassword, setEmailPassword] = useState('');
  const [emailSaving, setEmailSaving] = useState(false);

  // Password state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [passwordSaving, setPasswordSaving] = useState(false);

  // Username state
  const [newUsername, setNewUsername] = useState(user?.username || '');
  const [usernamePassword, setUsernamePassword] = useState('');
  const [usernameSaving, setUsernameSaving] = useState(false);

  // Delete state
  const [deletePassword, setDeletePassword] = useState('');
  const [deleting, setDeleting] = useState(false);

  if (!user) {
    return (
      <div className="settings-page">
        <div className="container">
          <p>Please log in to access settings.</p>
        </div>
      </div>
    );
  }

  // ── Username ──
  const handleUsernameSave = async (e) => {
    e.preventDefault();
    const trimmed = newUsername.trim();
    if (!trimmed || trimmed.length < 3) {
      toast.error('Username must be at least 3 characters');
      return;
    }
    if (!/^[a-zA-Z0-9_]+$/.test(trimmed)) {
      toast.error('Username can only contain letters, numbers, and underscores');
      return;
    }
    if (!usernamePassword) {
      toast.error('Enter your password to confirm');
      return;
    }
    setUsernameSaving(true);
    try {
      const res = await api.put('/api/user/change-username', {
        new_username: trimmed,
        password: usernamePassword
      });
      // Update token + user in auth context with new username
      const newToken = res.data.access_token;
      authLogin(newToken, { ...user, username: res.data.username });
      setUsernamePassword('');
      toast.success('Username updated!');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to change username');
    } finally {
      setUsernameSaving(false);
    }
  };

  // ── Bio ──
  const handleBioSave = async (e) => {
    e.preventDefault();
    setBioSaving(true);
    try {
      const res = await api.put('/api/user/update-bio', { bio: bio.trim() });
      authLogin(token, { ...user, bio: res.data.bio });
      toast.success('Bio updated!');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to update bio');
    } finally {
      setBioSaving(false);
    }
  };

  // ── Email ──
  const handleEmailSave = async (e) => {
    e.preventDefault();
    if (!emailPassword) {
      toast.error('Enter your password to confirm');
      return;
    }
    setEmailSaving(true);
    try {
      const res = await api.put('/api/user/update-email', { email: email.trim(), password: emailPassword });
      authLogin(token, { ...user, email: res.data.email });
      setEmailPassword('');
      toast.success('Email updated!');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to update email');
    } finally {
      setEmailSaving(false);
    }
  };

  // ── Password ──
  const handlePasswordChange = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmNewPassword) {
      toast.error('Passwords do not match');
      return;
    }
    if (newPassword.length < 6) {
      toast.error('New password must be at least 6 characters');
      return;
    }
    setPasswordSaving(true);
    try {
      await api.put('/api/user/change-password', {
        current_password: currentPassword,
        new_password: newPassword
      });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
      toast.success('Password changed!');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to change password');
    } finally {
      setPasswordSaving(false);
    }
  };

  // ── Delete Account ──
  const handleDeleteAccount = async (e) => {
    e.preventDefault();
    if (!deletePassword) {
      toast.error('Enter your password to confirm deletion');
      return;
    }
    const ok = await confirm({
      title: 'Delete Account',
      message: 'This will permanently delete your account, all your recipes, comments, and ratings. This action cannot be undone.',
      confirmText: 'Delete My Account',
      danger: true
    });
    if (!ok) return;

    setDeleting(true);
    try {
      await api.delete('/api/user/delete-account', { data: { password: deletePassword } });
      toast.success('Account deleted. Goodbye!');
      logout();
      navigate('/');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to delete account');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="settings-page">
      <div className="container">
        <button className="back-btn" onClick={() => navigate(-1)}>
          <FaArrowLeft /> Back
        </button>

        <div className="settings-header">
          <UserAvatar username={user.username} profilePic={user.profile_pic} size="lg" />
          <div>
            <h1>Account Settings</h1>
            <p className="settings-subtitle">Manage your profile and security</p>
          </div>
        </div>

        {/* ── Username Section ── */}
        <section className="settings-card">
          <h2 className="settings-card-title"><FaUserEdit /> Change Username</h2>
          <form onSubmit={handleUsernameSave}>
            <label className="settings-label">New Username</label>
            <input
              type="text"
              className="settings-input"
              value={newUsername}
              onChange={(e) => setNewUsername(e.target.value)}
              placeholder="Letters, numbers, underscores (3-30 chars)"
              minLength={3}
              maxLength={30}
              required
            />
            <label className="settings-label">Confirm Password</label>
            <input
              type="password"
              className="settings-input"
              value={usernamePassword}
              onChange={(e) => setUsernamePassword(e.target.value)}
              placeholder="Enter your current password"
              required
            />
            <button type="submit" className="btn btn-primary" disabled={usernameSaving || newUsername.trim() === user?.username}>
              {usernameSaving ? 'Saving...' : <><FaCheck /> Update Username</>}
            </button>
          </form>
        </section>

        {/* ── Bio Section ── */}
        <section className="settings-card">
          <h2 className="settings-card-title"><FaPen /> Bio</h2>
          <form onSubmit={handleBioSave}>
            <textarea
              className="settings-textarea"
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="Tell others about yourself..."
              maxLength={500}
              rows={3}
            />
            <div className="char-count">{bio.length}/500</div>
            <button type="submit" className="btn btn-primary" disabled={bioSaving}>
              {bioSaving ? 'Saving...' : <><FaCheck /> Save Bio</>}
            </button>
          </form>
        </section>

        {/* ── Email Section ── */}
        <section className="settings-card">
          <h2 className="settings-card-title"><FaEnvelope /> Change Email</h2>
          <form onSubmit={handleEmailSave}>
            <label className="settings-label">New Email</label>
            <input
              type="email"
              className="settings-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <label className="settings-label">Confirm Password</label>
            <input
              type="password"
              className="settings-input"
              value={emailPassword}
              onChange={(e) => setEmailPassword(e.target.value)}
              placeholder="Enter your current password"
              required
            />
            <button type="submit" className="btn btn-primary" disabled={emailSaving}>
              {emailSaving ? 'Saving...' : <><FaCheck /> Update Email</>}
            </button>
          </form>
        </section>

        {/* ── Password Section ── */}
        <section className="settings-card">
          <h2 className="settings-card-title"><FaLock /> Change Password</h2>
          <form onSubmit={handlePasswordChange}>
            <label className="settings-label">Current Password</label>
            <input
              type="password"
              className="settings-input"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
            <label className="settings-label">New Password</label>
            <input
              type="password"
              className="settings-input"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="At least 6 characters"
              required
            />
            <label className="settings-label">Confirm New Password</label>
            <input
              type="password"
              className="settings-input"
              value={confirmNewPassword}
              onChange={(e) => setConfirmNewPassword(e.target.value)}
              required
            />
            <button type="submit" className="btn btn-primary" disabled={passwordSaving}>
              {passwordSaving ? 'Saving...' : <><FaLock /> Change Password</>}
            </button>
          </form>
        </section>

        {/* ── Danger Zone ── */}
        <section className="settings-card danger-zone">
          <h2 className="settings-card-title danger-title"><FaExclamationTriangle /> Danger Zone</h2>
          <p className="danger-desc">
            Deleting your account is permanent. All your recipes, comments, and ratings will be removed.
          </p>
          <form onSubmit={handleDeleteAccount}>
            <label className="settings-label">Enter your password to confirm</label>
            <input
              type="password"
              className="settings-input"
              value={deletePassword}
              onChange={(e) => setDeletePassword(e.target.value)}
              placeholder="Your current password"
              required
            />
            <button type="submit" className="btn btn-danger" disabled={deleting}>
              {deleting ? 'Deleting...' : <><FaTrash /> Delete My Account</>}
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}

export default AccountSettings;
