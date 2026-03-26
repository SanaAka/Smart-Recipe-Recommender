import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  FaUsers, FaUtensils, FaCommentDots, FaStar, FaShieldAlt,
  FaSearch, FaBan, FaUserShield, FaUser, FaTrash, FaChevronLeft,
  FaChevronRight, FaExclamationTriangle, FaFlag, FaClock, FaEye,
  FaCheck, FaTimes, FaExternalLinkAlt, FaPauseCircle
} from 'react-icons/fa';
import api from '../utils/axios';
import { AuthContext } from '../App';
import { useToast } from '../context/ToastContext';
import { useConfirm } from '../context/ConfirmContext';
import UserAvatar from '../components/UserAvatar';
import './AdminDashboard.css';

function AdminDashboard() {
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);
  const { toast } = useToast();
  const { confirm } = useConfirm();

  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [usersLoading, setUsersLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  // Reports state
  const [reports, setReports] = useState([]);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [reportFilter, setReportFilter] = useState('pending');
  const [reportsPage, setReportsPage] = useState(1);
  const [reportsTotalPages, setReportsTotalPages] = useState(1);
  const [reportsTotal, setReportsTotal] = useState(0);
  const [adminNotes, setAdminNotes] = useState({});

  // Suspend dropdown
  const [suspendDropdown, setSuspendDropdown] = useState(null);

  // Redirect non-admin users
  useEffect(() => {
    if (user && user.role !== 'admin') {
      toast.error('Admin access required');
      navigate('/');
    }
  }, [user, navigate, toast]);

  const loadStats = useCallback(async () => {
    try {
      const res = await api.get('/api/admin/stats');
      setStats(res.data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  }, []);

  const loadUsers = useCallback(async (p = 1, s = '', r = '') => {
    setUsersLoading(true);
    try {
      const params = { page: p, per_page: 15 };
      if (s) params.search = s;
      if (r) params.role = r;
      const res = await api.get('/api/admin/users', { params });
      setUsers(res.data.users);
      setTotalPages(res.data.pages);
      setTotal(res.data.total);
    } catch (err) {
      toast.error('Failed to load users');
    } finally {
      setUsersLoading(false);
    }
  }, [toast]);

  const loadReports = useCallback(async (p = 1, status = 'pending') => {
    setReportsLoading(true);
    try {
      const params = { page: p, per_page: 10 };
      if (status) params.status = status;
      const res = await api.get('/api/admin/reports', { params });
      setReports(res.data.reports);
      setReportsTotalPages(res.data.pages);
      setReportsTotal(res.data.total);
    } catch (err) {
      toast.error('Failed to load reports');
    } finally {
      setReportsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    if (user?.role === 'admin') {
      Promise.all([loadStats(), loadUsers(1), loadReports(1, 'pending')]).finally(() => setLoading(false));
    }
  }, [user, loadStats, loadUsers, loadReports]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    loadUsers(1, search, roleFilter);
  };

  const handleRoleFilter = (r) => {
    setRoleFilter(r);
    setPage(1);
    loadUsers(1, search, r);
  };

  const handlePageChange = (newPage) => {
    setPage(newPage);
    loadUsers(newPage, search, roleFilter);
  };

  const handleSetRole = async (userId, username, newRole) => {
    const actionLabel = newRole === 'banned' ? `ban ${username}` : `set ${username} to ${newRole}`;
    const confirmed = await confirm({
      title: newRole === 'banned' ? 'Ban User' : 'Change Role',
      message: `Are you sure you want to ${actionLabel}?`,
      confirmText: newRole === 'banned' ? 'Ban' : 'Confirm',
      danger: newRole === 'banned'
    });
    if (!confirmed) return;

    try {
      await api.put(`/api/admin/users/${userId}/role`, { role: newRole });
      toast.success(`${username} is now ${newRole}`);
      loadUsers(page, search, roleFilter);
      loadStats();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to update role');
    }
  };

  const handleDeleteUser = async (userId, username) => {
    const confirmed = await confirm({
      title: 'Delete User',
      message: `Permanently delete ${username} and ALL their content? This cannot be undone.`,
      confirmText: 'Delete',
      danger: true
    });
    if (!confirmed) return;

    try {
      await api.delete(`/api/admin/users/${userId}`);
      toast.success(`User ${username} deleted`);
      loadUsers(page, search, roleFilter);
      loadStats();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to delete user');
    }
  };

  const handleSuspend = async (userId, username, duration) => {
    const durationLabels = {
      '1_day': '1 day', '3_days': '3 days', '1_week': '1 week', '2_weeks': '2 weeks', 'lift': 'lift suspension'
    };
    const label = durationLabels[duration] || duration;
    const isLift = duration === 'lift';
    const confirmed = await confirm({
      title: isLift ? 'Lift Suspension' : 'Suspend User',
      message: isLift
        ? `Remove suspension from ${username}?`
        : `Suspend ${username} for ${label}? They won't be able to log in during this period.`,
      confirmText: isLift ? 'Lift' : 'Suspend',
      danger: !isLift
    });
    if (!confirmed) return;

    try {
      await api.put(`/api/admin/users/${userId}/suspend`, { duration });
      toast.success(isLift ? `Suspension lifted for ${username}` : `${username} suspended for ${label}`);
      setSuspendDropdown(null);
      loadUsers(page, search, roleFilter);
      loadStats();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to suspend user');
    }
  };

  const handleResolveReport = async (reportId, action) => {
    try {
      await api.put(`/api/admin/reports/${reportId}/resolve`, {
        action,
        admin_notes: adminNotes[reportId] || ''
      });
      toast.success(`Report ${action === 'resolve' ? 'resolved' : 'dismissed'}`);
      setAdminNotes(prev => { const n = { ...prev }; delete n[reportId]; return n; });
      loadReports(reportsPage, reportFilter);
      loadStats();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to update report');
    }
  };

  const handleReportFilterChange = (status) => {
    setReportFilter(status);
    setReportsPage(1);
    loadReports(1, status);
  };

  const handleReportsPageChange = (newPage) => {
    setReportsPage(newPage);
    loadReports(newPage, reportFilter);
  };

  const roleBadge = (role) => {
    const map = {
      admin: { icon: <FaUserShield />, cls: 'badge-admin' },
      banned: { icon: <FaBan />, cls: 'badge-banned' },
      user: { icon: <FaUser />, cls: 'badge-user' }
    };
    const info = map[role] || map.user;
    return <span className={`role-badge ${info.cls}`}>{info.icon} {role}</span>;
  };

  const statusBadge = (status) => {
    const map = {
      pending: 'status-pending',
      reviewed: 'status-reviewed',
      resolved: 'status-resolved',
      dismissed: 'status-dismissed'
    };
    return <span className={`status-badge ${map[status] || ''}`}>{status}</span>;
  };

  const reasonLabel = (reason) => {
    const labels = {
      spam: 'Spam',
      harassment: 'Harassment',
      inappropriate_content: 'Inappropriate Content',
      fake_account: 'Fake Account',
      other: 'Other'
    };
    return labels[reason] || reason;
  };

  const isSuspended = (u) => {
    return u.suspended_until && new Date(u.suspended_until) > new Date();
  };

  const formatSuspension = (dateStr) => {
    if (!dateStr) return '';
    const until = new Date(dateStr);
    const now = new Date();
    if (until <= now) return '';
    const diff = until - now;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    if (days > 0) return `${days}d ${hours}h left`;
    return `${hours}h left`;
  };

  const formatDate = (d) => {
    if (!d) return '—';
    return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  if (!user || user.role !== 'admin') {
    return null;
  }

  if (loading) {
    return (
      <div className="admin-page">
        <div className="container">
          <div className="spinner"></div>
          <p>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-page">
      <div className="container">
        {/* Header */}
        <div className="admin-header">
          <div className="admin-title">
            <FaShieldAlt className="admin-icon" />
            <h1>Admin Dashboard</h1>
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="stats-grid">
            <div className="stat-card stat-users">
              <FaUsers className="stat-icon" />
              <div className="stat-number">{stats.total_users}</div>
              <div className="stat-label">Total Users</div>
            </div>
            <div className="stat-card stat-banned">
              <FaBan className="stat-icon" />
              <div className="stat-number">{stats.banned_users}</div>
              <div className="stat-label">Banned</div>
            </div>
            <div className="stat-card stat-suspended">
              <FaPauseCircle className="stat-icon" />
              <div className="stat-number">{stats.suspended_users || 0}</div>
              <div className="stat-label">Suspended</div>
            </div>
            <div className="stat-card stat-reports">
              <FaFlag className="stat-icon" />
              <div className="stat-number">{stats.pending_reports || 0}</div>
              <div className="stat-label">Pending Reports</div>
            </div>
            <div className="stat-card stat-recipes">
              <FaUtensils className="stat-icon" />
              <div className="stat-number">{stats.user_recipes}</div>
              <div className="stat-label">User Recipes</div>
            </div>
            <div className="stat-card stat-comments">
              <FaCommentDots className="stat-icon" />
              <div className="stat-number">{stats.total_comments}</div>
              <div className="stat-label">Comments</div>
            </div>
            <div className="stat-card stat-ratings">
              <FaStar className="stat-icon" />
              <div className="stat-number">{stats.total_ratings}</div>
              <div className="stat-label">Ratings</div>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="admin-tabs">
          <button
            className={`admin-tab ${activeTab === 'users' ? 'active' : ''}`}
            onClick={() => setActiveTab('users')}
          >
            <FaUsers /> Users
          </button>
          <button
            className={`admin-tab ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => { setActiveTab('reports'); loadReports(1, reportFilter); }}
          >
            <FaFlag /> Reports
            {stats?.pending_reports > 0 && (
              <span className="tab-badge">{stats.pending_reports}</span>
            )}
          </button>
        </div>

        {/* User Management Tab */}
        {activeTab === 'users' && (
        <div className="user-management">
          <h2><FaUsers /> User Management</h2>

          {/* Search & Filter Bar */}
          <div className="management-toolbar">
            <form className="search-form" onSubmit={handleSearch}>
              <div className="search-input-wrap">
                <FaSearch className="search-icon" />
                <input
                  type="text"
                  placeholder="Search by username or email..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <button type="submit" className="btn btn-search">Search</button>
            </form>
            <div className="role-filters">
              {['', 'user', 'admin', 'banned'].map(r => (
                <button
                  key={r}
                  className={`filter-btn ${roleFilter === r ? 'active' : ''}`}
                  onClick={() => handleRoleFilter(r)}
                >
                  {r === '' ? 'All' : r.charAt(0).toUpperCase() + r.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Users Table */}
          <div className="users-table-wrap">
            {usersLoading ? (
              <div className="table-loading"><div className="spinner"></div></div>
            ) : users.length === 0 ? (
              <div className="no-results">No users found</div>
            ) : (
              <table className="users-table">
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Recipes</th>
                    <th>Comments</th>
                    <th>Joined</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id} className={u.role === 'banned' ? 'row-banned' : isSuspended(u) ? 'row-suspended' : ''}>
                      <td className="user-cell">
                        <div className="user-cell-info">
                          <UserAvatar username={u.username} profilePic={u.profile_pic} size="md" />
                          <div>
                            <Link to={`/user/${u.username}`} className="table-username-link">
                              {u.username} <FaExternalLinkAlt className="link-icon" />
                            </Link>
                            <div className="table-email">{u.email}</div>
                          </div>
                        </div>
                      </td>
                      <td>{roleBadge(u.role)}</td>
                      <td>
                        {isSuspended(u) ? (
                          <span className="suspension-badge">
                            <FaPauseCircle /> {formatSuspension(u.suspended_until)}
                          </span>
                        ) : (
                          <span className="status-active">Active</span>
                        )}
                      </td>
                      <td className="center">{u.recipe_count}</td>
                      <td className="center">{u.comment_count}</td>
                      <td>{formatDate(u.created_at)}</td>
                      <td className="actions-cell">
                        {u.id !== user.id && (
                          <div className="action-buttons">
                            {/* View Profile */}
                            <Link to={`/user/${u.username}`} className="btn-action btn-view" title="View profile">
                              <FaEye />
                            </Link>

                            {/* Ban/Unban */}
                            {u.role === 'banned' ? (
                              <button
                                className="btn-action btn-unban"
                                onClick={() => handleSetRole(u.id, u.username, 'user')}
                                title="Unban user"
                              >
                                <FaUser /> Unban
                              </button>
                            ) : (
                              <button
                                className="btn-action btn-ban"
                                onClick={() => handleSetRole(u.id, u.username, 'banned')}
                                title="Ban user"
                              >
                                <FaBan /> Ban
                              </button>
                            )}

                            {/* Suspend dropdown */}
                            {u.role !== 'banned' && u.role !== 'admin' && (
                              <div className="suspend-dropdown-wrap">
                                <button
                                  className={`btn-action btn-suspend ${isSuspended(u) ? 'is-suspended' : ''}`}
                                  onClick={() => setSuspendDropdown(suspendDropdown === u.id ? null : u.id)}
                                  title={isSuspended(u) ? 'Manage suspension' : 'Suspend user'}
                                >
                                  <FaClock /> {isSuspended(u) ? 'Suspended' : 'Suspend'}
                                </button>
                                {suspendDropdown === u.id && (
                                  <div className="suspend-dropdown">
                                    {isSuspended(u) && (
                                      <button onClick={() => handleSuspend(u.id, u.username, 'lift')} className="suspend-option lift">
                                        <FaCheck /> Lift Suspension
                                      </button>
                                    )}
                                    <button onClick={() => handleSuspend(u.id, u.username, '1_day')} className="suspend-option">1 Day</button>
                                    <button onClick={() => handleSuspend(u.id, u.username, '3_days')} className="suspend-option">3 Days</button>
                                    <button onClick={() => handleSuspend(u.id, u.username, '1_week')} className="suspend-option">1 Week</button>
                                    <button onClick={() => handleSuspend(u.id, u.username, '2_weeks')} className="suspend-option">2 Weeks</button>
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Promote/Demote */}
                            {u.role !== 'admin' ? (
                              <button
                                className="btn-action btn-promote"
                                onClick={() => handleSetRole(u.id, u.username, 'admin')}
                                title="Promote to admin"
                              >
                                <FaUserShield />
                              </button>
                            ) : (
                              <button
                                className="btn-action btn-demote"
                                onClick={() => handleSetRole(u.id, u.username, 'user')}
                                title="Demote to user"
                              >
                                <FaUser />
                              </button>
                            )}

                            {/* Delete */}
                            <button
                              className="btn-action btn-delete"
                              onClick={() => handleDeleteUser(u.id, u.username)}
                              title="Delete user"
                            >
                              <FaTrash />
                            </button>
                          </div>
                        )}
                        {u.id === user.id && (
                          <span className="you-badge">You</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button
                disabled={page <= 1}
                onClick={() => handlePageChange(page - 1)}
                className="page-btn"
              >
                <FaChevronLeft />
              </button>
              <span className="page-info">
                Page {page} of {totalPages} ({total} users)
              </span>
              <button
                disabled={page >= totalPages}
                onClick={() => handlePageChange(page + 1)}
                className="page-btn"
              >
                <FaChevronRight />
              </button>
            </div>
          )}
        </div>
        )}

        {/* Reports Tab */}
        {activeTab === 'reports' && (
        <div className="user-management reports-section">
          <h2><FaFlag /> User Reports</h2>

          {/* Report Status Filters */}
          <div className="management-toolbar">
            <div className="role-filters">
              {['pending', 'reviewed', 'resolved', 'dismissed', ''].map(s => (
                <button
                  key={s}
                  className={`filter-btn ${reportFilter === s ? 'active' : ''}`}
                  onClick={() => handleReportFilterChange(s)}
                >
                  {s === '' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
                  {s === 'pending' && stats?.pending_reports > 0 && (
                    <span className="filter-count">{stats.pending_reports}</span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Reports List */}
          {reportsLoading ? (
            <div className="table-loading"><div className="spinner"></div></div>
          ) : reports.length === 0 ? (
            <div className="no-results">No reports found</div>
          ) : (
            <div className="reports-list">
              {reports.map(report => (
                <div key={report.id} className={`report-card report-${report.status}`}>
                  <div className="report-card-header">
                    <div className="report-meta">
                      {statusBadge(report.status)}
                      <span className="report-reason-badge">{reasonLabel(report.reason)}</span>
                      <span className="report-date">{formatDate(report.created_at)}</span>
                    </div>
                    <div className="report-id">#{report.id}</div>
                  </div>

                  <div className="report-parties">
                    <div className="report-party">
                      <span className="party-label">Reporter:</span>
                      <Link to={`/user/${report.reporter_username}`} className="party-link">
                        <UserAvatar username={report.reporter_username} profilePic={report.reporter_pic} size="sm" />
                        {report.reporter_username}
                      </Link>
                    </div>
                    <span className="report-arrow">→</span>
                    <div className="report-party">
                      <span className="party-label">Reported:</span>
                      <Link to={`/user/${report.reported_username}`} className="party-link">
                        <UserAvatar username={report.reported_username} profilePic={report.reported_pic} size="sm" />
                        {report.reported_username}
                      </Link>
                    </div>
                  </div>

                  {report.description && (
                    <div className="report-description">
                      <strong>Description:</strong> {report.description}
                    </div>
                  )}

                  {report.admin_notes && (
                    <div className="report-admin-notes">
                      <strong>Admin Notes:</strong> {report.admin_notes}
                      {report.resolved_by_username && (
                        <span className="resolved-by"> — {report.resolved_by_username}</span>
                      )}
                    </div>
                  )}

                  {report.status === 'pending' && (
                    <div className="report-actions">
                      <textarea
                        className="notes-input"
                        placeholder="Admin notes (optional)..."
                        value={adminNotes[report.id] || ''}
                        onChange={(e) => setAdminNotes(prev => ({ ...prev, [report.id]: e.target.value }))}
                        rows={2}
                      />
                      <div className="report-action-btns">
                        <button
                          className="btn-action btn-resolve"
                          onClick={() => handleResolveReport(report.id, 'resolve')}
                        >
                          <FaCheck /> Resolve
                        </button>
                        <button
                          className="btn-action btn-dismiss"
                          onClick={() => handleResolveReport(report.id, 'dismiss')}
                        >
                          <FaTimes /> Dismiss
                        </button>
                        <Link to={`/user/${report.reported_username}`} className="btn-action btn-view">
                          <FaEye /> View Profile
                        </Link>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Reports Pagination */}
          {reportsTotalPages > 1 && (
            <div className="pagination">
              <button
                disabled={reportsPage <= 1}
                onClick={() => handleReportsPageChange(reportsPage - 1)}
                className="page-btn"
              >
                <FaChevronLeft />
              </button>
              <span className="page-info">
                Page {reportsPage} of {reportsTotalPages} ({reportsTotal} reports)
              </span>
              <button
                disabled={reportsPage >= reportsTotalPages}
                onClick={() => handleReportsPageChange(reportsPage + 1)}
                className="page-btn"
              >
                <FaChevronRight />
              </button>
            </div>
          )}
        </div>
        )}

        {/* Warning Footer */}
        <div className="admin-warning">
          <FaExclamationTriangle />
          <span>Admin actions are logged and cannot be undone. Use with care.</span>
        </div>
      </div>
    </div>
  );
}

export default AdminDashboard;
