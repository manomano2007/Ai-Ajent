import { ChatIcon, CloseIcon, PlusIcon, LogoMark } from "./icons.jsx";

export default function Sidebar({
  onNewChat,
  onClose,
  newChatDisabled,
  sessionTitle,
  messageCount,
}) {
  const countLabel =
    messageCount === 0
      ? "No messages yet"
      : `${messageCount} message${messageCount === 1 ? "" : "s"}`;

  return (
    <aside className="sidebar" aria-label="Chat sidebar">
      <div className="sidebar-top">
        <div className="sidebar-brand">
          <LogoMark />
          <span>PyMate AI</span>
        </div>
        <button
          type="button"
          className="icon-button mobile-only"
          onClick={onClose}
          aria-label="Close sidebar"
        >
          <CloseIcon />
        </button>
      </div>

      <button
        type="button"
        className="new-chat-button"
        onClick={onNewChat}
        disabled={newChatDisabled}
      >
        <PlusIcon />
        <span>New chat</span>
      </button>

      <div className="sidebar-section">
        <p className="section-label">Current session</p>
        <div className="session-item active" aria-current="true">
          <ChatIcon />
          <div className="session-text">
            <span className="session-title">{sessionTitle || "New conversation"}</span>
            <span className="session-meta">{countLabel}</span>
          </div>
        </div>
      </div>

      <div className="sidebar-footer">
        Chats stay in this browser tab. Refreshing the page starts a new session.
      </div>
    </aside>
  );
}