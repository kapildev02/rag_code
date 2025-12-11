import { useState } from "react";
interface ChatMessageProps {
  content: string | object;
  sources: Array<{ file: string; content?: string; category?: string }>;
  role: "user" | "assistant";
  timestamp?: string;
}
export const ChatMessage = ({ content, sources, role, timestamp }: ChatMessageProps) => {
  const [selectedSource, setSelectedSource] = useState<
    { file: string; content?: string; category?: string } | null
  >(null);
  if (!content || (role !== "user" && role !== "assistant")) return null;
  const isUser = role === "user";
  const bubbleStyle = isUser
    ? "bg-gray-100 text-gray-800 rounded-t-2xl rounded-bl-2xl ml-auto"
    : "bg-gray-100 text-gray-800 rounded-t-2xl rounded-br-2xl";
  const isValidTimestamp = timestamp && !isNaN(Date.parse(timestamp));
  // prefer structured server response: { answer: "...", status?: "...", sources?: [...] }
  const messageText =
    typeof content === "string"
      ? content
      : content && (content as any).answer
      ? (content as any).answer
      : JSON.stringify(content, null, 2);

  // treat server "no_context" as non-final UI state or show guidance
  const isNoContext =
    messageText === "No relevant context found." ||
    (content && (content as any).status === "no_context");

  // Only show typing animation when a specific isTyping flag is present (or id === null while streaming)
  const showTyping = !isUser && (content as any)?.isTyping === true;

  return (
    <div className="px-4 py-2">
      <div className={`max-w-max ${isUser ? "ml-auto" : "mr-auto"}`}>
        <div className={`p-3 ${bubbleStyle}`}>
          <div
            className={`text-sm md:text-base whitespace-pre-wrap break-words ${showTyping ? "typing-animation" : ""}`}
          >
            {isNoContext ? "No context available — try broadening your query or re-ingesting documents." : messageText}
          </div>
        </div>
        {/* Sources Section */}
        {sources && sources.length > 0 && (
          <div className="text-xs text-gray-400 mt-1">
            <span>Sources:</span>
            <ul className="list-disc list-inside">
              {sources.map((source, index) => (
                <li key={index}>
                  <button
                    onClick={() => setSelectedSource(source)}
                    className="text-gray-300 hover:underline"
                  >
                    {source.file}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
        {/* Timestamp */}
        {isValidTimestamp && (
          <div
            className={`text-xs text-gray-400 mt-1 ${
              isUser ? "text-right" : "text-left"
            }`}
          >
            {new Date(timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>
      {/* Modal for showing full source */}
{selectedSource && (
  <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
    <div className="bg-white text-black rounded-lg p-4 max-w-2xl w-full max-h-[80vh] flex flex-col">
      {/* Header */}
      <h2 className="text-gray-600 font-bold mb-2">{selectedSource.file}</h2>
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto pr-2">
        {selectedSource.content && (
          <p className="text-gray-800 mb-2 whitespace-pre-wrap break-words">
            {selectedSource.content}
          </p>
        )}
        {selectedSource.category && (
          <p className="text-sm text-gray-800">
            Category: {selectedSource.category}
          </p>
        )}
      </div>
      {/* Footer with Close button */}
      <div className="mt-3 text-right">
        <button
          onClick={() => setSelectedSource(null)}
          className="px-3 py-1 bg-gray-700 text-white rounded hover:bg-gray-900"
        >
          Close
        </button>
      </div>
    </div>
  </div>
)}
    </div>
  );
}