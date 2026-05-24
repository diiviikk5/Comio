"""
COMIO — Comic File Loader
Handles CBZ (ZIP), CBR (RAR) archives — extracts pages on demand.
"""

import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Optional
from natsort import natsorted

from metadata import ComicMetadata, parse_comic_info

# Supported image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif"}


class ComicBook:
    """
    Represents an opened comic book (CBZ or CBR).
    Extracts pages on-demand and provides sequential access.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        self._pages: list[str] = []  # Sorted list of image file names in archive
        self._temp_dir: Optional[str] = None
        self._archive = None
        self._metadata: Optional[ComicMetadata] = None
        self._archive_type: str = ""  # "cbz" or "cbr"

        self._detect_format()
        self._load_page_list()

    def _detect_format(self):
        """Detect the archive format from extension and magic bytes."""
        ext = Path(self.file_path).suffix.lower()
        if ext in (".cbz", ".zip"):
            self._archive_type = "cbz"
        elif ext in (".cbr", ".rar"):
            self._archive_type = "cbr"
        else:
            # Try to detect from magic bytes
            with open(self.file_path, "rb") as f:
                magic = f.read(4)
            if magic[:2] == b"PK":
                self._archive_type = "cbz"
            elif magic[:3] == b"Rar":
                self._archive_type = "cbr"
            else:
                raise ValueError(f"Unsupported comic format: {ext}")

    def _load_page_list(self):
        """Load the list of image pages from the archive."""
        if self._archive_type == "cbz":
            self._load_cbz_pages()
        elif self._archive_type == "cbr":
            self._load_cbr_pages()

    def _load_cbz_pages(self):
        """Load page list from a CBZ (ZIP) file."""
        try:
            with zipfile.ZipFile(self.file_path, "r") as zf:
                all_files = zf.namelist()

                # Extract metadata if available
                for name in all_files:
                    if os.path.basename(name).lower() == "comicinfo.xml":
                        try:
                            xml_data = zf.read(name)
                            self._metadata = parse_comic_info(xml_data)
                        except Exception:
                            pass
                        break

                # Filter image files and sort naturally
                image_files = [
                    f for f in all_files
                    if Path(f).suffix.lower() in IMAGE_EXTENSIONS
                    and not os.path.basename(f).startswith(".")
                    and "__MACOSX" not in f
                ]
                self._pages = natsorted(image_files)
        except zipfile.BadZipFile:
            raise ValueError(f"Corrupted or invalid CBZ file: {self.file_path}")

    def _load_cbr_pages(self):
        """Load page list from a CBR (RAR) file."""
        try:
            import rarfile
            with rarfile.RarFile(self.file_path, "r") as rf:
                all_files = rf.namelist()

                # Extract metadata if available
                for name in all_files:
                    if os.path.basename(name).lower() == "comicinfo.xml":
                        try:
                            xml_data = rf.read(name)
                            self._metadata = parse_comic_info(xml_data)
                        except Exception:
                            pass
                        break

                # Filter image files and sort naturally
                image_files = [
                    f for f in all_files
                    if Path(f).suffix.lower() in IMAGE_EXTENSIONS
                    and not os.path.basename(f).startswith(".")
                ]
                self._pages = natsorted(image_files)
        except ImportError:
            raise ImportError(
                "rarfile package is required for CBR support. "
                "Install it with: pip install rarfile\n"
                "You also need UnRAR: https://www.rarlab.com/rar_add.htm"
            )
        except Exception as e:
            raise ValueError(f"Error reading CBR file: {e}")

    @property
    def page_count(self) -> int:
        """Total number of pages."""
        return len(self._pages)

    @property
    def metadata(self) -> ComicMetadata:
        """Get comic metadata."""
        if self._metadata is None:
            self._metadata = ComicMetadata()
        # Fill in file-level info
        self._metadata.file_path = self.file_path
        self._metadata.file_size = self.file_size
        if self._metadata.page_count == 0:
            self._metadata.page_count = self.page_count
        if self._metadata.title == "Unknown":
            # Use filename as fallback title
            self._metadata.title = Path(self.file_path).stem
        return self._metadata

    def _ensure_temp_dir(self):
        """Create a temp directory for extracted pages."""
        if self._temp_dir is None:
            self._temp_dir = tempfile.mkdtemp(prefix="comio_")

    def get_page_path(self, page_index: int) -> Optional[str]:
        """
        Get the file path for a specific page, extracting it if needed.
        
        Args:
            page_index: Zero-based page index.
            
        Returns:
            Absolute path to the extracted page image, or None if invalid.
        """
        if page_index < 0 or page_index >= self.page_count:
            return None

        self._ensure_temp_dir()
        page_name = self._pages[page_index]

        # Create a safe filename
        safe_name = f"page_{page_index:05d}{Path(page_name).suffix}"
        output_path = os.path.join(self._temp_dir, safe_name)

        # Only extract if not already cached
        if not os.path.exists(output_path):
            self._extract_page(page_name, output_path)

        return output_path

    def _extract_page(self, archive_name: str, output_path: str):
        """Extract a single page from the archive."""
        if self._archive_type == "cbz":
            with zipfile.ZipFile(self.file_path, "r") as zf:
                data = zf.read(archive_name)
                with open(output_path, "wb") as f:
                    f.write(data)
        elif self._archive_type == "cbr":
            import rarfile
            with rarfile.RarFile(self.file_path, "r") as rf:
                data = rf.read(archive_name)
                with open(output_path, "wb") as f:
                    f.write(data)

    def get_cover_path(self) -> Optional[str]:
        """Get the path to the cover (first page) image."""
        return self.get_page_path(0)

    def preload_pages(self, start: int, count: int = 3):
        """
        Preload a range of pages for smoother navigation.
        
        Args:
            start: Starting page index.
            count: Number of pages to preload.
        """
        for i in range(start, min(start + count, self.page_count)):
            self.get_page_path(i)

    def close(self):
        """Clean up temporary files."""
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
            except OSError:
                pass
            self._temp_dir = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()

    def __repr__(self) -> str:
        return f"ComicBook('{self.file_name}', pages={self.page_count})"
