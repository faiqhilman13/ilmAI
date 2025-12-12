"""Generate embeddings for processed Islamic knowledge and seed the database.

Usage:
  python backend/scripts/generate_embeddings.py
  python backend/scripts/generate_embeddings.py --path data/processed --batch-size 50

Requires:
  - Postgres + pgvector running (see docker-compose)
  - OPENAI_API_KEY set (even if using Anthropic for chat)
"""

import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Iterable, List

from sqlalchemy import select

from app.core.database import async_session_maker
from app.models.knowledge import KnowledgeChunk, KnowledgeSource
from app.services.llm import get_llm_client

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def iter_processed_files(root: Path) -> Iterable[Path]:
    """Yield processed chunk files.

    By default we only seed files that look like chunk payloads (e.g. *_chunks.json),
    and skip summaries/aux files.
    """
    for path in root.rglob("*.json"):
        if path.name.startswith("."):
            continue
        if not path.name.endswith("_chunks.json"):
            continue
        yield path


def load_items(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        logger.warning(f"Skipping non-list JSON file: {path}")
        return []
    return [item for item in data if isinstance(item, dict)]


async def get_or_create_source(
    db, source_type: str, name: str | None = None, metadata: dict | None = None
) -> KnowledgeSource:
    result = await db.execute(
        select(KnowledgeSource).where(KnowledgeSource.source_type == source_type)
    )
    source = result.scalars().first()
    if source:
        return source
    source = KnowledgeSource(
        source_type=source_type,
        name=name or source_type.title(),
        description=f"Imported {source_type} source",
        source_metadata=metadata or {},
    )
    db.add(source)
    await db.flush()
    return source


async def seed_file(db, llm_client, items: List[dict], batch_size: int) -> int:
    inserted = 0
    texts: List[str] = []
    payloads: List[dict] = []

    async def flush_batch():
        nonlocal inserted, texts, payloads
        if not texts:
            return
        embeddings = await llm_client.generate_embeddings_batch(texts)
        chunks: List[KnowledgeChunk] = []
        for payload, embedding in zip(payloads, embeddings):
            chunks.append(
                KnowledgeChunk(
                    source_id=payload["source_id"],
                    source_type=payload["source_type"],
                    text_content=payload["text_content"],
                    text_arabic=payload.get("text_arabic"),
                    text_translation=payload.get("text_translation"),
                    embedding=embedding,
                    chunk_metadata=payload.get("metadata") or {},
                    chunk_index=payload.get("chunk_index"),
                )
            )
        db.add_all(chunks)
        await db.commit()
        inserted += len(chunks)
        texts = []
        payloads = []

    for item in items:
        source_type = item.get("source_type")
        text_content = item.get("text_content")
        if not source_type or not text_content:
            continue
        metadata = item.get("metadata") or {}
        source_name = metadata.get("source_name") or metadata.get("collection") or source_type.title()
        source = await get_or_create_source(db, source_type, name=source_name)

        payloads.append(
            {
                "source_id": source.id,
                "source_type": source_type,
                "text_content": text_content,
                "text_arabic": item.get("text_arabic"),
                "text_translation": item.get("text_translation"),
                "metadata": metadata,
                "chunk_index": item.get("chunk_index"),
            }
        )
        texts.append(text_content)
        if len(texts) >= batch_size:
            await flush_batch()

    await flush_batch()
    return inserted


async def main(args: argparse.Namespace) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    processed_root = (repo_root / args.path).resolve()
    if not processed_root.exists():
        raise SystemExit(f"Processed path not found: {processed_root}")

    llm_client = get_llm_client()
    total_inserted = 0

    async with async_session_maker() as db:
        for file_path in iter_processed_files(processed_root):
            logger.info(f"Seeding from {file_path.relative_to(repo_root)}")
            try:
                items = load_items(file_path)
                if args.max_items:
                    items = items[: args.max_items]
                inserted = await seed_file(db, llm_client, items, args.batch_size)
                total_inserted += inserted
                logger.info(f"Inserted {inserted} chunks from {file_path.name}")
            except Exception as e:
                logger.error(f"Failed processing {file_path}: {e}")

    logger.info(f"Done. Total inserted chunks: {total_inserted}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        default="data/processed",
        help="Path to processed JSON folder (relative to repo root).",
    )
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument(
        "--max-items",
        type=int,
        default=None,
        help="Max items to seed per file (useful for incremental seeding).",
    )
    asyncio.run(main(parser.parse_args()))
