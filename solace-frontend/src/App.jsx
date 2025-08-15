import { useState, useEffect, useRef } from "react";
import Typed from "typed.js";
import { FiSend } from "react-icons/fi";

/* Small typing-dots component */
const TypingDots = () => (
  <div className="flex gap-1 items-center">
    <span className="w-2 h-2 rounded-full bg-gray-500 dark:bg-gray-300 animate-bounce" style={{ animationDelay: "0.05s" }} />
    <span className="w-2 h-2 rounded-full bg-gray-500 dark:bg-gray-300 animate-bounce" style={{ animationDelay: "0.15s" }} />
    <span className="w-2 h-2 rounded-full bg-gray-500 dark:bg-gray-300 animate-bounce" style={{ animationDelay: "0.25s" }} />
  </div>
);

/* Message component: typed.js for solace replies, simple text for user */
const Message = ({ sender, text, isTyping, userInputForReply, onRetry, retryDisabled }) => {
  const elRef = useRef(null);
  const typedRef = useRef(null);

  useEffect(() => {
    if (sender === "solace" && !isTyping && elRef.current && text) {
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
        <div className={`flex items-end gap-3 max-w-xs p-3 rounded-2xl text-sm shadow-md break-words
            ${sender === "user" ? "bg-blue-500 text-white" : "bg-gray-200 dark:bg-gray-700 dark:text-white text-gray-900"}`}>
          {sender === "solace" && <span className="text-2xl">🌿</span>}

        <div className="min-w-0">
          {sender === "solace" ? (
            isTyping ? <TypingDots /> : <div ref={elRef} />
          ) : (
            <div>{text}</div>
          )}
        </div>

        {sender === "user" && <span className="text-2xl">🧍‍♀</span>}
      </div>

      {/* Retry button for Solace messages */}
      {sender === "solace" && !isTyping && userInputForReply && (
        <button
          onClick={onRetry}
          disabled={retryDisabled}
          className="ml-2 self-end p-1 rounded-full bg-yellow-300 hover:bg-yellow-400 disabled:opacity-50 text-yellow-900"
          aria-label="Retry response"
          title="Retry"
        >
         ↻
        </button>
      )}
    </div>
  );
};

export default function App() {
  const [messages, setMessages] = useState([
    { id: `m-${Date.now()}-1`, sender: "solace", text: "Hi I am solace 🌸...", userInputForReply: null },
    { id: `m-${Date.now()}-2`, sender: "solace", text: "How are you feeling today?", userInputForReply: null }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [retryingMessageId, setRetryingMessageId] = useState(null);

  const audioRef = useRef(null);
  const bottomRef = useRef(null);
  const scrollContainerRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isTyping]);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  const genId = () => `m-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

  const stripEmotionBracket = (s) => {
    if (!s) return s;
    return s.replace(/\(Detected emotion:.*?\)/gi, "").trim();
  };

  // Main function to fetch a reply from backend for given user input and update messages
  const fetchReply = async (userText, replaceMessageId = null) => {
    setIsTyping(true);
    try {
      const resp = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "default",
          text: userText
        }),
      });
      const data = await resp.json();
      const raw = (data && data.response) ? String(data.response) : "Something went wrong. 🌧";
      const cleaned = stripEmotionBracket(raw);

      if (replaceMessageId) {
        // Replace the old Solace message text with the new reply
        setMessages((m) =>
          m.map((msg) =>
            msg.id === replaceMessageId ? { ...msg, text: cleaned } : msg
          )
        );
      } else {
        // Append new Solace message with userInputForReply linked
        setMessages((m) => [
          ...m,
          { id: genId(), sender: "solace", text: cleaned, userInputForReply: userText },
        ]);
      }
    } catch (err) {
      console.error("Chat API error:", err);
      if (replaceMessageId) {
        setMessages((m) =>
          m.map((msg) =>
            msg.id === replaceMessageId ? { ...msg, text: "Something went wrong. 🌧" } : msg
          )
        );
      } else {
        setMessages((m) => [
          ...m,
          { id: genId(), sender: "solace", text: "Something went wrong. 🌧", userInputForReply: userText },
        ]);
      }
    } finally {
      setIsTyping(false);
      setRetryingMessageId(null);
    }
  };

  const sendMessage = async () => {
    const textToSend = input.trim();
    if (!textToSend) return;

    const sendSound = new Audio("/send.mp3");
    sendSound.play().catch((err) => console.warn("Audio play error:", err));

    const userMsg = { id: genId(), sender: "user", text: textToSend };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    audioRef.current?.play();

    // Fetch reply for this input
    fetchReply(textToSend);
  };

  const handleRetry = (messageId) => {
  const msgToRetry = messages.find((m) => m.id === messageId);
  if (!msgToRetry || !msgToRetry.userInputForReply) return;

  setRetryingMessageId(messageId); // <-- set here before fetch
  fetchReply(msgToRetry.userInputForReply, messageId);
};

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 to-white dark:from-gray-900 dark:to-black transition-colors duration-300 flex flex-col items-center">
      <button
        onClick={() => setDarkMode(!darkMode)}
        className="fixed top-4 right-4 text-2xl z-20 p-2 rounded"
        aria-label="Toggle dark mode"
      >
        {darkMode ? "🌞" : "🌙"}
      </button>
      <div className="fixed top-4 left-1/2 transform -translate-x-1/2 flex items-center gap-2 z-10 px-4 py-2 rounded-full shadow-lg backdrop-blur-md bg-white/30 dark:bg-gray-800/30 border border-white/20 dark:border-gray-700/20">
  <img src="solacee.jpg" alt="Solace AI logo" className="w-8 h-8 rounded-full" />
  <span className="font-bold text-gray-900 dark:text-white text-lg">Solace AI</span>
</div>
      <div
        className="w-full max-w-md flex flex-col space-y-2 flex-grow overflow-y-auto px-4 pt-20 pb-28"
        ref={scrollContainerRef}
      >
       {messages.map((msg) => (
  <Message
    key={msg.id}
    sender={msg.sender}
    text={msg.text}
    userInputForReply={msg.userInputForReply}  // <-- Add this line
    isTyping={msg.id === retryingMessageId}
    onRetry={msg.sender === "solace" ? () => handleRetry(msg.id) : undefined}
    retryDisabled={retryingMessageId === msg.id || isTyping}
  />
))}
        {isTyping && !retryingMessageId && (
          <Message key="typing" sender="solace" text="" isTyping={true} />
        )}
        <div ref={bottomRef} />
      </div>

      <div className="fixed bottom-4 left-0 right-0 px-4 max-w-md mx-auto">
        <div className="flex">
          <textarea
            rows={1}
            className="flex-grow p-3 border dark:border-gray-700 rounded-l-2xl outline-none dark:bg-gray-800 dark:text-white resize-none"
            placeholder="I’m here to hear you..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            onClick={sendMessage}
            className="bg-green-500 text-white px-4 rounded-r-2xl hover:bg-green-600 flex items-center justify-center"
            aria-label="Send"
          >
            <FiSend className="text-xl" />
          </button>
        </div>
      </div>

      <audio ref={audioRef} src="/send.mp3" preload="auto" />
    </div>
  );
}