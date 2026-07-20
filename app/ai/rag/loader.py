import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class PDFLoader:
    def load(self, file_path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        try:
            docs = self._load_with_pypdf(file_path)
            if docs:
                return docs
        except Exception as e:
            logger.warning(
                f"pypdf failed: {e}"
            )

        logger.info(
            "pypdf extracted no text, trying PyMuPDF fallback"
        )
        try:
            docs = self._load_with_fitz(file_path)
            if docs:
                return docs
        except ImportError:
            logger.warning("PyMuPDF not installed")
        except Exception as e:
            logger.warning(f"PyMuPDF failed: {e}")

        logger.warning(
            f"Could not extract text from {file_path}. "
            "The PDF may be image-based."
        )
        return []

    def _load_with_pypdf(
        self, file_path: str
    ) -> List[Dict[str, Any]]:
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        documents = []

        for page_num, page in enumerate(
            reader.pages, 1
        ):
            text = page.extract_text()
            if text and text.strip():
                documents.append(
                    {
                        "text": text.strip(),
                        "metadata": {
                            "source": file_path,
                            "page": page_num,
                            "total_pages": len(
                                reader.pages
                            ),
                        },
                    }
                )

        logger.info(
            f"Loaded {len(documents)} pages from {file_path}"
        )
        return documents

    def _load_with_fitz(
        self, file_path: str
    ) -> List[Dict[str, Any]]:
        import fitz

        doc = fitz.open(file_path)
        documents = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text and text.strip():
                documents.append(
                    {
                        "text": text.strip(),
                        "metadata": {
                            "source": file_path,
                            "page": page_num + 1,
                            "total_pages": len(doc),
                        },
                    }
                )

        doc.close()
        logger.info(
            f"Loaded {len(documents)} pages with PyMuPDF from {file_path}"
        )
        return documents

    def load_directory(
        self, directory: str
    ) -> List[Dict[str, Any]]:
        documents = []
        for filename in os.listdir(directory):
            if filename.lower().endswith(".pdf"):
                file_path = os.path.join(
                    directory, filename
                )
                try:
                    docs = self.load(file_path)
                    documents.extend(docs)
                except Exception as e:
                    logger.error(
                        f"Error loading {filename}: {e}"
                    )
        return documents
