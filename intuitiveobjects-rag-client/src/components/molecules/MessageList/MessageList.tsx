import { ChatMessage } from "@/components/molecules/ChatMessage/ChatMessage";
import { Loading } from "@/components/atoms/Loading/Loading";

interface Message {
  id: string;
  content: string;
  sources: Array<{ file: string; content?: string; category?: string }>;
  role: "user" | "assistant";
  // Make timestamp optional because backend uses created_at etc.
  timestamp?: string;
  // keep other possible server timestamp fields for typing
  created_at?: string;
  createdAt?: string;
  updated_at?: string;
}

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
  messagesEndRef?: React.RefObject<HTMLDivElement>;
}

export const MessageList = ({
  messages,
  isLoading,
  messagesEndRef,
}: MessageListProps) => {
  return (
    <div>
      {messages.map((message) => {
        // Normalize timestamp from multiple possible server fields
        const normalizedTimestamp =
          message.timestamp ||
          message.created_at ||
          (message as any).createdAt ||
          message.updated_at ||
          "";

        return (
          <ChatMessage
            key={message.id}
            content={message.content}
            sources={message.sources || []}
            role={message.role}
            timestamp={normalizedTimestamp}
          />
        );
      })}
      {isLoading && <Loading />}
      {messagesEndRef && <div ref={messagesEndRef} />}
    </div>
  );
};