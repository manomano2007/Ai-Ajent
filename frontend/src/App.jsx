import { useEffect, useRef, useState } from "react";
import { checkBackendHealth, sendChatMessage } from "./api.js";
import MessageContent from "./components/MessageContent.jsx";
import Sidebar from "./components/Sidebar.jsx";
import { LogoMark, RetryIcon, SendIcon, SparkIcon, MenuIcon } from "./components/icons.jsx";

const PROMPT_SUGGESTIONS = [
  { label: "Learn", text: "Explain Python list comprehensions with a simple example." },
  { label: "Build", text: "Write a Python function that checks whether a number is prime." },
  { label: "Concepts", text: "What is the difference between a list and a tuple?" },
  { label: "Files", text: "How do I read a CSV file with Python?" },
];

const MAX_MESSAGE_CHARS = 8000;
const DESKTOP_BREAKPOINT = 900;

function makeId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function StatusPill({ online }) {
  const state = online === null ? "checking" : online ? "online" : "offline";
  const text =
    state === "checking"
      ? "Connecting..."
      : state === "online"
      ? "Backend online"
      : "Backend offline";
  const title =
    state === "offline" ? "Start the backend at http://127.0.0.1:8000" : undefined;

  return (
    <span className={`status-pill ${state}`} role="status" title={title}>
      <span className="status-dot" aria-hidden="true" />
      {text}
    </span>
  );
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [failedText, setFailedText] = useState(null);
  const [backendOnline, setBackendOnline] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(
    () => typeof window !== "undefined" && window.innerWidth > DESKTOP_BREAKPOINT
  );
  const textareaRef = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    let active = true;
    checkBackendHealth().then((ok) => {
      if (active) setBackendOnline(ok);
    });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
  }, [input]);

  const sessionTitle = messages.find((m) => m.role === "user")?.text ?? "";
  const isEmpty = messages.length === 0 && !loading;

  async function requestReply(text) {
    setLoading(true);
    setError(null);
    setFailedText(null);

    try {
      const reply = await sendChatMessage(text);
      setMessages((prev) => [...prev, { id: makeId(), role: "assistant", text: reply }]);
      setBackendOnline(true);
    } catch (err) {
      setError(err.message);
      setFailedText(text);
      if (err.network) setBackendOnline(false);
    } finally {
      setLoading(false);
    }
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    setMessages((prev) => [...prev, { id: makeId(), role: "user", text }]);
    setInput("");
    await requestReply(text);
  }

  function handleRetry() {
    if (failedText && !loading) {
      requestReply(failedText);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    handleSend();
  }

  function handleKeyDown(event) {
    // isComposing is true while an input method (such as Tamil typing) is still composing text.
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      handleSend();
    }
  }

  function useSuggestion(text) {
    setInput(text);
    textareaRef.current?.focus();
  }

  function handleNewChat() {
    if (loading) return;
    setMessages([]);
    setInput("");
    setError(null);
    setFailedText(null);
    if (window.innerWidth <= DESKTOP_BREAKPOINT) {
      setSidebarOpen(false);
    }
    textareaRef.current?.focus();
  }

  return (
    <div className={`app-shell${sidebarOpen ? " sidebar-open" : ""}`}>
      <Sidebar
        onNewChat={handleNewChat}
        onClose={() => setSidebarOpen(false)}
        newChatDisabled={loading}
        sessionTitle={sessionTitle}
        messageCount={messages.length}
      />

      <button
        type="button"
        className="scrim"
        aria-label="Close sidebar"
        onClick={() => setSidebarOpen(false)}
        tabIndex={sidebarOpen ? 0 : -1}
      />

      <div className="main">
        <header className="topbar">
          <div className="topbar-left">
            <button
              type="button"
              className="icon-button"
              onClick={() => setSidebarOpen((open) => !open)}
              aria-label={sidebarOpen ? "Hide sidebar" : "Show sidebar"}
              aria-expanded={sidebarOpen}
            >
              <MenuIcon />
            </button>
            <div className="brand">
              <LogoMark />
              <div className="brand-text">
                <h1>PyMate AI</h1>
                <p className="subtitle">Your AI Python Learning Companion</p>
              </div>
            </div>
          </div>
          <StatusPill online={backendOnline} />
        </header>

        <main className="chat" role="log" aria-live="polite">
          <div className="chat-inner">
            {isEmpty ? (
              <section className="welcome">
                <LogoMark large />
                <h2>Ask anything about Python</h2>
                <p>
                  Get clear explanations, working code, and help fixing bugs. Pick a starting
                  point below or write your own question.
                </p>
                <div className="suggestion-grid">
                  {PROMPT_SUGGESTIONS.map((suggestion) => (
                    <button
                      key={suggestion.text}
                      type="button"
                      className="suggestion-card"
                      onClick={() => useSuggestion(suggestion.text)}
                    >
                      <span className="suggestion-label">{suggestion.label}</span>
                      <span className="suggestion-text">{suggestion.text}</span>
                    </button>
                  ))}
                </div>
              </section>
            ) : (
              <div className="message-list">
                {messages.map((message) =>
                  message.role === "user" ? (
                    <div key={message.id} className="message user">
                      <div className="user-bubble">
                        <p>{message.text}</p>
                      </div>
                    </div>
                  ) : (
                    <div key={message.id} className="message assistant">
                      <div className="avatar" aria-hidden="true">
                        <SparkIcon width={15} height={15} />
                      </div>
                      <div className="message-body">
                        <MessageContent text={message.text} />
                      </div>
                    </div>
                  )
                )}

                {loading && (
                  <div className="message assistant">
                    <div className="avatar" aria-hidden="true">
                      <SparkIcon width={15} height={15} />
                    </div>
                    <div className="message-body thinking">
                      <div className="typing" aria-hidden="true">
                        <span />
                        <span />
                        <span />
                      </div>
                      <span className="thinking-text">PyMate AI is thinking...</span>
                    </div>
                  </div>
                )}

                <div ref={bottomRef} />
              </div>
            )}
          </div>
        </main>

        <div className="composer-area">
          {error && (
            <div className="error-banner" role="alert">
              <span>{error}</span>
              {failedText && (
                <button type="button" className="retry-button" onClick={handleRetry} disabled={loading}>
                  <RetryIcon width={14} height={14} />
                  <span>Retry</span>
                </button>
              )}
            </div>
          )}

          <form className="composer" onSubmit={handleSubmit}>
            <div className={`composer-box${loading ? " is-loading" : ""}`}>
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a Python question, or paste your code and error..."
                aria-label="Message PyMate AI"
                rows={1}
                maxLength={MAX_MESSAGE_CHARS}
              />
              <button
                type="submit"
                className="send-button"
                disabled={loading || !input.trim()}
                aria-label={loading ? "Waiting for reply" : "Send message"}
              >
                {loading ? <span className="spinner" aria-hidden="true" /> : <SendIcon />}
              </button>
            </div>
            <p className="composer-hint">
              {loading
                ? "PyMate AI is working on your answer..."
                : "Enter to send  ·  Shift+Enter for a new line"}
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}