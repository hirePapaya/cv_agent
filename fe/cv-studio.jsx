/* global React */
const { useState, useRef, useEffect, useCallback } = React;

const API_BASE = window.CV_STUDIO_API_BASE || "http://localhost:8000";
const WS_URL = (window.CV_STUDIO_WS_BASE || API_BASE.replace(/^http/, "ws")) + "/ws/edit-cv";
const WS_RECONNECT_DELAY = 2000;
const WS_RESPONSE_TIMEOUT = 30000;

// ---------- tiny inline icons (Lucide-style, 1.5px) ----------
const Icon = {
  download: (p) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
      strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M12 3v12M7 11l5 4 5-4M5 21h14" />
    </svg>
  ),
  send: (p) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
      strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M5 12h13M12 5l7 7-7 7" />
    </svg>
  ),
};

const Mark = (p) => (
  <svg viewBox="0 0 28 28" xmlns="http://www.w3.org/2000/svg" {...p}>
    <rect width="28" height="28" rx="3" fill="#1A1615" />
    <rect x="8" y="8" width="12" height="12" rx="1.5" fill="#DBFFA5" />
  </svg>
);

// ---------- helpers ----------
function nowStamp() {
  const d = new Date();
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// ---------- apply ops to the CV ----------
function parsePath(path) {
  const tokens = [];
  const re = /([a-zA-Z_]+)|\[(\d+)\]/g;
  let m;
  while ((m = re.exec(path))) {
    tokens.push(m[1] !== undefined ? m[1] : Number(m[2]));
  }
  return tokens;
}
function resolve(obj, tokens) {
  let cur = obj;
  for (const t of tokens) {
    if (cur == null) return undefined;
    cur = cur[t];
  }
  return cur;
}
function applyOps(baseCv, ops) {
  const cv = JSON.parse(JSON.stringify(baseCv));
  let applied = 0;
  for (const op of (ops || [])) {
    try {
      const tokens = parsePath(op.path || "");
      if (op.op === "set") {
        const parent = resolve(cv, tokens.slice(0, -1));
        if (parent == null) continue;
        parent[tokens[tokens.length - 1]] = op.value;
        applied++;
      } else if (op.op === "add") {
        const arr = resolve(cv, tokens);
        if (!Array.isArray(arr)) continue;
        const idx = Number.isInteger(op.index) ? op.index : arr.length;
        arr.splice(idx, 0, op.value);
        applied++;
      } else if (op.op === "remove") {
        const parent = resolve(cv, tokens.slice(0, -1));
        const last = tokens[tokens.length - 1];
        if (Array.isArray(parent) && typeof last === "number") { parent.splice(last, 1); applied++; }
        else if (parent && typeof parent === "object") { delete parent[last]; applied++; }
      } else if (op.op === "reorder") {
        const arr = resolve(cv, tokens);
        if (!Array.isArray(arr) || !Array.isArray(op.order)) continue;
        const next = op.order.map((i) => arr[i]).filter((x) => x !== undefined);
        if (next.length === arr.length) { resolve(cv, tokens.slice(0, -1))[tokens[tokens.length - 1]] = next; applied++; }
      }
    } catch (e) { /* skip bad op */ }
  }
  return { cv, applied };
}

// ---------- log + message renderers ----------
function LogBlock({ lines }) {
  return (
    <div className="log">
      {lines.map((l, i) => (
        <div key={i} className={"log-line" + (l.pending ? " is-pending" : "") + (l.error ? " is-error" : "")}>
          <span className="log-time">{l.time}</span>
          {l.pending ? (
            <span className="typing"><i /><i /><i /></span>
          ) : (
            <span className="log-tick">{l.error ? "×" : "›"}</span>
          )}
          <span className="log-text">{l.text}</span>
        </div>
      ))}
    </div>
  );
}

function Message({ m }) {
  if (m.type === "log") return <LogBlock lines={m.lines} />;
  const role = m.type === "user" ? "You" : "Agent";
  return (
    <div className={"msg msg-" + m.type}>
      <p className="msg-role">{role}</p>
      <div className="msg-body">{m.text}</div>
    </div>
  );
}

const SUGGESTIONS = [
  "Tighten the summary",
  "Make bullets more results-driven",
  "Fix the Fullmind dates",
  "Add a one-line headline",
];

// placeholder shown while the real CV loads from the agent backend
const DEFAULT_CV = {
  name: "",
  title: "",
  summary: "",
  contact: [],
  experience: [],
  education: [],
  skills: [],
};

// ---------- main app ----------
function Studio() {
  const [data, setData] = useState(DEFAULT_CV);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [flash, setFlash] = useState(false);
  const [connected, setConnected] = useState(false);

  const threadRef = useRef(null);
  const taRef = useRef(null);
  const idRef = useRef(1);
  const wsRef = useRef(null);
  const pendingRef = useRef(null);
  const nextId = () => idRef.current++;

  // keep window.RESUME synced so print + any other refs match live state
  useEffect(() => { window.RESUME = data; }, [data]);

  // load the real CV from the agent backend, replacing the defaults
  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/cv`)
      .then((res) => {
        if (!res.ok) throw new Error(`request failed: ${res.status}`);
        return res.json();
      })
      .then((cv) => {
        if (cancelled) return;
        setData(cv);
        setMessages((m) => [...m, { id: nextId(), type: "log", lines: [
          { time: nowStamp(), text: `Loaded ${cv.name} — CV` },
          { time: nowStamp(), text: "Layout: single-column editorial · A4" },
        ] }]);
      })
      .catch(() => {
        if (cancelled) return;
        setMessages((m) => [...m, { id: nextId(), type: "log", lines: [
          { time: nowStamp(), text: "Could not load the CV from the agent.", error: true },
        ] }]);
      });
    return () => { cancelled = true; };
  }, []);

  // open a persistent websocket to the agent, reconnecting on drop
  useEffect(() => {
    let cancelled = false;
    let socket;
    let reconnectTimer;

    const connect = () => {
      socket = new WebSocket(WS_URL);
      wsRef.current = socket;

      socket.onopen = () => { if (!cancelled) setConnected(true); };
      socket.onmessage = (event) => {
        let parsed;
        try {
          parsed = JSON.parse(event.data);
        } catch (e) {
          parsed = null;
        }

        const resolvePending = pendingRef.current;
        if (resolvePending) {
          pendingRef.current = null;
          resolvePending(parsed);
          return;
        }

        // unsolicited message from the agent (e.g. the welcome on connect)
        if (!parsed) return;
        if (Array.isArray(parsed.ops) && parsed.ops.length) {
          setData((prev) => applyOps(prev, parsed.ops).cv);
        }
        const logLines = (Array.isArray(parsed.log) ? parsed.log : [])
          .filter(Boolean)
          .map((t) => ({ time: nowStamp(), text: String(t) }));
        setMessages((m) => {
          const updated = [...m];
          if (logLines.length) updated.push({ id: idRef.current++, type: "log", lines: logLines });
          if (parsed.reply) updated.push({ id: idRef.current++, type: "agent", text: String(parsed.reply) });
          return updated;
        });
      };
      socket.onclose = () => {
        if (cancelled) return;
        setConnected(false);
        if (pendingRef.current) {
          pendingRef.current(null);
          pendingRef.current = null;
        }
        reconnectTimer = setTimeout(connect, WS_RECONNECT_DELAY);
      };
      socket.onerror = () => socket.close();
    };

    connect();
    return () => {
      cancelled = true;
      clearTimeout(reconnectTimer);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  useEffect(() => {
    const el = threadRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, busy]);

  const autosize = () => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 132) + "px";
  };

  const send = useCallback(async (text) => {
    const instruction = (text != null ? text : input).trim();
    if (!instruction || busy) return;
    setInput("");
    if (taRef.current) taRef.current.style.height = "auto";

    const userMsg = { id: nextId(), type: "user", text: instruction };
    const pendingId = nextId();
    const pendingMsg = { id: pendingId, type: "log", lines: [
      { time: nowStamp(), text: "Reading the CV and your request", pending: true },
    ] };
    const history = messages;
    setMessages((m) => [...m, userMsg, pendingMsg]);
    setBusy(true);

    let result = null, errored = false;
    const socket = wsRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      errored = true;
    } else {
      try {
        result = await new Promise((resolve, reject) => {
          pendingRef.current = resolve;
          socket.send(JSON.stringify({
            cv: data,
            history: history
              .filter((m) => m.type === "user" || m.type === "agent")
              .slice(-6)
              .map((m) => ({ role: m.type, text: m.text })),
            instruction,
          }));
          setTimeout(() => {
            if (pendingRef.current === resolve) {
              pendingRef.current = null;
              reject(new Error("timeout"));
            }
          }, WS_RESPONSE_TIMEOUT);
        });
      } catch (e) {
        errored = true;
      }
    }

    setBusy(false);

    if (errored || !result) {
      setMessages((m) => m.map((x) => x.id === pendingId ? {
        ...x, lines: [{ time: nowStamp(), text: "Could not reach the editor — try again.", error: true }],
      } : x));
      return;
    }

    const logLines = (Array.isArray(result.log) ? result.log : [])
      .filter(Boolean)
      .map((t) => ({ time: nowStamp(), text: String(t) }));

    let nextCv = data, applied = 0;
    if (Array.isArray(result.ops) && result.ops.length) {
      const r = applyOps(data, result.ops);
      nextCv = r.cv; applied = r.applied;
    }
    const changed = applied > 0 && JSON.stringify(nextCv) !== JSON.stringify(data);
    if (changed) {
      setData(nextCv);
      setFlash(true);
      setTimeout(() => setFlash(false), 750);
    }
    if (logLines.length === 0) {
      logLines.push({ time: nowStamp(), text: changed ? "Updated the CV" : "No changes made" });
    }

    setMessages((m) => {
      const updated = m.map((x) => x.id === pendingId ? { ...x, lines: logLines } : x);
      if (result.reply) updated.push({ id: nextId(), type: "agent", text: String(result.reply) });
      return updated;
    });
  }, [input, busy, messages, data]);

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="studio">
      {/* LEFT — chat / agent */}
      <aside className="chat">
        <div className="chat-head">
          <div className="chat-brand">
            <Mark className="chat-mark" />
            <div className="chat-titles">
              <p className="chat-title">CV Studio</p>
              <p className="chat-sub">Rafael Campo</p>
            </div>
          </div>
          <span className={"chat-status" + (connected ? " is-connected" : "")} title={connected ? "Connected to agent" : "Connecting to agent…"}>
            <span className="dot" /> {connected ? "Connected" : "Connecting…"}
          </span>
          <button className="btn-export" onClick={() => window.print()} title="Export the CV as a PDF">
            {Icon.download()} Export PDF
          </button>
        </div>

        <div className="thread" ref={threadRef}>
          {messages.map((m) => <Message key={m.id} m={m} />)}
        </div>

        <div className="composer">
          <div className="composer-suggest">
            {SUGGESTIONS.map((s) => (
              <button key={s} className="chip" disabled={busy} onClick={() => send(s)}>{s}</button>
            ))}
          </div>
          <div className="composer-row">
            <textarea
              ref={taRef}
              rows={1}
              value={input}
              placeholder="Ask the agent to edit the CV…"
              onChange={(e) => { setInput(e.target.value); autosize(); }}
              onKeyDown={onKeyDown}
            />
            <button className="btn-send" disabled={busy || !input.trim()} onClick={() => send()} title="Send">
              {Icon.send()}
            </button>
          </div>
        </div>
      </aside>

      {/* RIGHT — preview canvas */}
      <CanvasPane data={data} flash={flash} />
    </div>
  );
}

function CanvasPane({ data, flash }) {
  const scrollRef = useRef(null);
  const scaleRef = useRef(null);
  const [zoom, setZoom] = useState(1);

  useEffect(() => {
    const measure = () => {
      const el = scrollRef.current;
      if (!el) return;
      const avail = el.clientWidth - 64; // horizontal padding
      const z = Math.min(1, Math.max(0.4, avail / 794));
      setZoom(z);
    };
    measure();
    const ro = new ResizeObserver(measure);
    if (scrollRef.current) ro.observe(scrollRef.current);
    return () => ro.disconnect();
  }, []);

  return (
    <main className="canvas">
      <div className="canvas-bar">
        <span className="canvas-bar-label">Preview · A4</span>
        <div className="canvas-zoom">
          <span className="canvas-saved"><span className="dot" /> Synced</span>
          <span>{Math.round(zoom * 100)}%</span>
        </div>
      </div>
      <div className="canvas-scroll" ref={scrollRef}>
        <div
          className="sheet-scale"
          ref={scaleRef}
          style={{ transform: `scale(${zoom})`, height: 1123 * zoom }}
        >
          <div className={"sheet-wrap" + (flash ? " is-updating" : "")}>
            <ResumeA data={data} />
          </div>
        </div>
      </div>
    </main>
  );
}

Object.assign(window, { Studio });
