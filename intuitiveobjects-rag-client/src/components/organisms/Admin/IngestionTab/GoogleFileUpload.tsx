import useFormValidation from "@/hooks/useFormValidation";
import { validateIngestionForm } from "@/hooks/vaidate";
import {
  googleAuthApi,
  disconnectGoogleDriveApi,
  getGoogleDriveFilesApi,
  googleDriveFileUploadApi,
} from "@/services/adminApi";
import { useAppSelector, useAppDispatch } from "@/store/hooks";
import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import { SelectInput } from "@/components/atoms/SelectInput";
import { Button } from "@/components/atoms/Button/Button";
import { TextInput } from "@/components/atoms/TextInput";
import Chip from "@/components/atoms/Chip";
import { formatFileSize } from "@/utils/function";
import { GoogleDriveIcon } from "@/components/atoms/Icon/GoogleDriveIcon";

interface GoogleDriveFile {
  id: string;
  name: string;
  size?: string;
  mimeType: string;
  modifiedTime: string;
}

interface IngestionState {
  category_id: string;
  files: GoogleDriveFile[];
  tags: string[];
}

const initialState: IngestionState = {
  category_id: "",
  files: [],
  tags: [],
};

const GoogleFileUpload = ({
  setIsUploading,
  isUploading,
}: {
  setIsUploading: (isUploading: boolean) => void;
  isUploading: boolean;
}) => {
  const dispatch = useAppDispatch();
  const profile = useAppSelector((state) => state.admin.profile);

  const categories = useAppSelector((state) => state.admin.categories);
  const ingestionForm = useFormValidation(initialState, validateIngestionForm);
  const [error, setError] = useState<string | null>(null);
  const [newTag, setNewTag] = useState("");

  // Google Drive file picker states
  const [showFilePicker, setShowFilePicker] = useState(false);
  // const [selectedGoogleDriveFiles, setSelectedGoogleDriveFiles] = useState<GoogleDriveFile[]>([]);

  useEffect(() => {
    if (error) setError(null);
  }, [ingestionForm.values]);

  // Handle Google Drive file selection - updated for multiple files
  const handleGoogleDriveFilesSelected = (files: GoogleDriveFile[]) => {
    ingestionForm.setValues({
      ...ingestionForm.values,
      files: files,
    });
  };

  // Open Google Drive file picker
  const openGoogleDriveFilePicker = () => {
    setShowFilePicker(true);
  };

  // Close Google Drive file picker
  const closeGoogleDriveFilePicker = () => {
    setShowFilePicker(false);
  };

  // Remove individual Google Drive file
  const removeGoogleDriveFile = (fileId: string) => {
    ingestionForm.setValues((prev) => ({
      ...prev,
      files: prev.files.filter((file) => file.id !== fileId),
    }));
  };

  const onSubmit = async () => {
    setIsUploading(true);

    const fileData = {
      category_id: ingestionForm.values.category_id,
      files: ingestionForm.values.files.map((file) => file.id),
      tags: ingestionForm.values.tags,
    };

    const response = await dispatch(googleDriveFileUploadApi(fileData));
    if (googleDriveFileUploadApi.fulfilled.match(response)) {
      setIsUploading(false);
    }

    setIsUploading(false);
    ingestionForm.onReset();
    setNewTag("");
  };

  const handleAddNewTag = () => {
    const isAlreadyInTags = ingestionForm.values.tags.find(
      (tag: string) => tag === newTag
    );

    if (isAlreadyInTags) {
      toast.error("Tag already exists");
      return;
    }

    ingestionForm.setValues({
      ...ingestionForm.values,
      tags: [...ingestionForm.values.tags, newTag],
    });
    setNewTag("");
  };

  const handleRemoveTag = (tag: string) => {
    ingestionForm.setValues({
      ...ingestionForm.values,
      tags: ingestionForm.values.tags.filter((t: string) => t !== tag),
    });
  };

  const handleSelectCategory = (category: string) => {
    ingestionForm.setValues({
      ...ingestionForm.values,
      category_id: category,
    });
  };

  // Clear selected files when disconnecting Google Drive
  const handleClearSelectedFiles = () => {
    ingestionForm.setValues({
      ...ingestionForm.values,
      files: [],
    });
  };

  const connectGoogleDrive = async () => {
    try {
      const response = await dispatch(googleAuthApi());
      if (googleAuthApi.fulfilled.match(response)) {
        if (response.payload.data?.auth_url) {
          window.location.href = response.payload.data.auth_url;
        }
      }
    } catch (error) {
      console.error("Error connecting Google Drive:", error);
      toast.error("An error occurred while connecting Google Drive");
    }
  };

  const disconnectGoogleDrive = async () => {
    try {
      const response = await dispatch(disconnectGoogleDriveApi());
      if (disconnectGoogleDriveApi.fulfilled.match(response)) {
        if (response.payload.data?.message) {
          toast.success(response.payload.data.message);
          handleClearSelectedFiles(); // Clear selected files when disconnecting
        }
      }
    } catch (error) {
      console.error("Error disconnecting Google Drive:", error);
      toast.error("An error occurred while disconnecting Google Drive");
    }
  };

  // Calculate total size of selected files
  const getTotalFileSize = () => {
    const googleDriveSize = ingestionForm.values.files.reduce(
      (total, file) => total + parseInt(file.size || "0"),
      0
    );
    return googleDriveSize;
  };

  const isFormValid = useMemo(() => {
    return (
      ingestionForm.values.category_id &&
      ingestionForm.values.files.length > 0 &&
      ingestionForm.values.tags.length > 0
    );
  }, [ingestionForm]);

  return (
    <div className="bg-primary-100 rounded-lg border-b border-gray-700 pb-6">
      <h2 className="text-lg text-gray-200 font-medium mb-4">
        Upload Google Document
      </h2>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          ingestionForm.handleSubmit(onSubmit);
        }}
        className="space-y-4"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SelectInput
            label="Category"
            name="category_id"
            value={ingestionForm.values.category_id}
            onChange={(e) => handleSelectCategory(e.target.value)}
            options={categories.map((category) => ({
              value: category.id,
              label: category.name,
            }))}
          />

          <div className="xl:flex flex-col items-center sm:flex-row gap-2">
            <div className="flex-1 flex items-center gap-x-2">
              {profile?.google_drive_connected ? (
                <div className="flex items-center gap-x-2 w-full">
                  <Button
                    type="button"
                    onClick={openGoogleDriveFilePicker}
                    className="bg-primary-500 text-white flex gap-x-2 p-2 h-fit mt-6 w-full sm:w-auto"
                  >
                    SELECT FILES <GoogleDriveIcon />
                  </Button>
                  <Button
                    onClick={disconnectGoogleDrive}
                    type="button"
                    className="bg-red-500 text-white flex gap-x-2 p-2 h-fit mt-6 w-full sm:w-auto"
                  >
                    DISCONNECT DRIVE
                  </Button>
                </div>
              ) : (
                <Button
                  type="button"
                  onClick={connectGoogleDrive}
                  className="bg-primary-500 flex gap-x-2 text-white p-2 h-fit mt-6 w-full sm:w-auto"
                >
                  CONNECT DRIVE <GoogleDriveIcon />
                </Button>
              )}
            </div>
          </div>

          <div className="xl:flex flex-col sm:flex-row space-y-2 sm:space-y-0 gap-2 items-end">
            <div className="flex-1">
              <TextInput
                label="Tags"
                name="tags"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddNewTag();
                  }
                }}
              />
            </div>
            <Button
              type="button"
              onClick={handleAddNewTag}
              disabled={!newTag.trim()}
              className="bg-primary-500 text-gray-200 p-2 h-fit w-full sm:w-auto"
            >
              Add Tag
            </Button>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mb-2">
          {ingestionForm.values?.tags?.map((tag: string) => (
            <Chip
              key={tag}
              label={tag}
              removeTag={handleRemoveTag}
              color="blue"
            />
          ))}
        </div>

        {/* Display selected files info - updated for multiple files */}
        {ingestionForm.values.files.length > 0 && (
          <div className="col-span-2">
            <div className="bg-gray-800 rounded-lg p-3">
              <h4 className="text-sm font-medium text-gray-300 mb-2">
                Selected Files (
                {ingestionForm.values.files.length +
                  (ingestionForm.values.files ? 1 : 0)}
                ):
              </h4>

              {/* Google Drive files display */}
              {ingestionForm.values.files.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center justify-between mb-2 p-2 bg-gray-700 rounded"
                >
                  <div className="text-gray-400 text-sm">
                    {file.name}
                    <span className="ml-2 text-xs">
                      ({formatFileSize(parseInt(file.size || "0"))})
                    </span>
                    <div className="text-xs text-blue-400 mt-1">
                      📁 From Google Drive
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeGoogleDriveFile(file.id)}
                    className="text-gray-500 hover:text-gray-300 ml-2"
                  >
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>
              ))}

              {/* Total size display */}
              <div className="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-600">
                Total Size: {formatFileSize(getTotalFileSize())}
              </div>
            </div>
          </div>
        )}

        {error && <div className="text-red-400 text-sm mt-2">{error}</div>}

        <Button
          type="submit"
          disabled={isUploading || !isFormValid}
          className="px-4 py-[9px] rounded-md transition-colors duration-200 disabled:opacity-50 bg-chat-border text-white hover:bg-hover-bg disabled:hover:bg-chat-border w-full btn-primary"
        >
          {isUploading
            ? "Uploading..."
            : `Upload ${ingestionForm.values.files.length} Document(s)`}
        </Button>
      </form>

      {/* Google Drive File Picker Modal - now with multiSelect enabled */}
      <GoogleDriveFilePicker
        isOpen={showFilePicker}
        onClose={closeGoogleDriveFilePicker}
        onFilesSelected={handleGoogleDriveFilesSelected}
        multiSelect={true} // Enable multiple file selection
      />
    </div>
  );
};

interface GoogleDriveFilePickerProps {
  isOpen: boolean;
  onClose: () => void;
  onFilesSelected: (files: GoogleDriveFile[]) => void;
  multiSelect?: boolean;
}

const GoogleDriveFilePicker: React.FC<GoogleDriveFilePickerProps> = ({
  isOpen,
  onClose,
  onFilesSelected,
  multiSelect = false,
}) => {
  const [googleDriveFiles, setGoogleDriveFiles] = useState<GoogleDriveFile[]>(
    []
  );
  const [selectedFiles, setSelectedFiles] = useState<GoogleDriveFile[]>([]);
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const dispatch = useAppDispatch();

  const loadGoogleDriveFiles = async () => {
    setIsLoadingFiles(true);
    try {
      const response = await dispatch(getGoogleDriveFilesApi());

      if (getGoogleDriveFilesApi.fulfilled.match(response)) {
        const files = (response.payload.data.files || []) as GoogleDriveFile[];
        const filteredFiles = searchQuery
          ? files.filter((file) =>
              file.name.toLowerCase().includes(searchQuery.toLowerCase())
            )
          : files;

        setGoogleDriveFiles(filteredFiles);
      }
    } catch (error) {
      console.error("Error loading Google Drive files:", error);
      toast.error("Failed to load Google Drive files");
    } finally {
      setIsLoadingFiles(false);
    }
  };

  // Handle file selection
  const handleFileSelection = (file: GoogleDriveFile, isSelected: boolean) => {
    if (multiSelect) {
      if (isSelected) {
        setSelectedFiles((prev) => [...prev, file]);
      } else {
        setSelectedFiles((prev) => prev.filter((f) => f.id !== file.id));
      }
    } else {
      // Single select mode
      if (isSelected) {
        setSelectedFiles([file]);
      } else {
        setSelectedFiles([]);
      }
    }
  };

  // Select all files
  const handleSelectAll = () => {
    if (selectedFiles.length === googleDriveFiles.length) {
      // Deselect all
      setSelectedFiles([]);
    } else {
      // Select all
      setSelectedFiles([...googleDriveFiles]);
    }
  };

  // Confirm file selection
  const confirmFileSelection = () => {
    if (selectedFiles.length > 0) {
      onFilesSelected(selectedFiles);
      handleClose();
    }
  };

  // Handle modal close
  const handleClose = () => {
    setSelectedFiles([]);
    setSearchQuery("");
    onClose();
  };

  // Load files when modal opens
  useEffect(() => {
    if (isOpen) {
      loadGoogleDriveFiles();
    }
  }, [isOpen]);

  // Search with debounce
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (isOpen && searchQuery !== "") {
        loadGoogleDriveFiles();
      }
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  // Get file type icon
  const getFileIcon = (mimeType: string) => {
    if (mimeType.includes("pdf")) return "📄";
    if (mimeType.includes("spreadsheet") || mimeType.includes("excel"))
      return "📊";
    if (mimeType.includes("presentation") || mimeType.includes("powerpoint"))
      return "📽️";
    if (mimeType.includes("document") || mimeType.includes("word")) return "📝";
    if (mimeType.includes("image")) return "🖼️";
    if (mimeType.includes("video")) return "🎥";
    if (mimeType.includes("audio")) return "🎵";
    return "📁";
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center !z-[100]">
      <div className="fixed bg-[#343541] rounded-lg p-6 w-full max-w-4xl max-h-[80vh] overflow-hidden border border-gray-600">
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-100">
            Select Google Drive Files {multiSelect && "(Multiple Selection)"}
          </h3>
          <button
            onClick={handleClose}
            className="text-gray-300 hover:text-gray-100 transition-colors"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Search Bar */}
        <div className="mb-4">
          <div className="relative">
            <input
              type="text"
              placeholder="Search files..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-[#2A2B32] border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100 placeholder-gray-400"
            />
            <svg
              className="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
        </div>

        {/* Select All Button for multi-select */}
        {multiSelect && googleDriveFiles.length > 0 && (
          <div className="mb-4">
            <Button
              type="button"
              onClick={handleSelectAll}
              className="text-sm bg-[#4a4b53] text-gray-200 px-3 py-1 hover:bg-[#5a5b63] transition-colors border border-gray-600"
            >
              {selectedFiles.length === googleDriveFiles.length
                ? "Deselect All"
                : "Select All"}
            </Button>
          </div>
        )}

        {/* File List */}
        <div className="overflow-y-auto max-h-96 mb-4">
          {isLoadingFiles ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              <span className="ml-2 text-gray-300">Loading files...</span>
            </div>
          ) : googleDriveFiles.length === 0 ? (
            <div className="text-center py-8 text-gray-300">
              {searchQuery
                ? "No files found matching your search."
                : "No files found in Google Drive."}
            </div>
          ) : (
            <div className="space-y-2 overflow-y-auto">
              {googleDriveFiles.map((file) => {
                const isSelected = selectedFiles.some((f) => f.id === file.id);
                return (
                  <div
                    key={file.id}
                    className={`flex items-center p-3 border rounded-lg hover:bg-[#2A2B32] transition-colors cursor-pointer ${
                      isSelected
                        ? "bg-[#1e3a8a] border-blue-500"
                        : "border-gray-600 bg-[#404148]"
                    }`}
                    onClick={() => handleFileSelection(file, !isSelected)}
                  >
                    <input
                      type={multiSelect ? "checkbox" : "radio"}
                      name="file-selection"
                      id={`file-${file.id}`}
                      checked={isSelected}
                      onChange={(e) =>
                        handleFileSelection(file, e.target.checked)
                      }
                      className="mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-500 rounded bg-gray-700"
                    />
                    <div className="flex items-center flex-1">
                      <span className="text-2xl mr-3">
                        {getFileIcon(file.mimeType)}
                      </span>
                      <div className="flex-1">
                        <div className="font-medium text-gray-100">
                          {file.name}
                        </div>
                        <div className="text-sm text-gray-400">
                          {file.size && formatFileSize(parseInt(file.size))} •
                          Modified{" "}
                          {new Date(file.modifiedTime).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-300">
            {selectedFiles.length} file{selectedFiles.length !== 1 ? "s" : ""}{" "}
            selected
          </div>
          <div className="space-x-2">
            <Button
              type="button"
              onClick={handleClose}
              className="bg-[#4a4b53] text-gray-200 px-4 py-2 hover:bg-[#5a5b63] transition-colors border border-gray-600"
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={confirmFileSelection}
              disabled={selectedFiles.length === 0}
              className="bg-blue-600 text-white px-4 py-2 hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Select{" "}
              {selectedFiles.length > 0 ? `${selectedFiles.length} ` : ""}File
              {selectedFiles.length !== 1 ? "s" : ""}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
export default GoogleFileUpload;
