"""Document formats, collision policies, and conversion configuration models."""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DocFormat(str, Enum):
    """Supported document formats for conversion."""
    MD = "md"
    DOCX = "docx"
    PDF = "pdf"
    RTF = "rtf"
    HTML = "html"

    @classmethod
    def from_extension(cls, ext: str) -> Optional["DocFormat"]:
        """Resolves a file extension (e.g. '.md', 'docx', '.htm') to a DocFormat."""
        if not ext:
            return None
        cleaned = ext.strip().lower().lstrip(".")
        if cleaned in ("htm", "html"):
            return cls.HTML
        if cleaned in ("md", "markdown"):
            return cls.MD
        for member in cls:
            if member.value == cleaned:
                return member
        return None

    @property
    def label(self) -> str:
        """Human-friendly display name for the format."""
        labels = {
            DocFormat.MD: "Markdown (.md)",
            DocFormat.DOCX: "Word (.docx)",
            DocFormat.PDF: "PDF (.pdf)",
            DocFormat.RTF: "Rich Text (.rtf)",
            DocFormat.HTML: "HTML5 (.html)",
        }
        return labels[self]


class CollisionPolicy(str, Enum):
    """Policy for handling existing destination files."""
    OVERWRITE = "OVERWRITE"
    SKIP = "SKIP"
    RENAME = "RENAME"


@dataclass
class ConversionConfig:
    """Batch conversion configuration parameters."""
    target_format: DocFormat = DocFormat.PDF
    output_dir: str = ""
    preserve_folder_tree: bool = True
    collision_policy: CollisionPolicy = CollisionPolicy.RENAME
    max_workers: int = 4
    pdf_page_size: str = "A4"
