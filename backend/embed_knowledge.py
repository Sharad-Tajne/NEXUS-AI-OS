from database import SessionLocal
import models

from rag import create_embedding


# =========================================================
# DATABASE SESSION
# =========================================================

db = SessionLocal()


try:

    knowledge_items = (
        db.query(models.KnowledgeItem)
        .order_by(models.KnowledgeItem.id.asc())
        .all()
    )

    print(
        f"Found {len(knowledge_items)} knowledge items."
    )

    if not knowledge_items:

        print("No knowledge items found.")

    else:

        for item in knowledge_items:

            text = f"""
Title: {item.title}

Category: {item.category}

Source: {item.source or ""}

Content:
{item.content}
""".strip()

            print(
                f"\nCreating embedding for: {item.title}"
            )

            embedding = create_embedding(text)

            item.embedding = embedding

            db.commit()

            print(
                f"✓ Saved {len(embedding)} dimensions "
                f"for: {item.title}"
            )

    print(
        "\nAll knowledge embeddings "
        "saved successfully."
    )


except Exception as error:

    db.rollback()

    print(
        "\nERROR:",
        error
    )


finally:

    db.close()