import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";

// --- Small helpers ---
function classNames(...args: (string | false | undefined)[]) {
  return args.filter(Boolean).join(" ");
}

type Source = { id: number; title: string; source: string; score?: number; snippet?: string };
type TurnOut = {
  intent: string;
  text: string;
  sources: Source[];
  tool_result?: any;
  metrics?: any;
};

type Message = {
  role: "user" | "agent";
  data: TurnOut | { text: string };
};

function IntentChip({ intent }: { intent: string }) {
  const intentColor: Record<string, string> = {
    faq: "#3b82f6",
    order_status: "#16a34a",
    create_ticket: "#8b5cf6",
    handoff: "#f59e0b",
    out_of_scope: "#ef4444",
    refusal: "#ef4444",
    error: "#ef4444",
  };
  const color = intentColor[intent] || "#334155";
  return (
    <span
      style={{
        background: `${color}20`,
        color,
        border: `1px solid ${color}40`,
        padding: "2px 8px",
        borderRadius: 999,
        fontSize: 12,
        fontWeight: 600,
      }}
      title={`intent: ${intent}`}
    >
      {intent}
    </span>
  );
}

function MetricChip({ children }: { children: React.ReactNode }) {
  return (
    <span
      style={{
        background: "#0f172a0d",
        border: "1px solid #0f172a1a",
        padding: "2px 8px",
        borderRadius: 999,
        fontSize: 12,
        color: "#334155",
      }}
    >
      {children}
    </span>
  );
}

function SourceCard({ s }: { s: Source }) {
  const [open, setOpen] = useState(true);
  return (
    <div
      style={{
        border: "1px solid #e2e8f0",
        borderRadius: 12,
        padding: 12,
        background: "#f8fafc",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <strong style={{ fontSize: 13 }}>[{s.id}] {s.title}</strong>
        <span style={{ fontSize: 12, opacity: 0.7 }}>( {s.source} )</span>
        <div style={{ flex: 1 }} />
        <button
          onClick={() => setOpen((v) => !v)}
          style={{
            border: "1px solid #cbd5e1",
            background: "white",
            borderRadius: 8,
            padding: "2px 8px",
            fontSize: 12,
          }}
        >
          {open ? "Hide" : "Show"}
        </button>
      </div>
      {open && s.snippet && (
        <pre
          style={{
            marginTop: 8,
            whiteSpace: "pre-wrap",
            fontSize: 12,
            lineHeight: 1.5,
            color: "#334155",
          }}
        >
          {s.snippet}
        </pre>
      )}
    </div>
  );
}

function useStreaming(wsUrl: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [streamText, setStreamText] = useState("");
  useEffect(() => {
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (ev) => setStreamText((t) => t + String(ev.data || ""));
    return () => ws.close();
  }, [wsUrl]);
  const send = (msg: string) => {
    try {
      wsRef.current?.send(msg);
      setStreamText("");
    } catch {}
  };
  return { connected, streamText, send };
}

export default function App() {
  const API = (import.meta.env.VITE_API_BASE as string) || "http://localhost:8000";
  const WS = (import.meta.env.VITE_WS_BASE as string) || "ws://localhost:8000/ws/chat";

  const [sessionId] = useState("demo");
  const [input, setInput] = useState("");
  const [msgs, setMsgs] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const { connected, streamText, send } = useStreaming(WS);

  const ask = async (message: string) => {
    const user: Message = { role: "user", data: { text: message } };
    setMsgs((m) => [...m, user]);
    setLoading(true);
    try {
      const r = await axios.post<TurnOut>(`${API}/answer`, { session_id: sessionId, message });
      const agent: Message = { role: "agent", data: r.data };
      setMsgs((m) => [...m, agent]);
    } catch (e: any) {
      const err: Message = {
        role: "agent",
        data: { intent: "error", text: `Error: ${e?.message ?? "request failed"}`, sources: [] },
      } as any;
      setMsgs((m) => [...m, err]);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const msg = input.trim();
    if (!msg) return;
    if (connected) send(msg);
    ask(msg);
    setInput("");
  };

  const lastAgent = useMemo(() => {
    for (let i = msgs.length - 1; i >= 0; i--) {
      if (msgs[i].role === "agent") return msgs[i].data as TurnOut;
    }
    return null;
  }, [msgs]);

  return (
    <div style={{ minHeight: "100vh", background: "#f1f5f9" }}>
      {/* Inline styles for quick elegance without Tailwind setup */}
      <style>{`
        .wrap { max-width: 960px; margin: 0 auto; padding: 24px; }
        .card { background: white; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px rgba(0,0,0,0.04); border-radius: 16px; }
        .row { display: flex; gap: 12px; align-items: center; }
        .header { position: sticky; top: 0; z-index: 10; backdrop-filter: blur(8px); background: rgba(241,245,249,0.7); border-bottom: 1px solid #e2e8f0; }
        .title { font-size: 18px; font-weight: 700; color: #0f172a; }
        .subtitle { font-size: 13px; color: #475569; }
        .composer { position: sticky; bottom: 0; padding: 16px; background: linear-gradient(180deg, rgba(241,245,249,0), rgba(241,245,249,1) 30%); }
        .input { flex: 1; border: 1px solid #cbd5e1; border-radius: 12px; padding: 12px 14px; font-size: 14px; outline: none; }
        .input:focus { border-color: #94a3b8; box-shadow: 0 0 0 4px rgba(148,163,184,0.2);} 
        .btn { background: #0f172a; color: white; border-radius: 12px; padding: 10px 16px; font-weight: 600; border: none; }
        .btn:disabled { opacity: .5; }
        .bubble { max-width: 80%; padding: 12px 14px; border-radius: 16px; line-height: 1.6; font-size: 14px; }
        .bubble-user { background: #0f172a; color: white; border-top-right-radius: 4px; }
        .bubble-agent { background: white; border: 1px solid #e2e8f0; border-top-left-radius: 4px; }
        .stack { display: grid; gap: 16px; }
        .sources { display: grid; gap: 8px; }
        .meta { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
        .footer { color: #475569; font-size: 12px; }
      `}</style>

      {/* Header */}
      <div className="header">
        <div className="wrap" style={{ padding: 16 }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div>
              <div className="title">Customer Service Agent</div>
              <div className="subtitle">RAG answers · Tool calls · Guardrails · Streaming</div>
            </div>
            <div className="row" style={{ gap: 8 }}>
              <a href={`${API}/metrics`} target="_blank" rel="noreferrer" className="subtitle" style={{ textDecoration: "underline" }}>View Metrics</a>
              <span className="subtitle">WS: {connected ? "connected" : "disconnected"}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main body */}
      <div className="wrap" style={{ paddingTop: 24, paddingBottom: 96 }}>
        <div className="stack">
          {msgs.length === 0 && (
            <div className="card" style={{ padding: 16 }}>
              <div className="subtitle">Try:</div>
              <ul style={{ margin: 0, paddingLeft: 18, color: "#334155", fontSize: 14 }}>
                <li>“What is your return policy?”</li>
                <li>“Status for order A123?”</li>
                <li>“Open a ticket, my package arrived damaged.”</li>
              </ul>
            </div>
          )}

          {msgs.map((m, i) => (
            <div key={i} className="row" style={{ justifyContent: m.role === "user" ? "flex-end" : "flex-start" }}>
              <div className={classNames("bubble", m.role === "user" ? "bubble-user" : "bubble-agent")}
                   style={{ width: "fit-content" }}>
                {m.role === "agent" ? (
                  <div style={{ display: "grid", gap: 8 }}>
                    <div style={{ whiteSpace: "pre-wrap" }}>{(m.data as TurnOut).text}</div>
                    {/* meta chips */}
                    <div className="meta">
                      <IntentChip intent={(m.data as TurnOut).intent} />
                      {typeof (m.data as TurnOut)?.metrics?.latency_ms === "number" && (
                        <MetricChip>{Math.round((m.data as TurnOut).metrics.latency_ms)} ms</MetricChip>
                      )}
                      {typeof (m.data as TurnOut)?.metrics?.confidence === "number" && (
                        <MetricChip>conf {Math.round((m.data as TurnOut).metrics.confidence * 100)}%</MetricChip>
                      )}
                    </div>
                    {/* sources */}
                    {!!(m.data as TurnOut).sources?.length && (
                      <div className="sources">
                        {(m.data as TurnOut).sources.map((s) => (
                          <SourceCard key={s.id} s={s} />
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ whiteSpace: "pre-wrap" }}>{(m.data as any).text}</div>
                )}
              </div>
            </div>
          ))}

          {/* Streaming line (subtle) */}
          {connected && streamText && (
            <div className="subtitle">typing: <span style={{ color: "#0f172a" }}>{streamText}</span></div>
          )}
        </div>
      </div>

      {/* Composer */}
      <div className="composer">
        <div className="wrap">
          <form className="row" onSubmit={onSubmit}>
            <input
              className="input"
              placeholder="Ask about returns, shipping, or an order (e.g., Status for order A123?)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <button className="btn" disabled={loading}>{loading ? "Sending…" : "Send"}</button>
          </form>
          <div className="footer" style={{ marginTop: 8 }}>
            Session: <code>{sessionId}</code>
          </div>
        </div>
      </div>
    </div>
  );
}

