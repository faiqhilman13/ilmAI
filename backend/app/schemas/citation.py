"""Citation schemas for Islamic sources."""

from typing import Optional, Literal, Union
from pydantic import BaseModel


class BaseCitation(BaseModel):
    """Base citation schema."""

    index: int
    source_type: Literal["quran", "hadith", "fiqh", "fatwa"]
    text_snippet: str


class QuranCitation(BaseCitation):
    """Quran citation with ayah details."""

    source_type: Literal["quran"] = "quran"
    surah_number: int
    surah_name: str
    ayah_start: int
    ayah_end: Optional[int] = None
    arabic_text: Optional[str] = None
    translation: Optional[str] = None


class HadithCitation(BaseCitation):
    """Hadith citation with collection and grading."""

    source_type: Literal["hadith"] = "hadith"
    collection: str  # e.g., "Sahih al-Bukhari"
    hadith_number: str
    grading: Literal["sahih", "hasan", "daif", "mawdu"]
    book_name: Optional[str] = None
    narrator_chain: Optional[str] = None


class FiqhCitation(BaseCitation):
    """Fiqh citation with madhab details."""

    source_type: Literal["fiqh"] = "fiqh"
    madhab: str  # e.g., "shafii"
    topic: str
    source_book: Optional[str] = None
    scholar: Optional[str] = None
    evidence: Optional[str] = None


class FatwaCitation(BaseCitation):
    """Fatwa citation from religious authorities."""

    source_type: Literal["fatwa"] = "fatwa"
    issuing_authority: str  # e.g., "JAKIM"
    fatwa_number: Optional[str] = None
    date: Optional[str] = None
    topic: str


# Union type for all citations
Citation = Union[QuranCitation, HadithCitation, FiqhCitation, FatwaCitation]
