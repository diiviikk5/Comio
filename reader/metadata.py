"""
COMIO — ComicInfo.xml Parser & Metadata Model
Reads comic metadata from ComicInfo.xml found inside CBZ/CBR archives.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class ComicMetadata:
    """Represents metadata for a comic book."""
    title: str = "Unknown"
    series: str = ""
    number: str = ""
    volume: str = ""
    summary: str = ""
    publisher: str = ""
    genre: str = ""
    page_count: int = 0
    year: Optional[int] = None
    month: Optional[int] = None
    writer: str = ""
    penciller: str = ""
    inker: str = ""
    colorist: str = ""
    letterer: str = ""
    cover_artist: str = ""
    editor: str = ""
    language: str = ""
    format: str = ""
    manga: str = "No"  # "Yes", "No", "YesAndRightToLeft"
    characters: str = ""
    teams: str = ""
    locations: str = ""
    web: str = ""
    notes: str = ""

    # Non-ComicInfo fields (app-specific)
    file_path: str = ""
    file_size: int = 0
    cover_image_path: str = ""
    read_progress: int = 0  # Last page read
    is_read: bool = False
    date_added: str = ""
    tags: list = field(default_factory=list)

    @property
    def display_title(self) -> str:
        """Generate a display-friendly title."""
        if self.series and self.number:
            return f"{self.series} #{self.number}"
        if self.series:
            return self.series
        return self.title

    @property
    def creators(self) -> str:
        """Get a combined creator string."""
        parts = []
        if self.writer:
            parts.append(f"Writer: {self.writer}")
        if self.penciller:
            parts.append(f"Art: {self.penciller}")
        return " | ".join(parts) if parts else "Unknown Creator"

    @property
    def is_manga(self) -> bool:
        """Check if this comic should be read right-to-left."""
        return self.manga in ("Yes", "YesAndRightToLeft")


def parse_comic_info(xml_content: bytes | str) -> ComicMetadata:
    """
    Parse a ComicInfo.xml file content into a ComicMetadata object.
    
    Args:
        xml_content: Raw XML content as bytes or string.
        
    Returns:
        ComicMetadata with parsed fields.
    """
    metadata = ComicMetadata()

    try:
        if isinstance(xml_content, bytes):
            xml_content = xml_content.decode("utf-8", errors="replace")
        
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        return metadata

    # Map XML element names to dataclass field names
    field_map = {
        "Title": "title",
        "Series": "series",
        "Number": "number",
        "Volume": "volume",
        "Summary": "summary",
        "Publisher": "publisher",
        "Genre": "genre",
        "PageCount": "page_count",
        "Year": "year",
        "Month": "month",
        "Writer": "writer",
        "Penciller": "penciller",
        "Inker": "inker",
        "Colorist": "colorist",
        "Letterer": "letterer",
        "CoverArtist": "cover_artist",
        "Editor": "editor",
        "LanguageISO": "language",
        "Format": "format",
        "Manga": "manga",
        "Characters": "characters",
        "Teams": "teams",
        "Locations": "locations",
        "Web": "web",
        "Notes": "notes",
    }

    int_fields = {"page_count", "year", "month"}

    for xml_name, field_name in field_map.items():
        elem = root.find(xml_name)
        if elem is not None and elem.text:
            value = elem.text.strip()
            if field_name in int_fields:
                try:
                    setattr(metadata, field_name, int(value))
                except ValueError:
                    pass
            else:
                setattr(metadata, field_name, value)

    return metadata


def parse_comic_info_file(file_path: str | Path) -> ComicMetadata:
    """
    Parse a ComicInfo.xml file from disk.
    
    Args:
        file_path: Path to the ComicInfo.xml file.
        
    Returns:
        ComicMetadata with parsed fields.
    """
    path = Path(file_path)
    if not path.exists():
        return ComicMetadata()
    
    return parse_comic_info(path.read_bytes())
