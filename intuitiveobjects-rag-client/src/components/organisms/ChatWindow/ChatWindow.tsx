import { MessageList } from "@/components/molecules/MessageList/MessageList";
import { ChatInput } from "@/components/molecules/ChatInput/ChatInput";
import { EmptyState } from "@/components/molecules/EmptyState/EmptyState";
import { Container } from "@/components/atoms/Container/Container";
import { useEffect, useRef } from "react";
import { Loader } from "@/components/atoms/Loading/Loading";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { useParams } from "react-router-dom";
import { getChatMessagesApi } from "@/services/chatApis";
import { motion } from "framer-motion";

interface ChatWindowProps {
  isLoading?: boolean;
  onload?: boolean;
}

export const ChatWindow = ({ isLoading, onload }: ChatWindowProps) => {
  const messages = useAppSelector((state) => state.chat.messages);
  const history = useAppSelector((state) => state.chat.history);

  const dispatch = useAppDispatch();
  const { chatId } = useParams();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (chatId) {
      dispatch(getChatMessagesApi(chatId));
    }
  }, [chatId, dispatch]);

  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom();
    }
  }, [messages, isLoading]);

  return (
    // overall ChatWindow: full screen aware, shifts for large sidebar
    <div
      className="flex flex-col h-screen lg:ml-64 relative z-0 bg-gradient-to-b from-slate-50 via-slate-50 to-slate-100 dark:from-slate-900 dark:via-slate-900 dark:to-slate-800"
      style={{ minHeight: "100vh" }}
    >
      {/* Internal sticky header (combines Header features into chat view) */}
      <header className="sticky top-16 z-30 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 backdrop-blur-md bg-opacity-80 dark:bg-opacity-80">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
          {/* ...existing header content... */}
        </div>
      </header>

      {/* Message Scroll Area */}
      <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 px-4 pb-32 pt-6">
        {onload ? (
          <Loader className="h-full" />
        ) : !isLoading && messages.length === 0 ? (
          <EmptyState title="No messages yet" description="Start a new conversation by typing a message below." />
        ) : (
          <Container className="max-w-4xl mx-auto">
            <MessageList
              messages={messages.map((m) => ({ ...m, id: m.id || "" }))}
              isLoading={isLoading}
              messagesEndRef={messagesEndRef}
            />
            <div ref={messagesEndRef} />
          </Container>
        )}
      </div>

      {/* Input Footer */}
      {chatId && (
        <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-slate-800 px-4 py-4">
          <Container className="max-w-4xl mx-auto">
            <ChatInput disabled={history.length === 0} />
          </Container>
        </div>
      )}
    </div>
  );
};
