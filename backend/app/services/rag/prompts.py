"""Islamic Q&A prompts for the RAG pipeline."""

from typing import List, Optional

from app.services.rag.retriever import RetrievedChunk


SYSTEM_PROMPT_MS = """Anda adalah IlmuAI, pembantu ilmu Islam yang berpengetahuan luas.
Anda menjawab soalan berdasarkan mazhab Syafi'i yang menjadi pegangan majoriti umat Islam di Malaysia.

PERATURAN PENTING:
1. Jawab HANYA berdasarkan sumber yang disediakan dalam konteks
2. WAJIB meletakkan rujukan untuk setiap fakta yang dinyatakan (lihat FORMAT OUTPUT)
3. Jika tiada maklumat dalam sumber, nyatakan "Saya tidak menemui maklumat khusus mengenai perkara ini dalam sumber yang ada"
4. JANGAN membuat-buat maklumat atau menjawab berdasarkan pengetahuan luar
5. Gunakan bahasa yang mudah difahami oleh orang awam
6. Untuk soalan sensitif (perceraian, pusaka, isu kontemporari), ingatkan pengguna untuk merujuk mufti

FORMAT JAWAPAN:
- Mulakan dengan jawapan ringkas
- Berikan penjelasan dengan rujukan
- Akhiri dengan nota jika perlu

Anda bukan mufti dan tidak mengeluarkan fatwa. Anda adalah alat rujukan untuk pendidikan."""


SYSTEM_PROMPT_EN = """You are IlmuAI, a knowledgeable Islamic knowledge assistant.
You answer questions based on the Shafi'i school of thought, which is the predominant madhab in Malaysia.

IMPORTANT RULES:
1. Answer ONLY based on the sources provided in the context
2. You MUST include citations for every fact stated (see OUTPUT FORMAT)
3. If information is not in the sources, state "I could not find specific information about this in the available sources"
4. DO NOT fabricate information or answer based on outside knowledge
5. Use language that is accessible to general readers
6. For sensitive questions (divorce, inheritance, contemporary issues), remind users to consult a mufti

RESPONSE FORMAT:
- Start with a brief answer
- Provide explanation with citations
- End with a note if necessary

You are not a mufti and do not issue fatwas. You are a reference tool for education."""


JSON_OUTPUT_INSTRUCTIONS_MS = """
FORMAT OUTPUT (WAJIB):
Kembalikan output sebagai JSON yang sah SAHAJA (tiada markdown, tiada teks tambahan).
Skema:
{
  "answer": "jawapan penuh dalam Bahasa Malaysia dengan rujukan [1], [2] jika perlu",
  "citations": [1, 3, 5]
}

Peraturan:
- "citations" ialah senarai nombor indeks sumber yang anda gunakan daripada konteks.
- Jika anda tidak boleh menyokong jawapan dengan sumber, pulangkan:
  {"answer": "Saya tidak menemui maklumat khusus mengenai perkara ini dalam sumber yang ada", "citations": []}
"""

JSON_OUTPUT_INSTRUCTIONS_EN = """
OUTPUT FORMAT (REQUIRED):
Return ONLY valid JSON (no markdown, no extra text).
Schema:
{
  "answer": "full answer in English with inline [1], [2] if helpful",
  "citations": [1, 3, 5]
}

Rules:
- "citations" is a list of context indices you used.
- If you cannot support an answer with the sources, return:
  {"answer": "I could not find specific information about this in the available sources", "citations": []}
"""


def get_system_prompt(language: str = "ms", structured: bool = True) -> str:
    """Get system prompt based on language.

    Args:
        language: Language code ('ms' or 'en')
        structured: Whether to require JSON output

    Returns:
        System prompt string
    """
    base = SYSTEM_PROMPT_MS if language == "ms" else SYSTEM_PROMPT_EN
    if not structured:
        return base
    return base + (JSON_OUTPUT_INSTRUCTIONS_MS if language == "ms" else JSON_OUTPUT_INSTRUCTIONS_EN)


def format_chunk_for_context(chunk: RetrievedChunk, index: int) -> str:
    """Format a knowledge chunk for inclusion in context.

    Args:
        chunk: Retrieved knowledge chunk
        index: Citation index (1-based)

    Returns:
        Formatted string for context
    """
    header = _format_source_header(chunk, index)
    content = chunk.text_content

    # Include Arabic text if available
    if chunk.text_arabic:
        content = f"Arabic: {chunk.text_arabic}\n\nTranslation: {content}"

    return f"[{index}] {header}\n{content}"


def _format_source_header(chunk: RetrievedChunk, index: int) -> str:
    """Format header based on source type.

    Args:
        chunk: Knowledge chunk
        index: Citation index

    Returns:
        Formatted header string
    """
    metadata = chunk.metadata

    if chunk.source_type == "quran":
        surah_name = metadata.get("surah_name", "Unknown")
        surah_num = metadata.get("surah_number", "?")
        ayah_start = metadata.get("ayah_start", "?")
        ayah_end = metadata.get("ayah_end", ayah_start)
        if ayah_start == ayah_end:
            return f"Al-Quran - Surah {surah_name} ({surah_num}:{ayah_start})"
        return f"Al-Quran - Surah {surah_name} ({surah_num}:{ayah_start}-{ayah_end})"

    elif chunk.source_type == "hadith":
        collection = metadata.get("collection", "Unknown")
        hadith_num = metadata.get("hadith_number", "?")
        grading = metadata.get("grading", "unknown")
        grading_label = {
            "sahih": "Sahih",
            "hasan": "Hasan",
            "daif": "Da'if",
            "mawdu": "Mawdu'",
        }.get(grading, grading.capitalize())
        return f"{collection} - Hadith #{hadith_num} ({grading_label})"

    elif chunk.source_type == "fiqh":
        madhab = metadata.get("madhab", "shafii").capitalize()
        topic = metadata.get("topic", "General")
        source_book = metadata.get("source_book", "")
        if source_book:
            return f"Fiqh {madhab} - {topic} ({source_book})"
        return f"Fiqh {madhab} - {topic}"

    elif chunk.source_type == "fatwa":
        authority = metadata.get("issuing_authority", "Unknown")
        date = metadata.get("date", "")
        topic = metadata.get("topic", "")
        if date:
            return f"Fatwa {authority} ({date}) - {topic}"
        return f"Fatwa {authority} - {topic}"

    return f"Source #{index}"


def build_user_prompt(
    question: str,
    chunks: List[RetrievedChunk],
    language: str = "ms",
    conversation_history: Optional[List[dict]] = None,
    structured: bool = True,
) -> str:
    """Build user prompt with context from retrieved chunks.

    Args:
        question: User's question
        chunks: Retrieved knowledge chunks
        language: Language code
        conversation_history: Optional previous messages
        structured: Whether to require JSON output

    Returns:
        Formatted user prompt
    """
    # Build context section
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(format_chunk_for_context(chunk, i))

    context = "\n\n---\n\n".join(context_parts)

    # Build conversation history if provided
    history_text = ""
    if conversation_history:
        history_parts = []
        for msg in conversation_history[-4:]:  # Last 4 messages for context
            role = "Pengguna" if msg["role"] == "user" else "IlmuAI"
            if language == "en":
                role = "User" if msg["role"] == "user" else "IlmuAI"
            history_parts.append(f"{role}: {msg['content'][:500]}")
        history_text = "\n".join(history_parts)

    # Build prompt
    if language == "ms":
        prompt = f"""SUMBER RUJUKAN:
{context}

{"SEJARAH PERBUALAN:\n" + history_text + "\n\n" if history_text else ""}SOALAN PENGGUNA:
{question}

Sila jawab soalan di atas berdasarkan sumber rujukan yang disediakan."""
        if structured:
            prompt += "\n\nIngat: Kembalikan output sebagai JSON SAHAJA mengikut skema yang diberi."
        else:
            prompt += "\nPastikan setiap fakta disertakan dengan rujukan [1], [2], dll."
    else:
        prompt = f"""REFERENCE SOURCES:
{context}

{"CONVERSATION HISTORY:\n" + history_text + "\n\n" if history_text else ""}USER QUESTION:
{question}

Please answer the question above based on the reference sources provided."""
        if structured:
            prompt += "\n\nReminder: Return ONLY valid JSON per the required schema."
        else:
            prompt += "\nEnsure every fact is accompanied by citations [1], [2], etc."

    return prompt
