import { createContext, useContext } from "react";
import { Socket } from "socket.io-client";

import useSocket from "@/hooks/useSocket";

interface SocketProviderProps {
  children: React.ReactNode;
}

interface ISocketContext {
  socket: Socket | null;
  onDocumentNotifyListener: (callback: (message: any) => void) => void;
  offDocumentNotifyListener: (callback: (message: any) => void) => void;
}

const SocketContext = createContext<ISocketContext | null>(null);

export const SocketProvider = ({ children }: SocketProviderProps) => {
  const socket = useSocket(import.meta.env.VITE_SOCKET_URL);

  return (
    <SocketContext.Provider value={socket}>{children}</SocketContext.Provider>
  );
};

export const useSocketContext = () => {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error("useSocket must be used within a SocketProvider");
  }
  return context;
};
