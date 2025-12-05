import { useState, useEffect } from "react";
import { ChatWindow } from "@/components/organisms/ChatWindow/ChatWindow";
import { Header } from "@/components/organisms/Header/Header";
import { Sidebar } from "@/components/organisms/Sidebar/Sidebar";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { setCurrentChat } from "@/store/slices/chatSlice";
import { useNavigate } from "react-router-dom";
import { createChatApi, getChatsApi } from "@/services/chatApis";

export const Home = () => {
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const dispatch = useAppDispatch();
  const isLoading = useAppSelector((state) => state.chat.isLoading);
  const history = useAppSelector((state) => state.chat.history);
  const [isLoadingSidebar] = useState(false);
  const [isLoadingMessages] = useState(false);

  // Auto-open sidebar on large screens for better UX
  useEffect(() => {
    const handleResize = () => {
      setIsSidebarOpen(window.innerWidth >= 1024);
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const handleNewChat = async () => {
    const response = await dispatch(createChatApi("New Chat"));
    if (response.type === "chat/create/fulfilled") {
      navigate(`/chat/${response.payload.data.id}`);
    }
  };

  const fetchChats = async () => {
    const response = await dispatch(getChatsApi());
    if (response.type === "chat/getChats/fulfilled") {
      if (response.payload.data.length > 0) {
        navigate(`/chat/${response.payload.data[0].id}`);
      }
    }
  };

  useEffect(() => {
    fetchChats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="h-screen flex flex-col">
      <Header onToggleSidebar={() => setIsSidebarOpen((v) => !v)} />

      {/* Sidebar: fixed on the left; pass conversations in expected shape */}
      <Sidebar
        isOpen={isSidebarOpen}
        conversations={history.map((chat) => ({
          id: chat.id,
          title: chat.name || (chat as any).title || `Chat ${chat.id}`,
          timestamp: chat.created_at || "",
        }))}
        onNewChat={handleNewChat}
        onSelectChat={(id) => {
          dispatch(setCurrentChat(id));
          navigate(`/chat/${id}`);
        }}
        onClose={() => setIsSidebarOpen(false)}
        isLoading={isLoadingSidebar}
      />

      {/* Main area: let ChatWindow handle left offset (lg:ml-64) so we don't double apply margin */}
      <main className="flex-1">
        <ChatWindow onload={isLoadingMessages} isLoading={isLoading} />
      </main>
    </div>
  );
};
