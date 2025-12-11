import { createAsyncThunk } from "@reduxjs/toolkit";
import { axiosUserInstance } from "./axiosInstance";

export const createChatApi = createAsyncThunk(
  "chat/create",
  async (name: string, { rejectWithValue }) => {
    try {
      const response = await axiosUserInstance.post("/chat/user", { name });
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

interface SendChatMessagePayload {
  chatId: string;
  content: string;
}

export const sendChatMessageApi = createAsyncThunk(
  "chat/sendMessage",
  async (value: SendChatMessagePayload, { rejectWithValue }) => {
    try {
      const response = await axiosUserInstance.post(
        `/chat/${value.chatId}/user/message`,
        { content: value.content }
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const getChatMessagesApi = createAsyncThunk(
  "chat/getMessages",
  async (chatId: string, { rejectWithValue }) => {
    try {
      const response = await axiosUserInstance.get(
        `/chat/${chatId}/user/messages`
      );

      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const getChatsApi = createAsyncThunk(
  "chat/getChats",
  async (_, { rejectWithValue }) => {
    try {
      const response = await axiosUserInstance.get("/chat/user");

      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const deleteChatApi = createAsyncThunk(
  "chat/delete",
  async (chatId: string, { rejectWithValue }) => {
    try {
      const response = await axiosUserInstance.delete(`/chat/${chatId}/user`);

      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

interface EditChatPayload {
  chatId: string;
  name: string;
}

export const editChatApi = createAsyncThunk(
  "chat/edit",
  async (payload: EditChatPayload, { rejectWithValue }) => {
    try {
      const response = await axiosUserInstance.put(
        `/chat/${payload.chatId}/user`,
        { name: payload.name }
      );

      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const userPublicFile = createAsyncThunk(
  "orgAdmin/localFileUpload",
  async (data: any, { rejectWithValue }) => {
    try {
      const formData = new FormData();

      for (const file of data.files) {
        formData.append("files", file); // Append each file separately
      }

      formData.append("category_id", data.category_id);
      formData.append("tags", data.tags);

      // This endpoint expects a user token (get_current_user). Use the user axios instance.
      const response = await axiosUserInstance.post(
        "organization-file/local-drive/upload",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const userPrivateFile = createAsyncThunk(
  "chat/sendUserPrivateFile",
  async (data: any, { rejectWithValue }) => {
    try {
      const formData = new FormData();

      for (const file of data.files) {
        formData.append("files", file); // Append each file separately
      }

      formData.append("category_id", data.category_id);
      formData.append("tags", data.tags);

      // This endpoint expects a user token (get_current_user). Use the user axios instance.
      const response = await axiosUserInstance.post(
        `/chat/upload-file`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);