"""
COMIO — Internet Archive Client
Search, browse, and download free/public domain comics from the Internet Archive.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Generator
from PyQt6.QtCore import QThread, pyqtSignal


@dataclass
class IAComic:
    """Represents a comic item from the Internet Archive."""
    identifier: str = ""
    title: str = ""
    creator: str = ""
    date: str = ""
    description: str = ""
    subject: str = ""
    publisher: str = ""
    collection: str = ""
    mediatype: str = ""
    downloads: int = 0
    thumbnail_url: str = ""
    details_url: str = ""
    
    # File info (populated when item details are fetched)
    files: list = field(default_factory=list)
    
    @property
    def ia_url(self) -> str:
        return f"https://archive.org/details/{self.identifier}"
    
    @property
    def thumbnail(self) -> str:
        if self.thumbnail_url:
            return self.thumbnail_url
        return f"https://archive.org/services/img/{self.identifier}"

    def get_download_url(self, filename: str) -> str:
        import urllib.parse
        quoted_filename = urllib.parse.quote(filename)
        return f"https://archive.org/download/{self.identifier}/{quoted_filename}"

    def get_cbz_files(self) -> list[dict]:
        """Get all CBZ/ZIP files for this item."""
        return [
            f for f in self.files
            if f.get("name", "").lower().endswith((".cbz", ".zip"))
        ]
    
    def get_best_download(self) -> Optional[dict]:
        """Get the best file to download (prefer CBZ > ZIP > PDF)."""
        cbz = [f for f in self.files if f.get("name", "").lower().endswith(".cbz")]
        if cbz:
            return cbz[0]
        
        zips = [f for f in self.files if f.get("name", "").lower().endswith(".zip")]
        if zips:
            return zips[0]
        
        pdfs = [f for f in self.files if f.get("name", "").lower().endswith(".pdf")]
        if pdfs:
            return pdfs[0]
        
        return None


class IASearchThread(QThread):
    """Background thread for searching Internet Archive."""
    results_ready = pyqtSignal(list)   # list of IAComic
    error_occurred = pyqtSignal(str)
    search_started = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._query = ""
        self._max_results = 20
        self._sort = "downloads desc"
    
    def search(self, query: str, max_results: int = 20, sort: str = "downloads desc"):
        """Start a search in the background."""
        self._query = query
        self._max_results = max_results
        self._sort = sort
        self.start()
    
    def run(self):
        self.search_started.emit()
        try:
            import internetarchive as ia
            
            # Build search query — always filter to comics collection
            search_query = f"collection:comics AND mediatype:texts"
            if self._query:
                search_query += f" AND ({self._query})"
            
            results = []
            search = ia.search_items(
                search_query,
                fields=[
                    "identifier", "title", "creator", "date",
                    "description", "subject", "publisher",
                    "collection", "downloads"
                ],
                sorts=[self._sort],
            )
            
            count = 0
            for item_data in search:
                if count >= self._max_results:
                    break
                
                comic = IAComic(
                    identifier=item_data.get("identifier", ""),
                    title=item_data.get("title", "Unknown"),
                    creator=self._flatten(item_data.get("creator", "")),
                    date=item_data.get("date", ""),
                    description=str(item_data.get("description", ""))[:500],
                    subject=self._flatten(item_data.get("subject", "")),
                    publisher=self._flatten(item_data.get("publisher", "")),
                    collection=self._flatten(item_data.get("collection", "")),
                    downloads=int(item_data.get("downloads", 0)),
                )
                results.append(comic)
                count += 1
            
            self.results_ready.emit(results)
            
        except ImportError:
            self.error_occurred.emit(
                "internetarchive package not installed.\n"
                "Install with: pip install internetarchive"
            )
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    @staticmethod
    def _flatten(value) -> str:
        """Flatten a value that might be a list into a string."""
        if isinstance(value, list):
            return ", ".join(str(v) for v in value)
        return str(value) if value else ""


class IAItemDetailsThread(QThread):
    """Fetch detailed file list for an IA item."""
    details_ready = pyqtSignal(str, list)  # identifier, files
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._identifier = ""
    
    def fetch(self, identifier: str):
        self._identifier = identifier
        self.start()
    
    def run(self):
        try:
            import internetarchive as ia
            
            item = ia.get_item(self._identifier)
            files = []
            for f in item.files:
                files.append({
                    "name": f.get("name", ""),
                    "size": int(f.get("size", 0)),
                    "format": f.get("format", ""),
                    "source": f.get("source", ""),
                })
            
            self.details_ready.emit(self._identifier, files)
            
        except Exception as e:
            self.error_occurred.emit(f"Error fetching details for {self._identifier}: {e}")


# Pre-configured collection searches
COLLECTIONS = {
    "Popular Comics": "collection:comics AND mediatype:texts",
    "Golden Age": "collection:comics AND mediatype:texts AND date:[1930 TO 1956]",
    "Silver Age": "collection:comics AND mediatype:texts AND date:[1956 TO 1970]",
    "Comic Books": "collection:comic_books AND mediatype:texts",
    "Fan Comics": "collection:comic_fanzines AND mediatype:texts",
    "Open Source": "collection:opensource_comics AND mediatype:texts",
}
