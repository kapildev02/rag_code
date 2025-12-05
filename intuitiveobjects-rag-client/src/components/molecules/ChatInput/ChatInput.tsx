import {
  useState,
  KeyboardEvent,
  useRef,
  useEffect,
  useCallback,
} from "react";
import { Button } from "@/components/atoms/Button/Button";
import { TextArea } from "@/components/atoms/TextArea/TextArea";
import { Icon } from "@/components/atoms/Icon/Icon";
import { useAppDispatch } from "@/store/hooks";
import { addMessage, setLoading } from "@/store/slices/chatSlice";
import { useParams } from "react-router-dom";
import { sendChatMessageApi } from "@/services/chatApis";

interface ChatInputProps {
  disabled?: boolean;
}

export const ChatInput = ({ disabled }: ChatInputProps) => {
  const [message, setMessage] = useState("");
  const [isWaiting, setIsWaiting] = useState(false);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);

  const dispatch = useAppDispatch();
  const { chatId } = useParams();

  const sendMessage = useCallback(
    async (msg: string) => {
      if (msg.trim() && !disabled && chatId) {
        setIsWaiting(true);
        dispatch(setLoading(true));

        // Optimistically add user message
        dispatch(
          addMessage({
            id: null,
            content: msg,
            sources: [],
            role: "user",
            timestamp: new Date().toISOString(),
          })
        );

        setMessage(""); // clear input

        try {
          await dispatch(sendChatMessageApi({ chatId, content: msg.trim() }));
        } catch (error) {
          console.error("Error sending message:", error);
          // Show system feedback
          dispatch(
            addMessage({
              id: null,
              content: "⚠️ Failed to send message. Please try again.",
              sources: [],
              role: "assistant",
              timestamp: new Date().toISOString(),
            })
          );
        } finally {
          setIsWaiting(false);
          dispatch(setLoading(false));
        }
      }
    },
    [disabled, chatId, dispatch]
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await sendMessage(message);
  };

  const handleKeyDown = async (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      await sendMessage(message);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textAreaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, [message]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      dispatch(
        addMessage({
          id: null,
          content: `📎 Uploaded file: ${file.name}`,
          sources: [],
          role: "user",
          timestamp: new Date().toISOString(),
        })
      );
      // TODO: integrate file upload API here
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="relative bg-chat-bg rounded-lg shadow-lg"
    >
      {/* File upload */}
      <label
        htmlFor="file-upload"
        className="absolute left-2 top-3 cursor-pointer"
        aria-label="Upload file"
      >
      <Icon name="file upload" className="w-6 h-6 text-blue-500 hover:text-blue-600 cursor-pointer"/>
      </label>
      <input
        id="file-upload"
        type="file"
        className="hidden"
        onChange={handleFileUpload}
      />

      {/* Text input */}
      <TextArea
        ref={textAreaRef}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        className="w-full pl-10 pr-12" 
        placeholder="Send a message..."
        disabled={disabled || isWaiting}
        aria-label="Chat message input"
      />


      {/* Send button */}
      <Button
        type="submit"
        disabled={!message.trim() || disabled || isWaiting}
        variant="ghost"
        className="absolute right-2 bottom-[10px] p-1"
        aria-label="Send message"
      >
        <Icon name="send" className="w-5 h-5 md:w-6 md:h-6" />
      </Button>
    </form>
  );
};
