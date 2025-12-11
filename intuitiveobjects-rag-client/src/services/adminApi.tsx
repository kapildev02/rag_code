import { createAsyncThunk } from "@reduxjs/toolkit";
import { axiosAdminInstance } from "./axiosInstance";

interface CreateOrganizationPayload {
  name: string;
}
export const registerOrganizationAdminApi = createAsyncThunk(
  "organization/register",
  async (payload: CreateOrganizationPayload, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.post(
        "organization/register",
        payload
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);
interface AdminSignUpPayload {
  organization_id: string;
  name: string;
  email: string;
  password: string;
}
export const registerOrganizationAdminApiWithEmail = createAsyncThunk(
  "organization-admin/organizationadmin",
  async (payload: AdminSignUpPayload, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.post(
        `organization-admin/organization/${payload.organization_id}`,
        {
          name: payload.name,
          email: payload.email,
          password: payload.password,
        }
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const orgGetAdminApi = createAsyncThunk(
  "admin/getAdmin",
  async (organization_id: string, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.get(
        `/organization-admin/organization/${organization_id}`
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

// 1. Send OTP to admin's email for credential change
interface SendOtpPayload {
  organizationName: string;
  email: string;
}
export const sendOtpApi = createAsyncThunk(
  "admin/sendOtp",
  async (payload: SendOtpPayload, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.post(
        "/organization-admin/send-otp",
        payload
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);
// 2. Verify OTP and update admin credentials
interface VerifyOtpAndUpdatePayload {
  organizationName: string;
  email: string;
  otp: string;
  newPassword: string;
  newEmail: string;
}
export const verifyOtpAndUpdateAdminApi = createAsyncThunk(
  "admin/verifyOtpAndUpdate",
  async (payload: VerifyOtpAndUpdatePayload, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.post(
        "/organization-admin/verify-otp-update",
        payload
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

interface AdminLoginPayload {
  email: string;
  password: string;
}

export const orgAdminLoginApi = createAsyncThunk(
  "orgAdmin/login",
  async (credentials: AdminLoginPayload, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.post(
        "/organization-admin/login",
        credentials
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const orgAdminProfileApi = createAsyncThunk(
  "orgAdmin/profile",
  async (_, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.get(
        "/organization-admin/profile"
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const googleAuthApi = createAsyncThunk(
  "orgAdmin/googleAuth",
  async (_, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.get(
        "/organization-admin/google/auth"
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const disconnectGoogleDriveApi = createAsyncThunk(
  "orgAdmin/disconnectGoogleDrive",
  async (_, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.delete(
        "/organization-admin/google/auth"
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const getGoogleDriveFilesApi = createAsyncThunk(
  "orgAdmin/getGoogleDriveFiles",
  async (_, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.get(
        "/organization-admin/google/list-files"
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const googleDriveFileUploadApi = createAsyncThunk(
  "orgAdmin/googleDriveFileUpload",
  async (data: any, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.post(
        `organization-file/google-drive/upload`,
        data
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const localFileUploadApi = createAsyncThunk(
  "orgAdmin/localFileUpload",
  async (data: any, { rejectWithValue }) => {
    try {
      const formData = new FormData();

      for (const file of data.files) {
        formData.append("files", file); // Append each file separately
      }

      formData.append("category_id", data.category_id);
      formData.append("tags", data.tags);

      const response = await axiosAdminInstance.post(
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

interface CreateCategoryPayload {
  name: string;
  tags: string[] | string;
}

export const orgCreateCategoryApi = createAsyncThunk(
  "org/createCategory",
  async (category: CreateCategoryPayload, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.post(
        "organization-admin/category",
        { name: category.name, tags: category.tags }
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const orgUpdateCategoryApi = createAsyncThunk(
  "org/updateCategory",
  async (category, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.put(
        `/organization-admin/categories/${category}`,
        category
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const orgDeleteCategoryApi = createAsyncThunk(
  "org/deleteCategory",
  async (categoryId: string, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.delete(
        `organization-admin/category/${categoryId}`
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const orgGetCategoriesApi = createAsyncThunk(
  "org/getCategories",
  async (_, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.get(
        "/organization-admin/category"
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const orgCreateUserApi = createAsyncThunk(
  "org/createUser",
  async (user: any, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.post(
        "/organization-user",
        user
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const orgUpdateUserApi = createAsyncThunk(
  "org/updateUser",
  async (user: any, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.put(
        `/organization-admin/users/${user.id}`,
        user
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const orgDeleteUserApi = createAsyncThunk(
  "org/deleteUser",
  async (userId: string, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.delete(
        `/organization-user/${userId}`
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const orgGetUsersApi = createAsyncThunk(
  "org/getUsers",
  async (_, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.get("/organization-user");
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

interface IngestDocumentPayload {
  values: {
    category_id: string;
    file: File;
    tags: string[];
  };
  onProgress: (progress: number) => void;
}

export const orgIngestDocumentApi = createAsyncThunk(
  "org/ingestDocument",
  async (document: IngestDocumentPayload, { rejectWithValue }) => {
    try {
      const formData = new FormData();
      formData.append("category_id", document.values.category_id);
      formData.append("file", document.values.file);
      formData.append("tags", JSON.stringify(document.values.tags));

      const response = await axiosAdminInstance.post(
        "/organization-file/upload",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
          onUploadProgress: (progressEvent) => {
            console.log(progressEvent);
            const progress = Math.round(
              (progressEvent.loaded * 100) / (progressEvent.total || 1)
            );
            console.log(progress);
            document.onProgress(progress);
          },
        }
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const orgGetFilesApi = createAsyncThunk(
  "org/getFiles",
  async (_, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.get("/organization-file/all");
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const orgDeleteFileApi = createAsyncThunk(
  "org/deleteFile",
  async (fileId: string, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.delete(
        `/organization-file/${fileId}`
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const settingGetAppConfigApi = createAsyncThunk(
  "setting/getAppConfig",
  async (_, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.get(
        "/organization-app-config/app-config"
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const settingUpdateAppConfigApi = createAsyncThunk(
  "setting/updateAppConfig",
  async (config: any, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.post(
        "/organization-admin/organization-app-config",
        config
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const settingGetAppCurrentConfigApi = createAsyncThunk(
  "setting/getAppCurrentConfig",
  async (_, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.get(
        "/organization-admin/organization-app-config"
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);
export const orgResetMongoApi = createAsyncThunk(
  "org/resetMongo",
  async (_, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.post("/admin/reset-mongo");
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const orgResetChromaApi = createAsyncThunk(
  "org/resetChroma",
  async (_, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.post("/admin/reset-chroma");
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const orgGetCategoryNameApi = createAsyncThunk(
  "org/getCategoryName",
  async (id: string, { rejectWithValue }) => {
    try {
      const response = await axiosAdminInstance.get(
        `/organization-admin/category/${id}`
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

