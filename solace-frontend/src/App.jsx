import { useState, useEffect, useRef } from "react";
import Typed from "typed.js";
import { FiSend, FiUsers, FiMoreHorizontal, FiDatabase, FiVolume2 } from "react-icons/fi";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

/* Typing dots component */
const TypingDots = () => (
  <div className="flex gap-1 items-center">
    <span className="w-2 h-2 rounded-full bg-gray-500 dark:bg-gray-300 animate-bounce" style={{ animationDelay: "0.05s" }} />
    <span className="w-2 h-2 rounded-full bg-gray-500 dark:bg-gray-300 animate-bounce" style={{ animationDelay: "0.15s" }} />
    <span className="w-2 h-2 rounded-full bg-gray-500 dark:bg-gray-300 animate-bounce" style={{ animationDelay: "0.25s" }} />
  </div>
);

/* Message bubble */
const Message = ({ sender, text, isTyping, userInputForReply, onRetry, retryDisabled }) => {
  const elRef = useRef(null);
  const typedRef = useRef(null);

  useEffect(() => {
    if (sender === "Snugsy" && !isTyping && elRef.current && text) {
      elRef.current.innerHTML = "";
      typedRef.current = new Typed(elRef.current, {
        strings: [text],
        typeSpeed: 28,
        showCursor: false,
      });
    }
    return () => typedRef.current?.destroy();
  }, [sender, text, isTyping]);

  return (
    <div className={`flex ${sender === "user" ? "justify-end" : "justify-start"} my-2`}>
      <div
        className={`flex items-end gap-3 max-w-xl p-3 rounded-2xl text-sm shadow-md break-words
          ${sender === "user" ? "bg-blue-500 text-white" : "bg-gray-200 dark:bg-gray-700 dark:text-white text-gray-900"}`}>
        
        {sender === "Snugsy" && <span className="text-2xl">🌿</span>}
        
        <div className="min-w-0">
          {sender === "Snugsy"
            ? isTyping
              ? <TypingDots />
              : <div ref={elRef} />
            : <div>{text}</div>}
        </div>

        {sender === "user" && <span className="text-2xl">🧍‍♀</span>}
      </div>

      {/* Retry button */}
      {sender === "Snugsy" && !isTyping && userInputForReply && (
        <button
          onClick={onRetry}
          disabled={retryDisabled}
          className="ml-2 self-end p-1 rounded-full bg-yellow-300 hover:bg-yellow-400 disabled:opacity-50 text-yellow-900"
        >
          ↻
        </button>
      )}
    </div>
  );
};

export default function App() {

  const initialMessages = [
    { id: `m-${Date.now()}-1`, sender: "Snugsy", text: "Hi I am Snugsy 🌸... I’m here to hear you.", userInputForReply: null },
    { id: `m-${Date.now()}-2`, sender: "Snugsy", text: "How are you feeling today?", userInputForReply: null }
  ];

  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [retryingMessageId, setRetryingMessageId] = useState(null);

  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  const genId = () => `m-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

  /* ---------------- New Chat (sidebar) ---------------- */
  const newChat = () => {
    if (!confirm("Start a new chat? This will clear your current conversation.")) return;

    setMessages([
      { id: genId(), sender: "Snugsy", text: "Hi I am Snugsy 🌸... I’m here to hear you.", userInputForReply: null },
      { id: genId(), sender: "Snugsy", text: "How are you feeling today?", userInputForReply: null }
    ]);
    setInput("");
  };

  /* ---------------- Send message ---------------- */
  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = {
      id: genId(),
      sender: "user",
      text: input.trim(),
      userInputForReply: null,
    };

    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "user-123",
          text: userMsg.text
        }),
      });

      const data = await res.json();

      const reply = {
        id: genId(),
        sender: "Snugsy",
        text: data.response || "Sorry, I couldn't reply.",
        userInputForReply: userMsg.text,
      };

      setMessages(prev => [...prev, reply]);

    } catch (err) {
      console.error("Error:", err);
      setMessages(prev => [...prev, {
        id: genId(),
        sender: "Snugsy",
        text: "⚠ Oops, something went wrong.",
        userInputForReply: userMsg.text,
      }]);
    }

    setIsTyping(false);
  };

  /* ---------------- Retry ---------------- */
  const handleRetry = async (messageId) => {
    const msg = messages.find(m => m.id === messageId);
    if (!msg) return;

    setRetryingMessageId(messageId);
    const resendText = msg.userInputForReply;

    setIsTyping(true);
    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: "user-123", text: resendText }),
      });

      const data = await res.json();
      const reply = {
        id: genId(),
        sender: "Snugsy",
        text: data.response || "Sorry, no reply.",
        userInputForReply: resendText,
      };

      setMessages(prev => [...prev, reply]);

    } catch (err) {
      console.error(err);
    }

    setRetryingMessageId(null);
    setIsTyping(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  /* ---------------- Sidebar placeholders ---------------- */
  const openMemory = () => alert("Memory (coming soon)");
  const toggleSound = () => alert("Sound toggled");

  return (
    <div className="min-h-screen flex bg-gradient-to-b from-green-50 to-white dark:from-gray-900 dark:to-black transition-colors">

      {/* Center chat column */}
      <div className="flex-grow flex justify-center">
        <div className="w-full max-w-3xl flex flex-col relative">

          {/* Header */}
          <div className="fixed top-0 left-0 right-0 z-30">
            <div className="max-w-3xl mx-auto px-4 h-16 flex items-center gap-3 shadow-lg bg-white/30 dark:bg-gray-800/30 backdrop-blur-md">
              <img src="snugsyy.jpg" alt="Snugsy" className="w-10 h-10 rounded-full" />
              <span className="font-bold text-gray-900 dark:text-white text-lg">Snugsy AI</span>

              <div className="ml-auto flex items-center gap-2">
                <button
                  onClick={() => setShowSettings(true)}
                  className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <FiMoreHorizontal className="text-xl" />
                </button>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex flex-col flex-grow overflow-y-auto pt-20 pb-28 px-4">
            {messages.map(msg => (
              <Message
                key={msg.id}
                sender={msg.sender}
                text={msg.text}
                userInputForReply={msg.userInputForReply}
                isTyping={msg.id === retryingMessageId}
                onRetry={msg.sender === "Snugsy" ? () => handleRetry(msg.id) : undefined}
                retryDisabled={retryingMessageId === msg.id || isTyping}
              />
            ))}

            {isTyping && <Message key="typing" sender="Snugsy" isTyping={true} />}

            <div ref={bottomRef} />
          </div>

          {/* Input box */}
          <div className="fixed bottom-0 left-0 right-0 flex justify-center z-30">
            <div className="w-full max-w-3xl px-4 pb-4">
              <div className="flex">
                <textarea
                  rows={1}
                  className="flex-grow p-3 border dark:border-gray-700 rounded-l-2xl outline-none dark:bg-gray-800 dark:text-white resize-none"
                  placeholder="I’m here to hear you..."
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={isTyping}
                />

                <button
                  onClick={sendMessage}
                  disabled={isTyping || !input.trim()}
                  className="bg-green-500 text-white px-4 rounded-r-2xl hover:bg-green-600 disabled:opacity-50"
                >
                  <FiSend className="text-xl" />
                </button>
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* ⭐ RIGHT SIDEBAR (with New Chat added here) */}
      <aside className="fixed top-16 right-0 bottom-0 w-20 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-700 flex flex-col justify-between items-center py-4 z-40">

        <div className="flex flex-col gap-6">

          {/* NEW CHAT BUTTON HERE */}
          <button
            onClick={newChat}
            className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full"
            title="New Chat"
          >
            🆕
          </button>

          <button className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full">
            💬
          </button>

          <button className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full">
            <FiUsers className="text-xl" />
          </button>

          <button onClick={openMemory} className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full">
            <FiDatabase className="text-xl" />
          </button>

        </div>

        <div className="flex flex-col gap-4 items-center">
          <button onClick={toggleSound} className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full">
            <FiVolume2 className="text-xl" />
          </button>

          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full"
          >
            <FiMoreHorizontal className="text-xl" />
          </button>
        </div>

      </aside>

      {/* Settings Panel */}
      {showSettings && (
        <div className={`fixed top-0 right-20 h-full w-72 bg-white dark:bg-gray-800 shadow-xl p-4 transition-transform duration-300 ${showSettings ? "translate-x-0" : "translate-x-full"}`}>
          <h2 className="text-lg font-bold mb-4 text-gray-900 dark:text-white">Settings</h2>

          <div className="flex items-center justify-between py-2">
            <span className="text-gray-800 dark:text-gray-200">Dark Mode</span>
            <button onClick={() => setDarkMode(!darkMode)} className="p-2 rounded-full bg-gray-200 dark:bg-gray-700">
              {darkMode ? "🌞" : "🌙"}
            </button>
          </div>

          <div className="mt-4 flex flex-col gap-3">
            <button className="text-left py-2 px-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
              Profile
            </button>
            <button className="text-left py-2 px-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
              Notifications
            </button>
          </div>
        </div>
      )}

    </div>
  );
}