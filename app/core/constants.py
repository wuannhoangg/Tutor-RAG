"""
Constants used throughout the application.
"""

# Document source types
SOURCE_TYPE_PDF = "pdf"
SOURCE_TYPE_DOCX = "docx"
SOURCE_TYPE_SLIDES = "slides"
SOURCE_TYPE_TXT = "txt"
SOURCE_TYPE_MD = "markdown"

# Chunk content types
CHUNK_TYPE_DEFINITION = "definition"
CHUNK_TYPE_PARAGRAPH = "paragraph"
CHUNK_TYPE_HEADING = "heading"
CHUNK_TYPE_EXAMPLE = "example"

# Default user ID
SYSTEM_USER_ID = "system_user"

__all__ = [
    "SOURCE_TYPE_PDF",
    "SOURCE_TYPE_DOCX",
    "SOURCE_TYPE_SLIDES",
    "SOURCE_TYPE_TXT",
    "SOURCE_TYPE_MD",
    "CHUNK_TYPE_DEFINITION",
    "CHUNK_TYPE_PARAGRAPH",
    "CHUNK_TYPE_HEADING",
    "CHUNK_TYPE_EXAMPLE",
    "SYSTEM_USER_ID",
]