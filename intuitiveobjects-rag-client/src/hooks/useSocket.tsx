import { useCallback, useEffect, useState } from "react";
import io, { Socket } from "socket.io-client";

import { useAppSelector } from "@/store/hooks";

const useSocket = (url: string) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const token = useAppSelector((state) => state.auth.admin?.token);

  const connectSocket = useCallback(() => {
    if (!url || !token) return;

    const socketIO = io(url, {
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      auth: {
        token,
      },
    });

    socketIO.on("connect", () => {
      console.log("connected");
      setSocket(socketIO);
    });

    socketIO.on("disconnect", () => {
      setSocket(null);
    });

    socketIO.on("error", (error) => {
      console.log("error", error);
      setSocket(null);
    });

    return socketIO;
  }, [url, token]);

  useEffect(() => {
    const socketIO = connectSocket();
    return () => {
      socketIO?.close();
    };
  }, [connectSocket]);

  const onDocumentNotifyListener = useCallback(
    (callback: (message: any) => void) => {
      socket?.on("document_notify", callback);
    },
    [socket]
  );

  const offDocumentNotifyListener = useCallback(
    (callback: (message: any) => void) => {
      socket?.off("document_notify", callback);
    },
    [socket]
  );

  return {
    socket,
    onDocumentNotifyListener,
    offDocumentNotifyListener,
  };
};

export default useSocket;
