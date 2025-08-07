import { createSlice } from "@reduxjs/toolkit";
import {
  orgCreateCategoryApi,
  orgCreateUserApi,
  orgDeleteCategoryApi,
  orgGetCategoriesApi,
  orgGetUsersApi,
  orgDeleteUserApi,
  orgGetFilesApi,
  orgDeleteFileApi,
  settingGetAppConfigApi,
  settingUpdateAppConfigApi,
  settingGetAppCurrentConfigApi,
  orgAdminProfileApi,
  disconnectGoogleDriveApi,
  googleDriveFileUploadApi,
  localFileUploadApi,
} from "@/services/adminApi";

interface UserProfile {
  id: string;
  name: string;
  email: string;
  organization_id: string;
  role: string;
  google_drive_connected: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface AdminState {
  categories: any[];
  users: any[];
  files: any[];
  loading: boolean;
  error: string | null;
  appConfig: any;
  currentAppConfig: any;
  profile: UserProfile | null;
}

const initialState: AdminState = {
  categories: [],
  users: [],
  files: [],
  loading: false,
  error: null,
  appConfig: null,
  currentAppConfig: null,
  profile: null,
};

const adminSlice = createSlice({
  name: "admin",
  initialState,
  reducers: {
    updateFiles: (state, action) => {
      state.files = state.files.map((file) =>
        file.id === action.payload.id ? { ...file, ...action.payload } : file
      );
    },
  },
  extraReducers: (builder) => {
    builder.addCase(orgGetCategoriesApi.fulfilled, (state, action) => {
      state.categories = action.payload.data;
    });
    builder.addCase(orgCreateCategoryApi.fulfilled, (state, action) => {
      state.categories.push(action.payload.data);
    });
    builder.addCase(orgDeleteCategoryApi.fulfilled, (state, action) => {
      state.categories = state.categories.filter(
        (category) => category.id !== action.payload.data.id
      );
    });
    builder.addCase(orgCreateUserApi.fulfilled, (state, action) => {
      if (action.payload.organization_user) {
        state.users.push(action.payload.organization_user);
      }
    });
    builder.addCase(orgGetUsersApi.fulfilled, (state, action) => {
      if (action.payload.organization_users) {
        state.users = action.payload.organization_users;
      }
    });
    builder.addCase(orgDeleteUserApi.fulfilled, (state, action) => {
      state.users = state.users.filter(
        (user) => user.id !== action.payload.data.id
      );
    });
    builder.addCase(googleDriveFileUploadApi.fulfilled, (state, action) => {
      if (action.payload.data) {
        state.files = [...state.files, ...action.payload.data];
      }
    });
    builder.addCase(orgGetFilesApi.fulfilled, (state, action) => {
      if (action.payload.data) {
        state.files = action.payload.data;
      }
    });
    builder.addCase(orgDeleteFileApi.fulfilled, (state, action) => {
      if (action.payload.data) {
        state.files = state.files.filter(
          (file) => file.id !== action.payload.data.id
        );
      }
    });
    builder.addCase(settingGetAppConfigApi.fulfilled, (state, action) => {
      if (action.payload.data) {
        state.appConfig = action.payload.data;
      }
    });
    builder.addCase(settingUpdateAppConfigApi.fulfilled, (state, action) => {
      if (action.payload.data) {
        state.currentAppConfig = action.payload.data;
      }
    });
    builder.addCase(
      settingGetAppCurrentConfigApi.fulfilled,
      (state, action) => {
        if (action.payload.data) {
          state.currentAppConfig = action.payload.data?.[0];
        }
      }
    );
    builder.addCase(orgAdminProfileApi.fulfilled, (state, action) => {
      if (action.payload.data) {
        state.profile = action.payload.data;
      }
    });
    builder.addCase(disconnectGoogleDriveApi.fulfilled, (state, action) => {
      if (action.payload.data) {
        state.profile = action.payload.data;
      }
    });
	builder.addCase(localFileUploadApi.fulfilled, (state, action) => {
	  if (action.payload.data) {
		state.files = [...state.files, ...action.payload.data];
	  }
	});
  },
});

export default adminSlice.reducer;
export const { updateFiles } = adminSlice.actions;
