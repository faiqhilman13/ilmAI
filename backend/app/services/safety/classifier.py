"""Topic classification and sensitivity detection for Islamic questions."""

from enum import Enum
from typing import List, Tuple


class IslamicTopic(str, Enum):
    """Categories of Islamic topics."""

    AQIDAH = "aqidah"  # Creed/Belief
    FIQH_IBADAH = "fiqh_ibadah"  # Worship rulings (prayer, fasting, etc.)
    FIQH_MUAMALAT = "fiqh_muamalat"  # Transaction rulings
    FIQH_MUNAKAHAT = "fiqh_munakahat"  # Family law (marriage, divorce)
    FIQH_JINAYAT = "fiqh_jinayat"  # Criminal law
    TAFSIR = "tafsir"  # Quran interpretation
    HADITH = "hadith"  # Prophetic traditions
    AKHLAQ = "akhlaq"  # Ethics/Character
    SIRAH = "sirah"  # Prophetic biography
    CONTEMPORARY = "contemporary"  # Modern issues
    INTERFAITH = "interfaith"  # Comparative religion
    GENERAL = "general"  # General Islamic knowledge


class SensitivityLevel(str, Enum):
    """Sensitivity levels for topics."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Topics and their sensitivity levels
TOPIC_SENSITIVITY = {
    IslamicTopic.AQIDAH: SensitivityLevel.HIGH,
    IslamicTopic.FIQH_IBADAH: SensitivityLevel.LOW,
    IslamicTopic.FIQH_MUAMALAT: SensitivityLevel.MEDIUM,
    IslamicTopic.FIQH_MUNAKAHAT: SensitivityLevel.HIGH,
    IslamicTopic.FIQH_JINAYAT: SensitivityLevel.CRITICAL,
    IslamicTopic.TAFSIR: SensitivityLevel.MEDIUM,
    IslamicTopic.HADITH: SensitivityLevel.MEDIUM,
    IslamicTopic.AKHLAQ: SensitivityLevel.LOW,
    IslamicTopic.SIRAH: SensitivityLevel.LOW,
    IslamicTopic.CONTEMPORARY: SensitivityLevel.HIGH,
    IslamicTopic.INTERFAITH: SensitivityLevel.CRITICAL,
    IslamicTopic.GENERAL: SensitivityLevel.LOW,
}

# Keywords for topic classification (Malay and English)
TOPIC_KEYWORDS = {
    IslamicTopic.AQIDAH: [
        "iman", "tauhid", "syirik", "kufur", "akidah", "aqidah",
        "belief", "faith", "shirk", "kufr", "rukun iman",
        "malaikat", "angel", "qada", "qadar", "takdir",
    ],
    IslamicTopic.FIQH_IBADAH: [
        "solat", "sembahyang", "prayer", "salah", "salat",
        "puasa", "fasting", "saum", "sawm",
        "zakat", "zakah",
        "haji", "hajj", "umrah", "umra",
        "wuduk", "wudhu", "wudu", "ablution",
        "tayammum", "ghusl", "mandi wajib", "junub",
        "azan", "adhan", "iqamah", "imam", "makmum",
        "qunut", "sujud", "rukuk", "ruku",
    ],
    IslamicTopic.FIQH_MUAMALAT: [
        "jual beli", "buy sell", "riba", "usury", "interest",
        "hutang", "debt", "loan", "pinjam",
        "perniagaan", "business", "trade",
        "halal", "haram", "makanan", "food",
        "wakaf", "waqf", "hibah", "hadiah", "gift",
    ],
    IslamicTopic.FIQH_MUNAKAHAT: [
        "nikah", "kahwin", "marriage", "perkahwinan",
        "cerai", "talak", "divorce", "talaq",
        "iddah", "idda", "eddah",
        "mahar", "mas kahwin", "dowry",
        "nafkah", "maintenance",
        "poligami", "polygamy",
        "fasakh", "khulu", "khula",
        "rujuk", "reconciliation",
        "wali", "guardian",
    ],
    IslamicTopic.FIQH_JINAYAT: [
        "hudud", "qisas", "diyat",
        "hukuman", "punishment",
        "zina", "adultery", "fornication",
        "mencuri", "steal", "theft",
        "bunuh", "kill", "murder",
    ],
    IslamicTopic.TAFSIR: [
        "tafsir", "tafseer", "interpretation",
        "ayat", "verse", "surah", "sura",
        "makna", "meaning",
        "asbab nuzul", "sebab turun",
    ],
    IslamicTopic.HADITH: [
        "hadis", "hadith", "hadits",
        "sahih", "hasan", "daif", "dhaif", "weak",
        "riwayat", "narration", "sanad", "chain",
        "bukhari", "muslim", "tirmizi", "tirmidhi",
        "sunah", "sunnah",
    ],
    IslamicTopic.AKHLAQ: [
        "akhlak", "akhlaq", "ethics", "moral",
        "adab", "manners", "etiquette",
        "sabar", "patience", "syukur", "gratitude",
        "ikhlas", "sincerity", "tawaduk", "humble",
    ],
    IslamicTopic.SIRAH: [
        "sirah", "seerah", "biography",
        "nabi", "prophet", "rasul", "messenger",
        "sahabat", "companion", "sahaba",
        "hijrah", "hijra", "migration",
    ],
    IslamicTopic.CONTEMPORARY: [
        "vaksin", "vaccine",
        "crypto", "bitcoin", "nft",
        "insurans", "insurance", "takaful",
        "bank", "banking",
        "saham", "stock", "investment",
        "organ", "transplant",
        "euthanasia", "cloning",
        "ai", "artificial intelligence",
        "moden", "modern", "kontemporari", "contemporary",
    ],
    IslamicTopic.INTERFAITH: [
        "agama lain", "other religion",
        "kristian", "christian", "hindu", "buddha", "buddhist",
        "yahudi", "jewish", "jew",
        "perbandingan agama", "comparative religion",
        "dialog", "dialogue",
        "murtad", "apostasy", "apostate",
    ],
}


class TopicClassifier:
    """Classifies Islamic questions into topics and determines sensitivity."""

    def classify(self, query: str) -> List[IslamicTopic]:
        """Classify query into Islamic topics.

        Args:
            query: User's question

        Returns:
            List of detected topics
        """
        query_lower = query.lower()
        detected = []

        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                detected.append(topic)

        # Default to general if no specific topic detected
        if not detected:
            detected = [IslamicTopic.GENERAL]

        return detected

    def check_sensitivity(
        self,
        topics: List[IslamicTopic],
    ) -> Tuple[bool, str | None]:
        """Check if topics require a disclaimer.

        Args:
            topics: List of detected topics

        Returns:
            Tuple of (requires_disclaimer, disclaimer_type)
        """
        highest_sensitivity = SensitivityLevel.LOW
        disclaimer_type = None

        sensitivity_order = [
            SensitivityLevel.LOW,
            SensitivityLevel.MEDIUM,
            SensitivityLevel.HIGH,
            SensitivityLevel.CRITICAL,
        ]

        for topic in topics:
            sensitivity = TOPIC_SENSITIVITY.get(topic, SensitivityLevel.LOW)
            if sensitivity_order.index(sensitivity) > sensitivity_order.index(highest_sensitivity):
                highest_sensitivity = sensitivity
                disclaimer_type = topic.value

        # Require disclaimer for HIGH and CRITICAL sensitivity
        requires_disclaimer = highest_sensitivity in [
            SensitivityLevel.HIGH,
            SensitivityLevel.CRITICAL,
        ]

        return requires_disclaimer, disclaimer_type

    def get_sensitivity_level(self, topics: List[IslamicTopic]) -> SensitivityLevel:
        """Get the highest sensitivity level from topics.

        Args:
            topics: List of topics

        Returns:
            Highest sensitivity level
        """
        sensitivity_order = [
            SensitivityLevel.LOW,
            SensitivityLevel.MEDIUM,
            SensitivityLevel.HIGH,
            SensitivityLevel.CRITICAL,
        ]

        highest = SensitivityLevel.LOW
        for topic in topics:
            sensitivity = TOPIC_SENSITIVITY.get(topic, SensitivityLevel.LOW)
            if sensitivity_order.index(sensitivity) > sensitivity_order.index(highest):
                highest = sensitivity

        return highest
