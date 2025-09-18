import useFormValidation from "@/hooks/useFormValidation";
import { validateIngestionForm } from "@/hooks/vaidate";
import { localFileUploadApi, orgIngestDocumentApi } from "@/services/adminApi";
import { useAppSelector, useAppDispatch } from "@/store/hooks";
import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";
import UploadingFileProgress from "./UploadFilePreogress";
import { SelectInput } from "@/components/atoms/SelectInput";
import { FileInput } from "@/components/atoms/FileInput";
import { Button } from "@/components/atoms/Button/Button";
import { TextInput } from "@/components/atoms/TextInput";
import Chip from "@/components/atoms/Chip";

interface IngestionState {
  category_id: string;
  files: File[];
  // tags: string[];
}

const initialState: IngestionState = {
  category_id: "",
  files: [],
  // tags: [],
};

const toastId = "upload-toast";

const LocalFileUpload = ({
  setIsUploading,
  isUploading,
}: {
  setIsUploading: (isUploading: boolean) => void;
  isUploading: boolean;
}) => {
  const dispatch = useAppDispatch();

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const categories = useAppSelector((state) => state.admin.categories);
  const ingestionForm = useFormValidation(initialState, validateIngestionForm);
  const [error, setError] = useState<string | null>(null);

  console.log(ingestionForm.values);

  // const [newTag, setNewTag] = useState("");

  const isFormValid = () => {
    return (
      ingestionForm.values.category_id.trim() !== "" &&
      ingestionForm.values.files.length > 0 
      // ingestionForm.values.tags.length > 0
    );
  };

  useEffect(() => {
    if (error) setError(null);
  }, [ingestionForm.values]);

  const onSubmit = async () => {
    if (!isFormValid()) {
      toast.error("Please select a category and upload at least one PDF file");
      setError("Please select a category and upload at least one PDF file");
      return;
    }
    setIsUploading(true);
    const response = await dispatch(localFileUploadApi(ingestionForm.values));

    if (response.payload) {
      toast.success(
        `${ingestionForm.values.files.length} PDF document(s) uploaded successfully`,
        {
          id: toastId,
          duration: 2000,
        }
      );
      setIsUploading(false);
      ingestionForm.onReset();
      // setNewTag("");
      setTimeout(() => {
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
      }, 100);
    }
  };

  // const handleAddNewTag = () => {
  //   const isAlreadyInTags = ingestionForm.values.tags.find(
  //     (tag: string) => tag === newTag
  //   );

  //   if (isAlreadyInTags) {
  //     toast.error("Tag already exists");
  //     return;
  //   }

  //   ingestionForm.setValues({
  //     ...ingestionForm.values,
  //     tags: [...ingestionForm.values.tags, newTag],
  //   });
  //   setNewTag("");
  // };

  // const handleRemoveTag = (tag: string) => {
  //   ingestionForm.setValues({
  //     ...ingestionForm.values,
  //     tags: ingestionForm.values.tags.filter((t: string) => t !== tag),
  //   });
  // };

  const handleSelectFiles = (files: FileList | null) => {
    if (!files) {
      ingestionForm.setValues({
        ...ingestionForm.values,
        files: [],
      });
      return;
    }

    // Convert FileList to Array and filter only PDF files
    const fileArray = Array.from(files);
    // const pdfFiles = fileArray.filter(file => file.type === 'application/pdf');
    // Allowed MIME types and extensions
    const allowedTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "application/msword",
      "text/html",
      "application/xml",
      "application/xlsx",
      "application/xls",
      "application/json",
      "video/mp3",
      "image/jpeg",
      "image/png",
      "text/plain",
      "text/markdown",
      "text/csv",
      "application/x-zip-compressed",
      "application/zip",
      "application/vnd.ms-powerpoint",
      "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ];

    const allowedExtensions = [
      ".pdf",
      ".doc",
      ".docx",
      ".html",
      ".xml",
      ".xlsx",
      ".xls",
      ".json",
      ".png",
      ".ppt",
      ".pptx",
      ".mp3",
      ".txt",
      ".md",
      ".csv",
      ".zip",
      ".img",
      ".jpeg",
    ];

    const validFiles = fileArray.filter((file) => {
      const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
      return (
        allowedTypes.includes(file.type) || allowedExtensions.includes(ext)
      );
    });

    if (validFiles.length !== fileArray.length) {
      toast.error(
        "Only supported file types are allowed: PDF, DOCX, HTML, PPTX, PNG, etc."
      );
    }

    if (validFiles.length === 0) {
      toast.error("Please select at least one valid file");
      return;
    }

    ingestionForm.setValues({
      ...ingestionForm.values,
      files: validFiles,
    });

    // 	if (pdfFiles.length !== fileArray.length) {
    // 		toast.error("Only PDF files are allowed");
    // 	}

    // 	if (pdfFiles.length === 0) {
    // 		toast.error("Please select at least one PDF file");
    // 		return;
    // 	}

    // 	ingestionForm.setValues({
    // 		...ingestionForm.values,
    // 		files: pdfFiles,
    // 	});
  };

  const handleRemoveFile = (index: number) => {
    const updatedFiles = ingestionForm.values.files.filter(
      (_, i) => i !== index
    );
    ingestionForm.setValues({
      ...ingestionForm.values,
      files: updatedFiles,
    });

    // Clear the file input if no files remain
    if (updatedFiles.length === 0 && fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSelectCategory = (category: string) => {
    ingestionForm.setValues({
      ...ingestionForm.values,
      category_id: category,
    });
  };

  return (
    <div className="bg-primary-100 rounded-lg border-b border-gray-700 pb-6">
      <h2 className="text-lg text-gray-200 font-medium mb-4">
        Upload PDF Documents
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
            <div className="flex-1">
              <div className="flex flex-col">
                <label className="block text-sm font-medium text-gray-200 mb-2">
                  PDF Documents
                </label>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  // accept=".pdf"
                  accept=".pdf,.doc,.docx,.txt,.md,.csv,.ppt,.pptx,.xlsx,.mp3,.html,.xml,.json,.png,.jpeg,.zip,.img"
                  onChange={(e) => handleSelectFiles(e.target.files)}
                  className="block w-full text-sm text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-gray-700 file:text-gray-200 hover:file:bg-gray-600  border border-gray-600 rounded-md cursor-pointer"
                />
              </div>
            </div>
          </div>

          {/* <div className="xl:flex flex-col sm:flex-row space-y-2 sm:space-y-0 gap-2 items-end">
            <div className="flex-1">
              <TextInput
                label="Tags"
                name="tags"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
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
          </div> */}
        </div>

        {/* Display selected files */}
        {ingestionForm.values.files.length > 0 && (
          <div className="mt-4">
            <h3 className="text-sm font-medium text-gray-200 mb-2">
              Selected Files ({ingestionForm.values.files.length})
            </h3>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {ingestionForm.values.files.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between bg-primary-200 p-2 rounded border border-gray-600"
                >
                  <div className="flex items-center">
                    <svg
                      className="w-4 h-4 text-red-500 mr-2"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span className="text-sm text-gray-200 truncate max-w-xs">
                      {file.name}
                    </span>
                    <span className="text-xs text-gray-400 ml-2">
                      ({(file.size / 1024 / 1024).toFixed(2)} MB)
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveFile(index)}
                    className="text-red-400 hover:text-red-300 p-1"
                    title="Remove file"
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
            </div>
          </div>
        )}

        {/* <div className="flex flex-wrap gap-2 mb-2">
          {ingestionForm.values?.tags?.map((tag: string) => (
            <Chip
              key={tag}
              label={tag}
              removeTag={handleRemoveTag}
              color="blue"
            />
          ))}
        </div> */}

        <Button
          type="submit"
          disabled={isUploading || !isFormValid()}
          className="w-full sm:w-auto"
        >
          {isUploading
            ? "Uploading..."
            : `Upload ${ingestionForm.values.files.length} PDF Document(s)`}
        </Button>
      </form>
    </div>
  );
};

export default LocalFileUpload;
