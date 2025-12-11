import React, { useEffect } from "react";
import { Button } from "@/components/atoms/Button/Button";
import { TextInput } from "@/components/atoms/TextInput";
import useFormValidation from "@/hooks/useFormValidation";
import { orgCreateCategoryApi, orgDeleteCategoryApi, orgGetCategoriesApi } from "@/services/adminApi";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { TrashIcon } from "@/components/atoms/Icon/Trash";
import { confirmAction, showSuccess, showError } from "@/utils/sweetAlert";
import { ResponsiveTable } from "@/components/atoms/ResponsiveTable/ResponsiveTable";
import { toast } from "react-hot-toast";
import { Plus, Trash2, Tag } from "lucide-react";
import { motion } from "framer-motion";
import { useState } from "react";

const initialCategoryFormState = {
	name: "",
	tags: [] as string[],
};

export const CategoryTab = () => {
	const dispatch = useAppDispatch();
	const categories = useAppSelector((state) => state.admin.categories);
	const isLoading = useAppSelector((state) => state.admin.loading);
	const categoryForm = useFormValidation(initialCategoryFormState, validateCategoryForm);
	const [tagsInput, setTagsInput] = useState("");

	const handleAddCategory = () => {
		const category = {
			name: categoryForm.values.name,
			tags: categoryForm.values.tags.filter(tag => tag.trim().length > 0)
		};
		
		dispatch(orgCreateCategoryApi(category)).then((response) => {
			if (response.meta.requestStatus === "fulfilled") {
				toast.success("Category added successfully!");
				categoryForm.onReset();
				dispatch(orgGetCategoriesApi());
			} else {
				toast.error("Failed to add category, or category already exists.");
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

	const columns = [
		{
			key: "name",
			header: "Category Name",
			render: (value: string) => (
				<div className="flex items-center gap-2">
					<div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
						<Tag className="w-4 h-4 text-primary-600 dark:text-primary-400" />
					</div>
					<span className="font-medium text-gray-900 dark:text-white">{value}</span>
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
								<motion.span
									key={index}
									initial={{ scale: 0.8, opacity: 0 }}
									animate={{ scale: 1, opacity: 1 }}
									className="bg-accent-100 dark:bg-accent-900/30 text-accent-700 dark:text-accent-300 text-xs font-semibold px-3 py-1 rounded-full"
								>
									{tag}
								</motion.span>
							))
						) : (
							<span className="text-gray-500 dark:text-gray-400 text-sm">No tags</span>
						)}
					</div>
				);
			},
		},
		{
			key: "id",
			header: "Actions",
			className: "text-right",
			render: (id: string) => (
				<motion.button
					whileHover={{ scale: 1.1 }}
					whileTap={{ scale: 0.95 }}
					onClick={() => handleRemoveCategory(id)}
					className="p-2 text-red-600 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors"
				>
					<Trash2 className="w-4 h-4" />
				</motion.button>
			),
		},
	];

	const handleTagBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const cleanTags = e.target.value
      .split(",")
      .map(tag => tag.trim())
      .filter(tag => tag.length > 0);

    categoryForm.setValues({
      ...categoryForm.values,
      tags: cleanTags,
    });
  };
	return (
		<motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
			<div className="mb-8">
				<h1 className="text-3xl font-bold gradient-text mb-2">Category Management</h1>
				<p className="text-gray-600 dark:text-gray-400">Create and manage document categories</p>
			</div>

			{/* Add Category Form */}
			<div className="card mb-8">
				<h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
					<Plus className="w-5 h-5 text-primary-500" />
					Add New Category
				</h2>

				<div className="space-y-4">
					<div>
						<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Category Name
						</label>
						<TextInput
							type="text"
							name="name"
							error={categoryForm.errors.name}
							value={categoryForm.values.name}
							onChange={(e) => categoryForm.handleChange(e)}
							placeholder="e.g., Financial Reports"
						/>
					</div>

					<div>
            <label className="block text-sm font-medium mb-2">Tags (Comma separated)</label>
            <TextInput
              type="text"
              name="tags"
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
              onBlur={handleTagBlur}
              placeholder="e.g., finance, quarterly, 2024"
            />
          </div>

					<Button
						onClick={() => categoryForm.handleSubmit(handleAddCategory)}
						disabled={!categoryForm.values.name.trim()}
						className="w-full btn-primary"
					>
						<Plus className="w-4 h-4 mr-2" />
						Add Category
					</Button>
				</div>
			</div>

			{/* Categories Table */}
			<div>
				<h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">All Categories</h2>
				<ResponsiveTable columns={columns} data={categories} emptyMessage="No categories yet" isLoading={isLoading} />
			</div>
		</motion.div>
	);
};

const validateCategoryForm = (values: typeof initialCategoryFormState) => {
	const errors: Record<string, string> = {};
	if (!values.name.trim()) {
		errors.name = "Category name is required";
	}
	return errors;
};






