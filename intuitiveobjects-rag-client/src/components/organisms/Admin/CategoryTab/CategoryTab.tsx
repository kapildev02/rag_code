import { useEffect } from "react";
import { Button } from "@/components/atoms/Button/Button";
import { TextInput } from "@/components/atoms/TextInput";
import useFormValidation from "@/hooks/useFormValidation";
import { orgCreateCategoryApi, orgDeleteCategoryApi, orgGetCategoriesApi } from "@/services/adminApi";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { TrashIcon } from "@/components/atoms/Icon/Trash";
import { confirmAction, showSuccess, showError } from "@/utils/sweetAlert";
import { ResponsiveTable } from "@/components/atoms/ResponsiveTable/ResponsiveTable";
import { toast } from "react-hot-toast";

const initialCategoryFormState = {
	name: "",
	tags: [] as string[], // Explicitly type as string array
};

export const CategoryTab = () => {
	const dispatch = useAppDispatch();
	const categories = useAppSelector((state) => state.admin.categories);
	const isLoading = useAppSelector((state) => state.admin.loading);

	const categoryForm = useFormValidation(initialCategoryFormState, validateCategoryForm);

	const handleAddCategory = () => {
		// Ensure tags are properly formatted before sending
		const category = {
			name: categoryForm.values.name,
			tags: categoryForm.values.tags.filter(tag => tag.trim().length > 0) // Filter out empty tags
		};
		
		dispatch(orgCreateCategoryApi(category)).then((response) => {
			if (response.meta.requestStatus === "fulfilled") {
				toast.success("Category added!");
				categoryForm.onReset();
				// Refresh categories list
				dispatch(orgGetCategoriesApi());
			} else {
				toast.error("Failed to add category, or category may already exist.");
			}
		});
	};

	const handleRemoveCategory = (id: string) => {
		confirmAction("Are you sure?", "You won't be able to revert this!", "Yes, delete it!").then((result) => {
			if (result.isConfirmed) {
				dispatch(orgDeleteCategoryApi(id)).then((response) => {
					if (response.meta.requestStatus === "fulfilled") {
						showSuccess("Deleted!", "Category has been deleted.");
					} else {
						showError("Error!", "Failed to delete category.");
					}
				});
			}
		});
	};

	useEffect(() => {
		dispatch(orgGetCategoriesApi());
	}, []);

	// Define columns for the responsive table
	const columns = [
		{
			key: "name",
			header: "Category Name",
			render: (value: string) => (
				<div className="flex items-center">
					<div className="text-sm font-medium text-gray-400 truncate max-w-xs">{value}</div>
				</div>
			),
		},

		{
			key: "tags",
			header: "Tags",
			render: (tags?: string[]) => {
            const safeTags = tags ?? [];
            return (
                 <div className="flex flex-wrap gap-2">
                 {safeTags.length > 0 ? (
                 safeTags.map((tag, index) => (
                 <span
                   key={index}
                   className="bg-blue-100 text-blue-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded dark:bg-blue-200 dark:text-blue-800">
                   {tag}
                 </span>
                ))
               ) : (
               <span className="text-gray-500 text-sm">No tags</span>
      )}
    </div>
  );
}

		},
		{
			key: "id",
			header: "Actions",
			className: "text-right",
			render: (id: string) => (
				<button onClick={() => handleRemoveCategory(id)} className="text-red-600 hover:text-red-900 focus:outline-none">
					<TrashIcon />
				</button>
			),
		},
	];

	const handleTagChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		const tagInput = e.target.value;
		
		// Allow commas to be typed by storing raw input
		categoryForm.setValues({
			...categoryForm.values,
			tags: tagInput.split('/').map(tag => tag.trim()).filter(Boolean)
		});
	};

	return (
		<>
			<h1 className="text-2xl font-semibold text-white mb-6">Category Management</h1>
			<div className="mb-8">
				<div className="flex flex-col sm:flex-row gap-4 sm:items-end">
					<div className="flex-1">
						<TextInput
							label="Category Name"
							type="text"
							name="name"
							error={categoryForm.errors.name}
							value={categoryForm.values.name}
							onChange={(e) => categoryForm.handleChange(e)}
							placeholder="New category name"
						/>
					</div>
					<div className="flex-1">
						<TextInput
							label="Tags (Comma separated)"
							type="text"
							name="tags"
							value={categoryForm.values.tags.join(',')}
							onChange={handleTagChange}
							onBlur={(e) => {
								// Clean up tags on blur
								const cleanTags = e.target.value
									.split(',')
									.map(tag => tag.trim())
									.filter(tag => tag.length > 0);
								categoryForm.setValues({
									...categoryForm.values,
									tags: cleanTags
								});
							}}
							placeholder="e.g., tag_1, tag_2,tag_3"
						/>
					</div>
					<Button
						onClick={() => categoryForm.handleSubmit(handleAddCategory)}
						disabled={!categoryForm.values.name.trim()}
						className="w-full sm:w-auto">
						Add Category
					</Button>
				</div>
			</div>

			<div className="space-y-4">
				<ResponsiveTable columns={columns} data={categories} emptyMessage="No categories added yet" isLoading={isLoading} />
			</div>
		</>
	);
};

// Update form validation
const validateCategoryForm = (values: typeof initialCategoryFormState) => {
	const errors: Record<string, string> = {};
	
	if (!values.name.trim()) {
		errors.name = "Category name is required";
	}
	
	// Optional: validate tags
	if (values.tags.some(tag => tag.trim().length === 0)) {
		errors.tags = "Tags cannot be empty";
	}
	
	return errors;
};






