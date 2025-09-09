// interface ChatMessageProps {
//   content: string;
//   role: "user" | "assistant";
//   timestamp?: string;
// }

// export const ChatMessage = ({ content, role, timestamp }: ChatMessageProps) => {
//   const isUser = role === "user";
//   const bubbleStyle = isUser
//     ? "bg-gray-300 text-gray-800 rounded-t-2xl rounded-bl-2xl ml-auto"
//     : "bg-gray-400 text-gray-800 rounded-t-2xl rounded-br-2xl";

//   return (
//     <div className="px-4 py-2">
//       <div className={`max-w-max ${isUser ? "ml-auto" : "mr-auto"}`}>
//         <div className={`p-3 ${bubbleStyle}`}>
//           <div
//             className={`text-sm md:text-base whitespace-pre-wrap break-words ${
//               !isUser && "typing-animation"
//             }`}
//           >
//             {content}
//           </div>
//         </div>

//         {timestamp && (
//           <div
//             className={`text-xs text-gray-400 mt-1 ${
//               isUser ? "text-right" : "text-left"
//             }`}
//           >
//             {new Date(timestamp).toLocaleTimeString()}
//           </div>
//         )}
//       </div>
//     </div>
//   );
// };

interface ChatMessageProps {
  content: string | object;
  sources: Array<{ file: string; }>;
  role: "user" | "assistant";
  timestamp?: string;
}

export const ChatMessage = ({ content, sources, role, timestamp }: ChatMessageProps) => {
  if (!content || (role !== "user" && role !== "assistant")) return null;

  const isUser = role === "user";
  const bubbleStyle = isUser
    ? "bg-gray-300 text-gray-800 rounded-t-2xl rounded-bl-2xl ml-auto"
    : "bg-gray-400 text-gray-800 rounded-t-2xl rounded-br-2xl";

  const isValidTimestamp = timestamp && !isNaN(Date.parse(timestamp));

  const messageText =
    typeof content === "string" ? content : JSON.stringify(content, null, 2); // format JSON nicely

  return (
    <div className="px-4 py-2">
      <div className={`max-w-max ${isUser ? "ml-auto" : "mr-auto"}`}>
        <div className={`p-3 ${bubbleStyle}`}>
          <div
            className={`text-sm md:text-base whitespace-pre-wrap break-words ${
              !isUser && "typing-animation"
            }`}
          >
            {messageText}
          </div>
        </div>
        {sources && sources.length > 0 && (
          <div className="text-xs text-gray-400 mt-1">
            Sources:
            <ul className="list-disc list-inside">
              {sources.map((source, index) => (
                <li key={index}>{source.file}</li>
              ))}
            </ul>
          </div>
        )}
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
    </div>
  );
};
