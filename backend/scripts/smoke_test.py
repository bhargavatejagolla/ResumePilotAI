"""Run: python -m scripts.smoke_test"""
import sys
from app.services.groq_service import chat_json
from app.services.embedding_service import embed_one
from app.services.chroma_service import get_collection


def check(name: str, fn):
    try:
        result = fn()
        print(f"✅ {name}: {result}")
        return True
    except Exception as e:
        print(f"❌ {name}: {e}")
        return False


def main():
    print("\n🔍 Running ResumePilot AI Phase 0 Smoke Tests...")
    ok = True
    ok &= check("Embeddings (all-MiniLM-L6-v2)", lambda: f"dim={len(embed_one('hello world'))}")
    ok &= check("Chroma persistent collection", lambda: get_collection().name)
    ok &= check("Groq JSON mode", lambda: chat_json(
        'Return exactly this JSON: {"ok": true, "model": "groq"}'
    ))

    if ok:
        print("\n🎉 Phase 0 backend is fully operational.\n")
        sys.exit(0)
    else:
        print("\n⚠️ Note: If Groq failed, please make sure your valid GROQ_API_KEY is set in backend/.env")
        print("Embeddings and Chroma are working locally.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
