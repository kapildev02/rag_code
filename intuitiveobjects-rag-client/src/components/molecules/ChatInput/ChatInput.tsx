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
import { sendChatMessageApi,userPublicFile, userPrivateFile} from "@/services/chatApis";
import { useAppSelector } from "@/store/hooks";
// import { log } from "console";

interface ChatInputProps {
  disabled?: boolean;
}

export const ChatInput = ({ disabled }: ChatInputProps) => {
  const [message, setMessage] = useState("");
  const [isWaiting, setIsWaiting] = useState(false);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  const dispatch = useAppDispatch();
  const { chatId } = useParams();

  const user = useAppSelector((state) => state.auth.user);
  const [selectedAccess, setSelectedAccess] = useState<"public" | "private">("private");
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  if (!file || !chatId) return;

  dispatch(
    addMessage({
      id: null,
      content: `📎 Uploading file: ${file.name} (${selectedAccess})...`,
      sources: [],
      role: "user",
      timestamp: new Date().toISOString(),
    })
  );

  try {
    if (selectedAccess === "public") {
      
      await dispatch(
        userPublicFile({
          files: [file],
          category_id: "someCategoryId", // supply actual category id
          tags: "tag1,tag2",             // supply actual tags
        })
      ).unwrap();
    } else {
      await dispatch(
        userPrivateFile({
          files: [file],
          category_id: "someCategoryId", 
          tags: "tag1,tag2",             
        })
      ).unwrap();
    }

    dispatch(
      addMessage({
        id: null,
        content: `✅ File "${file.name}" uploaded as ${selectedAccess} and processing started.`,
        sources: [],
        role: "assistant",
        timestamp: new Date().toISOString(),
      })
    );
  } catch (error) {
    console.error(error);
    dispatch(
      addMessage({
        id: null,
        content: `❌ Failed to upload file: ${file.name}`,
        sources: [],
        role: "assistant",
        timestamp: new Date().toISOString(),
      })
    );
  }
};



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

 return (
  <form
    onSubmit={handleSubmit}
    className="w-full bg-chat-bg rounded-xl border border-gray-700 p-3"
  >
    <div className="flex items-center gap-3">

      {/* LEFT SIDE: Upload + Access Dropdown */}
      <div className="flex items-center gap-3">

        {/* Upload Icon */}
        <label htmlFor="file-upload" className="cursor-pointer flex items-center">
          <Icon
            name="file upload"
            className="w-6 h-6 text-blue-400 hover:text-blue-500"
          />
        </label>

        <input
          id="file-upload"
          type="file"
          className="hidden"
          onChange={handleFileUpload}
        />

        {/* Access Dropdown */}
        <select
          value={selectedAccess}
          onChange={(e) =>
            setSelectedAccess(e.target.value as "public" | "private")
          }
          className="bg-gray-800 border border-gray-600 text-white text-sm px-2 py-1 rounded-md"
        >
          <option value="private">Private</option>
          <option value="public">Public</option>
        </select>
      </div>

      {/* INPUT BOX */}
      <div className="flex-1 relative">
        <TextArea
          ref={textAreaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          className="w-full resize-none bg-transparent text-white px-3 py-2 rounded-md placeholder-gray-400"
          placeholder="Message ChatGPT…"
          disabled={disabled || isWaiting}
        />

        {/* SEND BUTTON */}
        <Button
          type="submit"
          disabled={!message.trim() || disabled || isWaiting}
          variant="ghost"
          className="absolute right-2 top-1/2 -translate-y-1/2 p-1"
        >
          <Icon name="send" className="w-6 h-6 text-gray-300 hover:text-white" />
        </Button>
      </div>

    </div>
  </form>


  );
};

