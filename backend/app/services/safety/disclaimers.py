"""Disclaimer service for sensitive Islamic topics."""

from typing import Optional

# Disclaimers in Malay and English for different topic types
DISCLAIMERS = {
    "aqidah": {
        "ms": """**Peringatan Penting:** Soalan ini berkaitan dengan akidah Islam.
Untuk pemahaman yang tepat dan mendalam, sila rujuk kepada ulama yang berkelayakan.
Jawapan ini bersifat umum untuk tujuan pendidikan dan tidak menggantikan nasihat ulama.""",
        "en": """**Important Notice:** This question relates to Islamic creed (aqidah).
For proper and in-depth understanding, please consult qualified scholars.
This answer is general in nature for educational purposes and does not replace scholarly guidance.""",
    },
    "fiqh_munakahat": {
        "ms": """**Nota Penting:** Soalan ini berkaitan dengan hukum kekeluargaan Islam.
Untuk kes-kes khusus yang melibatkan situasi peribadi anda, sila rujuk kepada mufti negeri atau pihak berkuasa agama yang berkenaan.
Setiap kes mungkin mempunyai pertimbangan yang berbeza.""",
        "en": """**Important Note:** This question relates to Islamic family law.
For specific cases involving your personal situation, please consult your state mufti or relevant religious authority.
Each case may have different considerations.""",
    },
    "fiqh_jinayat": {
        "ms": """**Amaran:** Soalan ini berkaitan dengan hukum jenayah Islam (hudud/qisas).
Perbincangan ini adalah untuk tujuan akademik sahaja.
Pelaksanaan hukum jenayah Islam adalah bidang kuasa pihak berkuasa agama dan mahkamah syariah.
Sila rujuk pakar undang-undang syariah untuk sebarang pertanyaan lanjut.""",
        "en": """**Warning:** This question relates to Islamic criminal law (hudud/qisas).
This discussion is for academic purposes only.
Implementation of Islamic criminal law falls under the jurisdiction of religious authorities and Syariah courts.
Please consult Syariah legal experts for further inquiries.""",
    },
    "contemporary": {
        "ms": """**Perhatian:** Ini adalah isu kontemporari yang mungkin mempunyai pelbagai pandangan dalam kalangan ulama.
Sila rujuk fatwa rasmi dari JAKIM atau majlis agama negeri anda untuk pendirian rasmi.
Pandangan yang diberikan adalah berdasarkan sumber yang ada dan mungkin tidak merangkumi semua pendapat.""",
        "en": """**Attention:** This is a contemporary issue where scholarly opinions may vary.
Please refer to official fatwas from JAKIM or your state religious council for the official position.
The views provided are based on available sources and may not encompass all opinions.""",
    },
    "interfaith": {
        "ms": """**Amaran Penting:** Topik perbandingan agama memerlukan kepekaan yang tinggi.
Jawapan ini bertujuan untuk pendidikan dan pemahaman sahaja, bukan untuk perdebatan.
Untuk dialog antara agama yang produktif, sila libatkan pakar yang bertauliah dari kedua-dua pihak.""",
        "en": """**Important Warning:** Comparative religion topics require high sensitivity.
This answer is intended for education and understanding only, not for debate.
For productive interfaith dialogue, please involve qualified experts from all sides.""",
    },
    "default": {
        "ms": """**Nota:** Jawapan ini berdasarkan sumber-sumber yang disediakan dan bertujuan untuk pendidikan.
Untuk keputusan hukum yang mengikat dalam situasi peribadi anda, sila rujuk ulama atau mufti tempatan.""",
        "en": """**Note:** This answer is based on the provided sources and is intended for educational purposes.
For binding religious rulings in your personal situation, please consult local scholars or muftis.""",
    },
}

# Standard footer reminder
FOOTER_REMINDER = {
    "ms": "\n\n_IlmuAI adalah alat rujukan pendidikan, bukan pengganti nasihat ulama._",
    "en": "\n\n_IlmuAI is an educational reference tool, not a substitute for scholarly advice._",
}


class DisclaimerService:
    """Service for generating appropriate disclaimers based on topic sensitivity."""

    def get_disclaimer(
        self,
        disclaimer_type: Optional[str],
        language: str = "ms",
        include_footer: bool = True,
    ) -> str:
        """Get appropriate disclaimer based on topic type and language.

        Args:
            disclaimer_type: Type of disclaimer needed (topic name or None)
            language: Language code ('ms' or 'en')
            include_footer: Whether to include the standard footer reminder

        Returns:
            Formatted disclaimer string
        """
        # Get disclaimer for the topic type, fall back to default
        if disclaimer_type and disclaimer_type in DISCLAIMERS:
            disclaimer_dict = DISCLAIMERS[disclaimer_type]
        else:
            disclaimer_dict = DISCLAIMERS["default"]

        # Get language-specific text, fall back to English
        disclaimer = disclaimer_dict.get(language, disclaimer_dict["en"])

        # Add footer if requested
        if include_footer:
            footer = FOOTER_REMINDER.get(language, FOOTER_REMINDER["en"])
            disclaimer += footer

        return disclaimer

    def should_add_disclaimer(
        self,
        topics: list,
        sensitivity_level: str,
    ) -> bool:
        """Determine if a disclaimer should be added.

        Args:
            topics: List of detected topics
            sensitivity_level: Sensitivity level string

        Returns:
            True if disclaimer should be added
        """
        return sensitivity_level in ["high", "critical"]

    def get_educational_note(self, language: str = "ms") -> str:
        """Get a standard educational note.

        Args:
            language: Language code

        Returns:
            Educational note string
        """
        notes = {
            "ms": "Jawapan ini disediakan untuk tujuan pembelajaran dan rujukan umum.",
            "en": "This answer is provided for learning and general reference purposes.",
        }
        return notes.get(language, notes["en"])
