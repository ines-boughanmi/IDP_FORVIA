import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  fetchChatbotQuery,
  fetchChatbotStatus,
  fetchConversations,
  fetchConversationDetail,
  deleteConversation,
  deleteAllConversations,
  type ConversationSummary,
} from '@/services/backendApi';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type AssistantMessage = {
  role: 'assistant';
  text: string;
  sources: string[];
  confidence: number;
  timestamp: Date;
};

type UserMessage = {
  role: 'user';
  text: string;
  timestamp: Date;
};

type Message = UserMessage | AssistantMessage;

// ---------------------------------------------------------------------------
// Starter questions
// ---------------------------------------------------------------------------

const STARTERS = [
  'Which suppliers have the highest risk score?',
  'What transactions contain anomalies?',
  'Show me all HIGH_RISK_SUPPLIERS cluster members',
  'Which contracts have the largest amounts?',
  'What is the average risk score across all transactions?',
  'Show details for supplier 113907',
  'Which suppliers are classified as CRITICAL risk?',
  'How many delayed transactions are there?',
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffDays = Math.floor(diffMs / 86_400_000);
  if (diffDays === 0) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return d.toLocaleDateString([], { weekday: 'short' });
  return d.toLocaleDateString([], { day: 'numeric', month: 'short' });
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ConfidenceBadge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 70 ? 'var(--green)' : pct >= 40 ? 'var(--amber)' : 'var(--red)';
  const bg =
    pct >= 70
      ? 'rgba(84,192,138,0.12)'
      : pct >= 40
      ? 'rgba(255,181,71,0.12)'
      : 'rgba(243,111,124,0.12)';
  return (
    <span
      style={{
        fontSize: '11px',
        padding: '2px 9px',
        borderRadius: '999px',
        background: bg,
        color,
        fontWeight: 700,
        letterSpacing: '0.04em',
      }}
    >
      {pct}% match
    </span>
  );
}

function SourceTag({ label }: { label: string }) {
  return (
    <span
      style={{
        fontSize: '11px',
        padding: '2px 9px',
        borderRadius: '999px',
        background: 'rgba(127,179,255,0.1)',
        color: 'var(--blue)',
        border: '1px solid rgba(127,179,255,0.18)',
        fontWeight: 600,
      }}
    >
      {label}
    </span>
  );
}

function TypingDots() {
  return (
    <div style={{ display: 'flex', gap: '4px', alignItems: 'center', height: '20px' }}>
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            background: 'var(--muted)',
            display: 'inline-block',
            animation: `pulse-dot 1.2s ease-in-out ${i * 0.2}s infinite`,
          }}
        />
      ))}
      <style>{`
        @keyframes pulse-dot {
          0%, 80%, 100% { opacity: 0.3; transform: scale(0.85); }
          40%            { opacity: 1;   transform: scale(1.1);  }
        }
      `}</style>
    </div>
  );
}

function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user';
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        gap: '6px',
      }}
    >
      <span
        style={{
          fontSize: '11px',
          fontWeight: 700,
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          color: isUser ? 'var(--blue)' : 'var(--muted)',
        }}
      >
        {isUser ? 'You' : 'P2P Copilot'}
      </span>

      <div
        style={{
          maxWidth: '78%',
          padding: '12px 16px',
          borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
          background: isUser ? 'var(--blue-strong)' : 'var(--panel-2)',
          border: isUser ? 'none' : '1px solid var(--border)',
          lineHeight: 1.65,
          fontSize: '14px',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {msg.text}
      </div>

      {!isUser && (msg as AssistantMessage).sources?.length > 0 && (
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '6px',
            maxWidth: '78%',
            alignItems: 'center',
          }}
        >
          <ConfidenceBadge value={(msg as AssistantMessage).confidence} />
          {(msg as AssistantMessage).sources.map((s, i) => (
            <SourceTag key={i} label={s} />
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Conversation sidebar item
// ---------------------------------------------------------------------------

function ConvItem({
  conv,
  isActive,
  onSelect,
  onDelete,
}: {
  conv: ConversationSummary;
  isActive: boolean;
  onSelect: () => void;
  onDelete: (e: React.MouseEvent) => void;
}) {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      onClick={onSelect}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '10px',
        padding: '10px 12px',
        borderRadius: '10px',
        cursor: 'pointer',
        background: isActive
          ? 'rgba(127,179,255,0.12)'
          : hovered
          ? 'rgba(255,255,255,0.04)'
          : 'transparent',
        border: isActive ? '1px solid rgba(127,179,255,0.22)' : '1px solid transparent',
        transition: 'background 0.15s, border-color 0.15s',
      }}
    >
      {/* Chat icon */}
      <svg
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="none"
        stroke={isActive ? 'var(--blue)' : 'var(--muted)'}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{ flexShrink: 0, marginTop: '2px' }}
      >
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>

      {/* Text */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: '13px',
            fontWeight: isActive ? 600 : 400,
            color: isActive ? 'var(--blue)' : 'var(--text)',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            lineHeight: 1.4,
          }}
        >
          {conv.title}
        </div>
        <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px' }}>
          {formatDate(conv.updated_at)} · {conv.message_count / 2 | 0} exchange{conv.message_count / 2 !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Delete button */}
      <button
        onClick={onDelete}
        title="Delete conversation"
        style={{
          flexShrink: 0,
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: '2px 4px',
          color: hovered ? 'var(--red)' : 'transparent',
          transition: 'color 0.15s',
          lineHeight: 1,
        }}
      >
        <svg
          width="13"
          height="13"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="3 6 5 6 21 6" />
          <path d="M19 6l-1 14H6L5 6" />
          <path d="M10 11v6M14 11v6" />
          <path d="M9 6V4h6v2" />
        </svg>
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export function ChatbotPage() {
  const queryClient = useQueryClient();

  const [input, setInput]           = useState('');
  const [messages, setMessages]     = useState<Message[]>([]);
  const [currentConvId, setCurrentConvId] = useState<number | null>(null);
  const [loadingConvId, setLoadingConvId] = useState<number | null>(null);
  const [confirmDeleteAll, setConfirmDeleteAll] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  // ── Status polling ─────────────────────────────────────────────────────────
  const { data: statusData } = useQuery({
    queryKey: ['chatbot-status'],
    queryFn: fetchChatbotStatus,
    refetchInterval: (data: any) => (data?.ready ? 30_000 : 5_000),
    staleTime: 0,
  });

  const isReady    = !!(statusData as any)?.ready;
  const isBuilding = !!(statusData as any)?.building;
  const docCount   = (statusData as any)?.documents ?? 0;
  const sources    = (statusData as any)?.sources   ?? [];

  // ── Conversation list ──────────────────────────────────────────────────────
  const { data: conversations = [] } = useQuery({
    queryKey: ['conversations'],
    queryFn: fetchConversations,
    staleTime: 10_000,
  });

  // ── Load a past conversation ───────────────────────────────────────────────
  const { data: loadedConv, isFetching: isLoadingConv } = useQuery({
    queryKey: ['conversation', loadingConvId],
    queryFn: () => fetchConversationDetail(loadingConvId!),
    enabled: !!loadingConvId,
    staleTime: 0,
  });

  useEffect(() => {
    if (!loadedConv || !loadingConvId) return;
    const msgs: Message[] = loadedConv.messages.map((m) =>
      m.role === 'user'
        ? { role: 'user' as const, text: m.content, timestamp: new Date(m.created_at) }
        : {
            role: 'assistant' as const,
            text: m.content,
            sources: m.sources,
            confidence: m.confidence,
            timestamp: new Date(m.created_at),
          }
    );
    setMessages(msgs);
    setCurrentConvId(loadingConvId);
  }, [loadedConv, loadingConvId]);

  // ── Send message mutation ──────────────────────────────────────────────────
  const mutation = useMutation({
    mutationFn: (question: string) => fetchChatbotQuery(question, currentConvId),
    onSuccess(data: any) {
      const answer     = data?.answer     ?? 'No response received.';
      const srcs       = data?.sources    ?? [];
      const confidence = data?.confidence ?? 0;
      const newConvId  = data?.conversation_id ?? null;

      setMessages((m) => [
        ...m,
        { role: 'assistant', text: answer, sources: srcs, confidence, timestamp: new Date() },
      ]);

      if (newConvId && !currentConvId) {
        setCurrentConvId(newConvId);
        setLoadingConvId(null); // prevent re-loading
      }

      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
    onError() {
      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          text: 'Request failed. Please check the backend connection and try again.',
          sources: [],
          confidence: 0,
          timestamp: new Date(),
        },
      ]);
    },
  });

  // ── Delete one conversation ────────────────────────────────────────────────
  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteConversation(id),
    onSuccess(_data, id) {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      if (id === currentConvId) {
        setMessages([]);
        setCurrentConvId(null);
        setLoadingConvId(null);
      }
    },
  });

  // ── Delete all conversations ───────────────────────────────────────────────
  const deleteAllMutation = useMutation({
    mutationFn: deleteAllConversations,
    onSuccess() {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      setMessages([]);
      setCurrentConvId(null);
      setLoadingConvId(null);
      setConfirmDeleteAll(false);
    },
  });

  // ── Auto-scroll ────────────────────────────────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, mutation.isPending]);

  // ── Actions ────────────────────────────────────────────────────────────────
  function send(overrideText?: string) {
    const q = (overrideText ?? input).trim();
    if (!q || mutation.isPending) return;
    setMessages((m) => [...m, { role: 'user', text: q, timestamp: new Date() }]);
    setInput('');
    mutation.mutate(q);
  }

  function handleKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  function startNewChat() {
    setMessages([]);
    setCurrentConvId(null);
    setLoadingConvId(null);
  }

  function openConversation(id: number) {
    if (id === currentConvId) return;
    setMessages([]);
    setLoadingConvId(id);
  }

  // ── Status pill ────────────────────────────────────────────────────────────
  const pillClass = isReady ? 'success' : isBuilding ? 'warning' : 'neutral';
  const pillLabel = isReady
    ? `Ready · ${docCount.toLocaleString()} documents indexed`
    : isBuilding
    ? 'Indexing datasets — please wait…'
    : 'Initializing…';

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="page-stack">
      {/* ─── Page header ─────────────────────────────────────────────────── */}
      <div className="page-header">
        <div>
          <p className="page-kicker">AI-Powered Analysis</p>
          <h1>P2P Intelligence Copilot</h1>
          <p>
            Ask questions about suppliers, transactions, contracts, and risk
            metrics — grounded exclusively in your datasets.
          </p>
        </div>
        <span className={`status-pill ${pillClass}`}>{pillLabel}</span>
      </div>

      {/* ─── Body: sidebar + main ────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>

        {/* ── History sidebar ──────────────────────────────────────────────── */}
        <div
          className="section-card"
          style={{
            width: '260px',
            flexShrink: 0,
            padding: 0,
            display: 'flex',
            flexDirection: 'column',
            maxHeight: '680px',
          }}
        >
          {/* Sidebar header */}
          <div
            style={{
              padding: '14px 16px 10px',
              borderBottom: '1px solid var(--border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '8px',
            }}
          >
            <span
              style={{ fontSize: '12px', fontWeight: 700, color: 'var(--muted)', letterSpacing: '0.08em' }}
            >
              HISTORY
            </span>
            <button
              className="btn btn-primary"
              style={{ fontSize: '12px', padding: '5px 12px', borderRadius: '8px' }}
              onClick={startNewChat}
            >
              + New Chat
            </button>
          </div>

          {/* Conversation list */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '8px',
              display: 'flex',
              flexDirection: 'column',
              gap: '2px',
              minHeight: '120px',
            }}
          >
            {isLoadingConv && (
              <div style={{ padding: '12px', fontSize: '12px', color: 'var(--muted)', textAlign: 'center' }}>
                Loading…
              </div>
            )}

            {conversations.length === 0 && !isLoadingConv && (
              <div
                style={{
                  padding: '24px 12px',
                  fontSize: '12px',
                  color: 'var(--muted)',
                  textAlign: 'center',
                  lineHeight: 1.6,
                }}
              >
                No conversations yet.
                <br />
                Ask your first question to get started.
              </div>
            )}

            {conversations.map((conv) => (
              <ConvItem
                key={conv.id}
                conv={conv}
                isActive={conv.id === currentConvId}
                onSelect={() => openConversation(conv.id)}
                onDelete={(e) => {
                  e.stopPropagation();
                  deleteMutation.mutate(conv.id);
                }}
              />
            ))}
          </div>

          {/* Delete all footer */}
          {conversations.length > 0 && (
            <div
              style={{
                padding: '10px 12px',
                borderTop: '1px solid var(--border)',
              }}
            >
              {confirmDeleteAll ? (
                <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                  <span style={{ fontSize: '12px', color: 'var(--muted)', flex: 1 }}>
                    Delete all?
                  </span>
                  <button
                    className="btn"
                    style={{
                      fontSize: '11px',
                      padding: '4px 10px',
                      background: 'rgba(243,111,124,0.12)',
                      color: 'var(--red)',
                      border: '1px solid rgba(243,111,124,0.25)',
                      borderRadius: '6px',
                    }}
                    onClick={() => deleteAllMutation.mutate()}
                    disabled={deleteAllMutation.isPending}
                  >
                    Confirm
                  </button>
                  <button
                    className="btn btn-secondary"
                    style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '6px' }}
                    onClick={() => setConfirmDeleteAll(false)}
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  className="btn btn-secondary"
                  style={{
                    width: '100%',
                    fontSize: '12px',
                    padding: '6px',
                    color: 'var(--red)',
                    borderColor: 'rgba(243,111,124,0.2)',
                    borderRadius: '8px',
                  }}
                  onClick={() => setConfirmDeleteAll(true)}
                >
                  Delete all history
                </button>
              )}
            </div>
          )}
        </div>

        {/* ── Main content ─────────────────────────────────────────────────── */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '16px', minWidth: 0 }}>

          {/* Index summary */}
          {isReady && sources.length > 0 && (
            <div className="section-card" style={{ padding: '14px 20px' }}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
                <span style={{ fontSize: '12px', color: 'var(--muted)', fontWeight: 600 }}>
                  INDEXED SOURCES
                </span>
                {sources.map((s: string, i: number) => (
                  <SourceTag key={i} label={s} />
                ))}
              </div>
            </div>
          )}

          {/* Suggested questions (shown before first message in a new chat) */}
          {messages.length === 0 && !isLoadingConv && (
            <div className="section-card">
              <div className="section-header">
                <h3>Suggested Questions</h3>
                <p>Click any question below to get started.</p>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                {STARTERS.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => send(q)}
                    disabled={!isReady || mutation.isPending}
                    className="btn btn-secondary"
                    style={{
                      borderRadius: '20px',
                      fontSize: '13px',
                      padding: '7px 14px',
                      color: 'var(--blue)',
                      borderColor: 'rgba(127,179,255,0.2)',
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Chat area */}
          <div
            className="section-card"
            style={{ display: 'flex', flexDirection: 'column', gap: 0, padding: 0 }}
          >
            {/* Message list */}
            <div
              style={{
                padding: '24px',
                minHeight: '300px',
                maxHeight: '480px',
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
                gap: '20px',
              }}
            >
              {messages.length === 0 && !isLoadingConv && (
                <div
                  style={{
                    color: 'var(--muted)',
                    textAlign: 'center',
                    marginTop: '60px',
                    fontSize: '14px',
                  }}
                >
                  {isReady
                    ? 'Ask a question about your P2P data…'
                    : isBuilding
                    ? 'The index is being built. This takes 2–5 minutes. You can ask questions once ready.'
                    : 'Waiting for the assistant to initialise…'}
                </div>
              )}

              {isLoadingConv && (
                <div
                  style={{
                    color: 'var(--muted)',
                    textAlign: 'center',
                    marginTop: '60px',
                    fontSize: '14px',
                  }}
                >
                  Loading conversation…
                </div>
              )}

              {messages.map((m, i) => (
                <MessageBubble key={i} msg={m} />
              ))}

              {mutation.isPending && (
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    gap: '6px',
                  }}
                >
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      letterSpacing: '0.1em',
                      textTransform: 'uppercase',
                      color: 'var(--muted)',
                    }}
                  >
                    P2P Copilot
                  </span>
                  <div
                    style={{
                      padding: '12px 16px',
                      borderRadius: '18px 18px 18px 4px',
                      background: 'var(--panel-2)',
                      border: '1px solid var(--border)',
                    }}
                  >
                    <TypingDots />
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div
              style={{
                padding: '14px 20px',
                borderTop: '1px solid var(--border)',
                display: 'flex',
                gap: '10px',
                alignItems: 'center',
              }}
            >
              <input
                className="input"
                style={{ flex: 1, borderRadius: '12px', padding: '10px 16px' }}
                placeholder={
                  isReady
                    ? 'Ask about suppliers, transactions, contracts, or risks…'
                    : isBuilding
                    ? 'Index is building — please wait…'
                    : 'Initializing…'
                }
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKey}
                disabled={!isReady || mutation.isPending}
              />
              <button
                className="btn btn-primary"
                style={{ padding: '10px 22px', borderRadius: '12px', minWidth: '80px' }}
                onClick={() => send()}
                disabled={!isReady || mutation.isPending || !input.trim()}
              >
                {mutation.isPending ? '…' : 'Send'}
              </button>
            </div>

            {mutation.isError && (
              <div
                style={{
                  margin: '0 20px 16px',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  background: 'rgba(243,111,124,0.1)',
                  border: '1px solid rgba(243,111,124,0.25)',
                  color: 'var(--red)',
                  fontSize: '13px',
                }}
              >
                Request failed — check the backend connection or try again.
              </div>
            )}
          </div>

          {/* Clear current conversation button */}
          {messages.length > 0 && (
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                className="btn btn-secondary"
                style={{ fontSize: '13px', padding: '7px 16px' }}
                onClick={startNewChat}
              >
                New conversation
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ChatbotPage;
