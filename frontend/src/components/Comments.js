import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../App';
import { useToast } from '../context/ToastContext';
import { useConfirm } from '../context/ConfirmContext';
import api from '../utils/axios';
import UserAvatar from './UserAvatar';
import './Comments.css';

// ─── Reaction Button ────────────────────────────────────────────────
const ReactionButtons = ({ likes = 0, dislikes = 0, userReaction, onReact, disabled }) => (
  <div className="reaction-buttons">
    <button
      className={`reaction-btn like-btn ${userReaction === 'like' ? 'active' : ''}`}
      onClick={() => onReact('like')}
      disabled={disabled}
      title="Like"
    >
      👍 <span>{likes}</span>
    </button>
    <button
      className={`reaction-btn dislike-btn ${userReaction === 'dislike' ? 'active' : ''}`}
      onClick={() => onReact('dislike')}
      disabled={disabled}
      title="Dislike"
    >
      👎 <span>{dislikes}</span>
    </button>
  </div>
);

// ─── Reply Item ─────────────────────────────────────────────────────
const ReplyItem = ({ reply, user, onDelete, onReact, formatDate }) => (
  <div className="reply-item">
    <div className="reply-header">
      <div className="comment-author">
        <UserAvatar username={reply.username} profilePic={reply.profile_pic} size="sm" />
        <Link to={`/user/${reply.username}`} className="username-link"><strong>{reply.username}</strong></Link>
        <span className="comment-date">{formatDate(reply.created_at)}</span>
      </div>
      {user && user.username === reply.username && (
        <button className="delete-btn" onClick={() => onDelete(reply.id)} title="Delete reply">
          🗑️
        </button>
      )}
    </div>
    <p className="comment-text reply-text">{reply.reply}</p>
    <ReactionButtons
      likes={reply.likes}
      dislikes={reply.dislikes}
      userReaction={reply.user_reaction}
      onReact={(type) => onReact(reply.id, type)}
      disabled={!user}
    />
  </div>
);

// ─── Reply Section ──────────────────────────────────────────────────
const ReplySection = ({ commentId, user, formatDate, initialReplyCount = 0 }) => {
  const { toast } = useToast();
  const { confirm } = useConfirm();
  const [replies, setReplies] = useState([]);
  const [showReplies, setShowReplies] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(false);
  const [replyCount, setReplyCount] = useState(initialReplyCount);

  const fetchReplies = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/api/comments/${commentId}/replies`);
      setReplies(res.data.replies);
      setReplyCount(res.data.total);
    } catch (err) {
      console.error('Failed to fetch replies:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleReplies = () => {
    if (!showReplies) fetchReplies();
    setShowReplies(!showReplies);
  };

  const handleSubmitReply = async (e) => {
    e.preventDefault();
    if (!replyText.trim()) return;
    try {
      setSubmitting(true);
      const res = await api.post(`/api/comments/${commentId}/replies`, { reply: replyText });
      setReplies(prev => [...prev, res.data.reply]);
      setReplyCount(prev => prev + 1);
      setReplyText('');
      setShowForm(false);
      setShowReplies(true);
      toast.success('Reply posted!');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to post reply');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteReply = async (replyId) => {
    const ok = await confirm({
      title: 'Delete Reply',
      message: 'This reply will be permanently removed.',
      confirmText: 'Delete',
      cancelText: 'Keep',
      variant: 'danger',
    });
    if (!ok) return;
    try {
      await api.delete(`/api/replies/${replyId}`);
      setReplies(prev => prev.filter(r => r.id !== replyId));
      setReplyCount(prev => prev - 1);
      toast.success('Reply deleted');
    } catch (err) {
      toast.error('Failed to delete reply');
    }
  };

  const handleReplyReaction = async (replyId, type) => {
    if (!user) { toast.warning('Login to react'); return; }
    try {
      const res = await api.post(`/api/replies/${replyId}/react`, { reaction: type });
      setReplies(prev => prev.map(r => r.id === replyId ? {
        ...r,
        likes: res.data.likes,
        dislikes: res.data.dislikes,
        user_reaction: res.data.user_reaction
      } : r));
    } catch (err) {
      toast.error('Failed to react');
    }
  };

  return (
    <div className="reply-section">
      <div className="reply-actions">
        {user && (
          <button className="reply-toggle-btn" onClick={() => setShowForm(!showForm)}>
            💬 Reply
          </button>
        )}
        {replyCount > 0 && (
          <button className="reply-toggle-btn" onClick={handleToggleReplies}>
            {showReplies ? '▲ Hide' : '▼ Show'} {replyCount} {replyCount === 1 ? 'reply' : 'replies'}
          </button>
        )}
      </div>

      {showForm && (
        <form className="reply-form" onSubmit={handleSubmitReply}>
          <textarea
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            placeholder="Write a reply..."
            maxLength={1000}
            rows={2}
            disabled={submitting}
          />
          <div className="reply-form-actions">
            <span className="char-count">{replyText.length}/1000</span>
            <div>
              <button type="button" className="cancel-btn" onClick={() => { setShowForm(false); setReplyText(''); }}>
                Cancel
              </button>
              <button type="submit" className="submit-btn" disabled={submitting || !replyText.trim()}>
                {submitting ? 'Posting...' : 'Reply'}
              </button>
            </div>
          </div>
        </form>
      )}

      {showReplies && (
        <div className="replies-list">
          {loading ? (
            <div className="loading-replies">Loading replies...</div>
          ) : (
            replies.map(reply => (
              <ReplyItem
                key={reply.id}
                reply={reply}
                user={user}
                onDelete={handleDeleteReply}
                onReact={handleReplyReaction}
                formatDate={formatDate}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
};

// ─── Main Comments Component ────────────────────────────────────────
const Comments = ({ recipeId }) => {
  const { user } = useContext(AuthContext);
  const { toast } = useToast();
  const { confirm } = useConfirm();
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchComments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recipeId, page]);

  const fetchComments = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/recipe/${recipeId}/comments`, {
        params: { page, limit: 20 }
      });
      
      if (page === 1) {
        setComments(response.data.comments);
      } else {
        setComments(prev => [...prev, ...response.data.comments]);
      }
      
      setHasMore(response.data.has_more);
    } catch (err) {
      console.error('Failed to fetch comments:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!user) {
      setError('Please login to comment');
      return;
    }
    
    if (!newComment.trim()) {
      setError('Comment cannot be empty');
      return;
    }
    
    try {
      setSubmitting(true);
      setError('');
      
      const response = await api.post(`/api/recipe/${recipeId}/comments`, {
        comment: newComment
      });
      
      const newC = response.data.comment;
      newC.likes = 0;
      newC.dislikes = 0;
      newC.reply_count = 0;
      newC.user_reaction = null;

      setComments([newC, ...comments]);
      setNewComment('');
      toast.success('Comment posted!');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to post comment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (commentId) => {
    const ok = await confirm({
      title: 'Delete Comment',
      message: 'This comment and all its replies will be permanently removed.',
      confirmText: 'Delete',
      cancelText: 'Keep it',
      variant: 'danger',
    });
    if (!ok) return;
    
    try {
      await api.delete(`/api/recipe/${recipeId}/comments/${commentId}`);
      setComments(comments.filter(c => c.id !== commentId));
      toast.success('Comment deleted');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to delete comment');
    }
  };

  const handleCommentReaction = async (commentId, type) => {
    if (!user) { toast.warning('Login to react'); return; }
    try {
      const res = await api.post(`/api/comments/${commentId}/react`, { reaction: type });
      setComments(prev => prev.map(c => c.id === commentId ? {
        ...c,
        likes: res.data.likes,
        dislikes: res.data.dislikes,
        user_reaction: res.data.user_reaction
      } : c));
    } catch (err) {
      toast.error('Failed to react');
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="comments-section">
      <h3 className="comments-title">
        💬 Comments {comments.length > 0 && `(${comments.length})`}
      </h3>
      
      {/* Comment Form */}
      {user ? (
        <form className="comment-form" onSubmit={handleSubmit}>
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Share your thoughts about this recipe..."
            maxLength={1000}
            rows={3}
            disabled={submitting}
          />
          {error && <p className="error-message">{error}</p>}
          <div className="form-footer">
            <span className="char-count">{newComment.length}/1000</span>
            <button 
              type="submit" 
              disabled={submitting || !newComment.trim()}
              className="submit-btn"
            >
              {submitting ? 'Posting...' : 'Post Comment'}
            </button>
          </div>
        </form>
      ) : (
        <div className="login-prompt">
          Please <a href="/login">login</a> to leave a comment
        </div>
      )}
      
      {/* Comments List */}
      <div className="comments-list">
        {loading && page === 1 ? (
          <div className="loading-comments">
            <div className="spinner"></div>
            Loading comments...
          </div>
        ) : comments.length === 0 ? (
          <p className="no-comments">No comments yet. Be the first to share your thoughts!</p>
        ) : (
          <>
            {comments.map(comment => (
              <div key={comment.id} className="comment-item">
                <div className="comment-header">
                  <div className="comment-author">
                    <UserAvatar username={comment.username} profilePic={comment.profile_pic} size="md" />
                    <Link to={`/user/${comment.username}`} className="username-link"><strong>{comment.username}</strong></Link>
                  </div>
                  <div className="comment-meta">
                    <span className="comment-date">{formatDate(comment.created_at)}</span>
                    {user && user.username === comment.username && (
                      <button
                        className="delete-btn"
                        onClick={() => handleDelete(comment.id)}
                        title="Delete comment"
                      >
                        🗑️
                      </button>
                    )}
                  </div>
                </div>
                <p className="comment-text">{comment.comment}</p>

                {/* Reactions */}
                <ReactionButtons
                  likes={comment.likes || 0}
                  dislikes={comment.dislikes || 0}
                  userReaction={comment.user_reaction}
                  onReact={(type) => handleCommentReaction(comment.id, type)}
                  disabled={!user}
                />

                {/* Replies */}
                <ReplySection
                  commentId={comment.id}
                  user={user}
                  formatDate={formatDate}
                  initialReplyCount={comment.reply_count || 0}
                />
              </div>
            ))}
            
            {hasMore && (
              <button 
                className="load-more-btn" 
                onClick={() => setPage(p => p + 1)}
                disabled={loading}
              >
                {loading ? 'Loading...' : 'Load More Comments'}
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Comments;
