from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader

def get_loader(file_path: str):
    if file_path.endswith(".txt"):
        return TextLoader(file_path, encoding="utf-8")
    elif file_path.endswith(".pdf"):
        return PyPDFLoader(file_path)
    elif file_path.endswith(".docx"):
        return Docx2txtLoader(file_path)
    else:
        raise ValueError("不支持的文件类型")