// import { useState, useEffect } from "react";
// import { useAppDispatch } from "@/store/hooks";
// import { Button } from "@/components/atoms/Button/Button";
// import {
//   orgResetChromaApi,
//   orgResetMongoApi,
//   orgDeleteFileApi,
//   orgGetFilesApi,
// } from "@/services/adminApi";
// import toast from "react-hot-toast";

// const AdditionalTab = () => {
//   const dispatch = useAppDispatch();
//   const [loading, setLoading] = useState(false);
//   const [fileId, setFileId] = useState("");
//   const [files, setFiles] = useState<{ id: string; file_name: string }[]>([]);

//   // Fetch file list on mount
//   useEffect(() => {
//     const fetchFiles = async () => {
//       try {
//         const response = await dispatch(orgGetFilesApi()).unwrap();
//         console.log("Files response:", response.data);
//         if (response.success && Array.isArray(response.data)) {
//           setFiles(response.data);
//         }
//       } catch (err) {
//         toast.error("Failed to fetch files");
//       }
//     };
//     fetchFiles();
//   }, [dispatch]);

//   const handleResetChroma = async () => {
//     setLoading(true);
//     try {
//       const response = await dispatch(orgResetChromaApi()).unwrap();
//       toast[response.success ? "success" : "error"](
//         response.success
//           ? "ChromaDB reset successfully"
//           : "Failed to reset ChromaDB"
//       );
//     } catch (err: any) {
//       toast.error(
//         "Error resetting ChromaDB: " + (err.message || "Unknown error")
//       );
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleResetMongo = async () => {
//     setLoading(true);
//     try {
//       const response = await dispatch(orgResetMongoApi()).unwrap();
//       toast[response.success ? "success" : "error"](
//         response.success
//           ? "MongoDB reset successfully"
//           : "Failed to reset MongoDB"
//       );
//     } catch (err: any) {
//       toast.error(
//         "Error resetting MongoDB: " + (err.message || "Unknown error")
//       );
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleDeleteFile = async () => {
//     if (!fileId) {
//       toast.error("Please select a file");
//       return;
//     }
//     setLoading(true);
//     try {
//       const response = await dispatch(orgDeleteFileApi(fileId)).unwrap();
//       toast[response.success ? "success" : "error"](
//         response.success ? "File deleted successfully" : "Failed to delete file"
//       );
//       // Remove deleted file from local state
//       if (response.success) {
//         setFiles(files.filter((file) => file.id !== fileId));
//         setFileId("");
//       }
//     } catch (err: any) {
//       toast.error("Error deleting file: " + (err.message || "Unknown error"));
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <div className="p-6 space-y-4">
//       <h2 className="text-xl font-semibold text-white">Additional Tools</h2>
//       <div className="flex gap-4 flex-wrap items-center">
//         <Button
//           onClick={handleResetChroma}
//           disabled={loading}
//           className="bg-red-600 text-white"
//         >
//           Reset ChromaDB
//         </Button>
//         <Button
//           onClick={handleResetMongo}
//           disabled={loading}
//           className="bg-yellow-500 text-white"
//         >
//           Reset MongoDB
//         </Button>
//         <select
//           value={fileId}
//           onChange={(e) => setFileId(e.target.value)}
//           className="px-2 py-1 rounded"
//         >
//           <option value="">Select File</option>
//           {files.map((file) => (
//             <option key={file.id} value={file.id}>
//               {file.file_name}
//             </option>
//           ))}
//         </select>
//         <Button
//           onClick={handleDeleteFile}
//           disabled={loading || !fileId}
//           className="bg-blue-600 text-white"
//         >
//           Delete File
//         </Button>
//       </div>
//     </div>
//   );
// };

// export default AdditionalTab;
import { useState, useEffect } from "react";
import { useAppDispatch } from "@/store/hooks";
import { Button } from "@/components/atoms/Button/Button";
import {
  orgResetChromaApi,
  orgResetMongoApi,
  orgDeleteFileApi,
  orgGetFilesApi,
} from "@/services/adminApi";
import toast from "react-hot-toast";

type FileType = {
  id: string;
  file_name: string;
  tags?: string[];
  tag?: string;
};

const AdditionalTab = () => {
  const dispatch = useAppDispatch();
  const [loading, setLoading] = useState(false);
  const [fileId, setFileId] = useState("");
  const [files, setFiles] = useState<FileType[]>([]);

  // const groupedFiles = files.reduce((acc, file) => {
  //   const tag = file.file_name.split("_")[3];
  //   if (!acc[tag]) acc[tag] = [];
  //   acc[tag].push(file);
  //   return acc;
  // }, {} as Record<string, FileType[]>);

  const groupedFiles = files.reduce((acc, file) => {
    // If tags is an array, group by each tag
    if (Array.isArray(file.tags)) {
      file.tags.forEach((tag: string) => {
        if (!acc[tag]) acc[tag] = [];
        acc[tag].push(file);
      });
    } else if (file.tag) {
      // If single tag
      const tag = file.tag;
      if (!acc[tag]) acc[tag] = [];
      acc[tag].push(file);
    } else {
      // fallback for files without tag
      if (!acc["untagged"]) acc["untagged"] = [];
      acc["untagged"].push(file);
    }
    return acc;
  }, {} as Record<string, FileType[]>);

  // Fetch file list on mount
  useEffect(() => {
    const fetchFiles = async () => {
      try {
        const response = await dispatch(orgGetFilesApi()).unwrap();
        if (response.success && Array.isArray(response.data)) {
          setFiles(response.data);
        }
      } catch (err) {
        toast.error("Failed to fetch files");
      }
    };
    fetchFiles();
  }, [dispatch]);

  const handleResetChroma = async () => {
    setLoading(true);
    try {
      const response = await dispatch(orgResetChromaApi()).unwrap();
      toast[response.success ? "success" : "error"](
        response.success
          ? "ChromaDB reset successfully"
          : "Failed to reset ChromaDB"
      );
    } catch (err: any) {
      toast.error(
        "Error resetting ChromaDB: " + (err.message || "Unknown error")
      );
    } finally {
      setLoading(false);
    }
  };

  const handleResetMongo = async () => {
    setLoading(true);
    try {
      const response = await dispatch(orgResetMongoApi()).unwrap();
      toast[response.success ? "success" : "error"](
        response.success
          ? "MongoDB reset successfully"
          : "Failed to reset MongoDB"
      );
    } catch (err: any) {
      toast.error(
        "Error resetting MongoDB: " + (err.message || "Unknown error")
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
          onClick={handleResetChroma}
          disabled={loading}
          className="bg-red-600 text-white w-full"
        >
          Reset ChromaDB
        </Button>
        <Button
          onClick={handleResetMongo}
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
            {Object.entries(groupedFiles).map(([tag, fileList]) => (
              <optgroup key={tag} label={tag}>
                {fileList.map((file) => (
                  <option key={file.id} value={file.id}>
                    {file.file_name}
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
          Files Collection by tag
        </h3>
        <div className="mt-2 space-y-4">
          {Object.entries(groupedFiles).map(([tag, group]) => (
            <div key={tag} className="bg-gray-800 p-4 rounded-lg text-white">
              <div className="font-semibold mb-2">Tag: {tag}</div>
              <ul className="list-disc list-inside text-sm">
                {group.map((file) => (
                  <li key={file.id}>{file.file_name}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AdditionalTab;
