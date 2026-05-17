"""
Script de configuración inicial del chatbot.
Ejecuta esto UNA VEZ antes de arrancar el bot por primera vez.

Uso:
    python setup.py
"""

import asyncio
import shutil
from pathlib import Path


async def setup():
    print("\n🤖 Configurando el Chatbot Vendedor IA...\n")

    # 1. Crear archivo .env si no existe
    env_path = Path(".env")
    env_example = Path(".env.example")
    if not env_path.exists() and env_example.exists():
        shutil.copy(env_example, env_path)
        print("✅ Archivo .env creado — IMPORTANTE: edita .env con tus tokens reales")
    elif env_path.exists():
        print("✅ Archivo .env ya existe")
    else:
        print("⚠️  No se encontró .env.example — crea .env manualmente")

    # 2. Crear base de datos
    try:
        from database.manager import DatabaseManager
        db = DatabaseManager()
        await db.initialize()
        print("✅ Base de datos creada correctamente")
    except Exception as e:
        print(f"❌ Error creando base de datos: {e}")
        return

    # 3. Verificar archivos de conocimiento
    knowledge_files = [
        "knowledge/products.json",
        "knowledge/faqs.json",
        "knowledge/policies.json",
        "knowledge/style_examples.json",
    ]
    for f in knowledge_files:
        if Path(f).exists():
            print(f"✅ {f} existe")
        else:
            print(f"⚠️  {f} no encontrado")

    # 4. Importar conocimiento inicial a la BD
    try:
        import json
        from core.memory.knowledge_base import KnowledgeManager
        km = KnowledgeManager()

        products_path = Path("knowledge/products.json")
        if products_path.exists():
            with open(products_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            products = [p for p in data.get("products", []) if "Ejemplo" not in p.get("name", "")]
            if products:
                await km.import_products(products)
                print(f"✅ {len(products)} productos importados a la base de datos")

        faqs_path = Path("knowledge/faqs.json")
        if faqs_path.exists():
            with open(faqs_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            faqs = data.get("faqs", [])
            if faqs:
                await km.import_faqs(faqs)
                print(f"✅ {len(faqs)} FAQs importadas a la base de datos")

    except Exception as e:
        print(f"⚠️  Error importando conocimiento: {e}")

    print("\n" + "="*50)
    print("🎉 Configuración completada!")
    print("="*50)
    print("\nPróximos pasos:")
    print("1. Edita .env con tu ANTHROPIC_API_KEY y tokens de Facebook/WhatsApp")
    print("2. Edita knowledge/products.json con TUS productos reales")
    print("3. Edita knowledge/faqs.json con TUS preguntas frecuentes")
    print("4. Edita knowledge/policies.json con la info de TU negocio")
    print("5. Edita knowledge/style_examples.json con tu estilo de escritura")
    print("6. Ejecuta: python main.py")
    print("\n📖 Panel de administración: http://localhost:8000/admin/status")
    print("🔧 Prueba el bot: POST http://localhost:8000/admin/test")
    print("📚 Docs API: http://localhost:8000/docs\n")


if __name__ == "__main__":
    asyncio.run(setup())
