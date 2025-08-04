// import { useState, KeyboardEvent, useRef, useEffect, useCallback } from "react";
// import { Button } from "@/components/atoms/Button/Button";
// import { TextArea } from "@/components/atoms/TextArea/TextArea";
// import { Icon } from "@/components/atoms/Icon/Icon";
// import { useAppDispatch } from "@/store/hooks";
// import { addMessage, setLoading } from "@/store/slices/chatSlice";
// import { useParams } from "react-router-dom";
// import { sendChatMessageApi } from "@/services/chatApis";

// interface ChatInputProps {
//   disabled?: boolean;
// }

// export const ChatInput = ({ disabled }: ChatInputProps) => {
//   const [message, setMessage] = useState("");
//   const [isWaiting, setIsWaiting] = useState(false);
//   const textAreaRef = useRef<HTMLTextAreaElement>(null);

//   const dispatch = useAppDispatch();
//   const { chatId } = useParams();

//   const sendMessage = useCallback(async () => {
//     if (message.trim() && !disabled && chatId) {
//       const trimmedMessage = message.trim();
//       setIsWaiting(true);
//       dispatch(setLoading(true));
//       dispatch(
//         addMessage({
//           id: null,
//           content: trimmedMessage,
//           role: "user",
//           timestamp: new Date().toISOString(),
//         })
//       );
//       setMessage("");

//       await dispatch(sendChatMessageApi({ chatId, content: trimmedMessage }));

//       setIsWaiting(false);
//       dispatch(setLoading(false));
//     }
//   }, [message, disabled, chatId, dispatch]);

//   const handleSubmit = async (e: React.FormEvent) => {
//     e.preventDefault();
//     await sendMessage();
//   };

//   const handleKeyDown = async (e: KeyboardEvent<HTMLTextAreaElement>) => {
//     if (e.key === "Enter" && !e.shiftKey) {
//       e.preventDefault();
//       await sendMessage();
//     }
//   };

//   useEffect(() => {
//     const textarea = textAreaRef.current;
//     if (textarea) {
//       textarea.style.height = "auto";
//       textarea.style.height = `${textarea.scrollHeight}px`;
//     }
//   }, [message]);

//   useEffect(() => {
//     if (!isWaiting && textAreaRef.current) {
//       textAreaRef.current.focus();
//     }
//   }, [isWaiting]);

//   return (
//     <form
//       onSubmit={handleSubmit}
//       className="relative bg-chat-bg rounded-lg shadow-lg"
//     >
//       <TextArea
//         ref={textAreaRef}
//         value={message}
//         onChange={(e) => setMessage(e.target.value)}
//         onKeyDown={handleKeyDown}
//         className="w-full pr-12"
//         placeholder="Send a message..."
//         disabled={disabled || isWaiting}
//       />
//       <Button
//         type="submit"
//         aria-label="Send message"
//         disabled={!message.trim() || disabled || isWaiting}
//         variant="ghost"
//         className="absolute right-2 bottom-[10px] p-1"
//       >
//         <Icon name="send" className="w-5 h-5 md:w-6 md:h-6" />
//       </Button>
//     </form>
//   );
// };
import { useState, KeyboardEvent, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/atoms/Button/Button";
import { TextArea } from "@/components/atoms/TextArea/TextArea";
import { Icon } from "@/components/atoms/Icon/Icon";
import { useAppDispatch } from "@/store/hooks";
import { addMessage, setLoading } from "@/store/slices/chatSlice";
import { useParams } from "react-router-dom";
import { sendChatMessageApi } from "@/services/chatApis";
import { orgGetFilesApi } from "@/services/adminApi";

interface ChatInputProps {
  disabled?: boolean;
}

type FileType = {
  id: string;
  file_name: string;
  tags?: string[];
};

export const ChatInput = ({ disabled }: ChatInputProps) => {
  const [message, setMessage] = useState("");
  const [isWaiting, setIsWaiting] = useState(false);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  const [tags, setTags] = useState<string[]>([]);
  const [selectedTag, setSelectedTag] = useState("");
  const dispatch = useAppDispatch();
  const { chatId } = useParams();

  // Fetch tags from backend
  useEffect(() => {
    const fetchTags = async () => {
      try {
        const res = await dispatch(orgGetFilesApi()).unwrap();
        console.log("Files Response:", res);
        const uniqueTags: string[] = Array.from(
          new Set(res.data.flatMap((file: FileType) => file.tags || []))
        );
        setTags(uniqueTags);
      } catch (err) {
        console.error("Failed to load tags", err);
      }
    };
    fetchTags();
  }, [dispatch]);

  const sendMessage = useCallback(async () => {
    if (message.trim() && !disabled && chatId) {
      const trimmedMessage = message.trim();
      setIsWaiting(true);
      dispatch(setLoading(true));

      dispatch(
        addMessage({
          id: null,
          content: trimmedMessage,
          role: "user",
          timestamp: new Date().toISOString(),
        })
      );

      setMessage("");

      try {
        await dispatch(
          sendChatMessageApi({
            chatId,
            content: trimmedMessage,
            tag: selectedTag || undefined,
          })
        ).unwrap();
        console.log("Sending message with tag:", selectedTag);
      } catch (err) {
        console.error("Failed to send message", err);
      } finally {
        setIsWaiting(false);
        dispatch(setLoading(false));
      }
    }
  }, [message, disabled, chatId, dispatch, selectedTag]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await sendMessage();
  };

  const handleKeyDown = async (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      await sendMessage();
    }
  };

  // Auto-grow textarea
  useEffect(() => {
    const textarea = textAreaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, [message]);

  // Focus on input after sending
  useEffect(() => {
    if (!isWaiting && textAreaRef.current) {
      textAreaRef.current.focus();
    }
  }, [isWaiting]);

  return (
    <>
      <div className="mb-2">
        <select
          value={selectedTag}
          onChange={(e) => setSelectedTag(e.target.value || "")}
          className="px-3 py-2 rounded border text-black"
        >
          <option value="">Select Tag</option>
          {tags.map((tag) => (
            <option key={tag} value={tag}>
              {tag}
            </option>
          ))}
        </select>
      </div>

      <form
        onSubmit={handleSubmit}
        className="relative bg-chat-bg rounded-lg shadow-lg"
      >
        <TextArea
          ref={textAreaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          className="w-full pr-12"
          placeholder="Send a message..."
          disabled={disabled || isWaiting}
        />
        <Button
          type="submit"
          aria-label="Send message"
          disabled={!message.trim() || disabled || isWaiting}
          variant="ghost"
          className="absolute right-2 bottom-[10px] p-1"
        >
          <Icon name="send" className="w-5 h-5 md:w-6 md:h-6" />
        </Button>
      </form>
    </>
  );
};
