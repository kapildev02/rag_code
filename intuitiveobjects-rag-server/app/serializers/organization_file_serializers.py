def OrganizationFileEntity(file) -> dict:
    return {
        "id": str(file["_id"]),
        "organization_id": file.get("organization_id"),
        "category_id": file.get("category_id"),
        "filename": file.get("filename"),
        "file_size": file.get("file_size"),
        "mime_type": file.get("mime_type"),
        "file_id": file.get("file_id"),
        "tags": file.get("tags") or [],
        "hash_key": file.get("hash_key"),
        "source_type": file.get("source_type"),
        "current_stage": file.get("current_stage"),
        "status_history": file.get("status_history") or [],
        "created_at": file.get("created_at"),
        "updated_at": file.get("updated_at"),
    }


def OrganizationFileListEntity(files) -> list:
    return [OrganizationFileEntity(file) for file in files]
