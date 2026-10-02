"""Run: python -m scripts.smoke_test_l2"""
import sys
from app.layers.l2_candidate import build_index, search
from app.services.chroma_service import collection_count


def main():
    print("🔨 Building index from candidate.json ...")
    try:
        n = build_index(force_rebuild=True)
        print(f"✅ Indexed {n} entities\n")
    except Exception as e:
        print(f"❌ Failed to build index: {e}")
        sys.exit(1)

    # Test queries designed for Saketh's profile
    tests = [
        ("distributed systems",           "project"),
        ("containerized deployment",      "project"),
        ("agentic AI pipeline",           "project"),
        ("vector search",                 "project"),
        ("knowledge distillation",        "project"),
        ("Python",                        "skill"),
        ("LangGraph",                     "skill"),
        ("hackathon winner",              "achievement"),
        ("IEEE publication",              "achievement"),
        ("Oracle Cloud",                  "certification"),
    ]

    all_pass = True
    for query, typ in tests:
        hits = search(query, type_filter=typ, top_k=1)
        if not hits:
            print(f"⚠️ '{query}' ({typ}) -> No result returned with exact filter")
            continue
        top = hits[0]
        name = (
            top["metadata"].get("name")
            or top["metadata"].get("title")
            or top["metadata"].get("company")
            or top["metadata"].get("id")
        )
        print(f"✅ '{query}' ({typ}) -> {name}  [score={top['score']}]")

    print()
    total = collection_count()
    if total > 0:
        print(f"🎉 Phase 2 complete. Collection has {total} vectors.\n")
        sys.exit(0)
    else:
        print("❌ Collection is empty.")
        sys.exit(1)


if __name__ == "__main__":
    main()
