import { useState, useEffect } from "react";
import { useAppDispatch } from "@/store/hooks";
import { Button } from "@/components/atoms/Button/Button";
import {
  orgResetChromaApi,
  orgResetMongoApi,
  orgDeleteFileApi,
  orgGetFilesApi,
  orgGetCategoryNameApi,
} from "@/services/adminApi";
import toast from "react-hot-toast";

type FileType = {
  id: string;
  filename: string;
  category_id: string;
  category_name?: string; // Will store the fetched category name
};

type ConfirmAction = {
  open: boolean;
  actionType: "mongodb" | "chromadb" | null;
  input: string;
};

const AdditionalTab = () => {
  const dispatch = useAppDispatch();
  const [loading, setLoading] = useState(false);
  const [fileId, setFileId] = useState("");
  const [files, setFiles] = useState<FileType[]>([]);
  const [confirm, setConfirm] = useState<ConfirmAction>({
    open: false,
    actionType: null,
    input: "",
  });

  const groupedFiles = files.reduce((acc, file) => {
    const categoryName = file.category_name || 'Uncategorized';
    if (!acc[categoryName]) {
      acc[categoryName] = [];
    }
    acc[categoryName].push(file);
    return acc;
  }, {} as Record<string, FileType[]>);

  useEffect(() => {
    const fetchFiles = async () => {
      try {
        const response = await dispatch(orgGetFilesApi()).unwrap();
        if (response.success && Array.isArray(response.data)) {
          // Fetch category names for all files
          const filesWithCategories = await fetchCategoryNames(response.data);
          setFiles(filesWithCategories);
        }
      } catch {
        toast.error("Failed to fetch files");
      }
    };
    fetchFiles();
  }, [dispatch]);

  const fetchCategoryNames = async (files: FileType[]) => {
    const uniqueCategoryIds = [...new Set(files.map((file) => file.category_id))];

    try {
      const categoryPromises = uniqueCategoryIds.map((categoryId) =>
        dispatch(orgGetCategoryNameApi(categoryId)).unwrap()
      );

      const categoryResponses = await Promise.all(categoryPromises);

      // Create a map of category_id to category name
      const categoryMap = categoryResponses.reduce((acc, response) => {
        if (response.success && response.data) {
          acc[response.data.id] = response.data.name;
        }
        return acc;
      }, {} as Record<string, string>);

      // Update files with category names
      return files.map((file) => ({
        ...file,
        category_name: categoryMap[file.category_id] || "Uncategorized",
      }));
    } catch (error) {
      toast.error("Failed to fetch category names");
      return files;
    }
  };

  const triggerReset = (type: "mongodb" | "chromadb") => {
    setConfirm({ open: true, actionType: type, input: "" });
  };

  const handleConfirm = async () => {
    if (!confirm.actionType) return;

    setLoading(true);
    setConfirm({ open: false, actionType: null, input: "" });

    try {
      let response;
      if (confirm.actionType === "mongodb") {
        response = await dispatch(orgResetMongoApi()).unwrap();
      } else {
        response = await dispatch(orgResetChromaApi()).unwrap();
      }
      toast[response.success ? "success" : "error"](
        response.success
          ? `${confirm.actionType} reset successfully`
          : `Failed to reset ${confirm.actionType}`
      );
    } catch (err: any) {
      toast.error(
        `Error resetting ${confirm.actionType}: ` +
          (err.message || "Unknown error")
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteFile = async () => {
    if (!fileId) {
      toast.error("Please select a file");
      return;
    }
    setLoading(true);
    try {
      const response = await dispatch(orgDeleteFileApi(fileId)).unwrap();
      toast[response.success ? "success" : "error"](
        response.success ? "File deleted successfully" : "Failed to delete file"
      );
      if (response.success) {
        setFiles((prev) => prev.filter((file) => file.id !== fileId));
        setFileId("");
      }
    } catch (err: any) {
      toast.error("Error deleting file: " + (err.message || "Unknown error"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-xl font-semibold text-white">
        Ingestion Additional Tools
      </h2>

      {/* Reset buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        <Button
          onClick={() => triggerReset("chromadb")}
          disabled={loading}
          className="bg-red-600 text-white w-full"
        >
          Reset ChromaDB
        </Button>
        <Button
          onClick={() => triggerReset("mongodb")}
          disabled={loading}
          className="bg-yellow-500 text-white w-full"
        >
          Reset MongoDB
        </Button>

        {/* File selection and delete */}
        <div className="flex flex-col space-y-2">
          <select
            value={fileId}
            onChange={(e) => setFileId(e.target.value)}
            className="px-3 py-2 rounded bg-white text-black border"
          >
            <option value="">Select File to Delete</option>
            {Object.entries(groupedFiles).map(([category, fileList]) => (
              <optgroup key={category} label={category}>
                {fileList.map((file) => (
                  <option key={file.id} value={file.id}>
                    {file.filename}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
          <Button
            onClick={handleDeleteFile}
            disabled={loading || !fileId}
            className="bg-blue-600 text-white"
          >
            Delete File
          </Button>
        </div>
      </div>

      {/* File list grouped by tag */}
      <div className="mt-6">
        <h3 className="text-lg text-white font-medium">
          Files Collection by Category
        </h3>
        <div className="mt-2 space-y-4">
          {Object.entries(groupedFiles).map(([category, group]) => (
            <div key={category} className="bg-gray-800 p-4 rounded-lg text-white">
              <div className="font-semibold mb-2">Category: {category}</div>
              <ul className="list-disc list-inside text-sm">
                {group.map((file) => (
                  <li key={file.id}>{file.filename}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Confirmation Modal */}
      {confirm.open && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg shadow-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold text-white">
              Drop {confirm.actionType?.toUpperCase()}?
            </h2>
            <p className="mt-2 text-gray-300">
              Type <b>{`reset ${confirm.actionType}`}</b> to confirm this
              action.
            </p>
            <input
              type="text"
              value={confirm.input}
              onChange={(e) =>
                setConfirm((prev) => ({ ...prev, input: e.target.value }))
              }
              className="w-full border rounded px-3 py-2 mt-4 bg-gray-700 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={`reset ${confirm.actionType}`}
            />
            <div className="mt-4 flex justify-end space-x-3">
              <Button
                onClick={() =>
                  setConfirm({ open: false, actionType: null, input: "" })
                }
                className="bg-gray-600 text-white hover:bg-gray-700"
              >
                Cancel
              </Button>
              <Button
                onClick={handleConfirm}
                disabled={
                  confirm.input.trim().toLowerCase() !==
                  `reset ${confirm.actionType}`
                }
                className="bg-red-600 text-white hover:bg-red-700"
              >
                Confirm Reset
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdditionalTab;
