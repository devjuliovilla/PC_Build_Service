import os
import json
import sys
from database import DDTechDB
from dotenv import load_dotenv

load_dotenv()

# =====================================================================
# ⚙️ CONFIGURACIÓN DE PERFIL AUTOMÁTICO (PERFIL JULIO VILLA / AI DEV)
# =====================================================================
# Si es True, el script omitirá las preguntas y usará tu perfil predeterminado.
# Si es False, se activará el configurador interactivo normal para cualquier usuario.
PERFIL_AI_DEV_ACTIVO = True

# Tu presupuesto asignado para la estación de trabajo (en pesos MXN)
PRESUPUESTO_DEV = 36000.0
# =====================================================================

LIMITS_BY_CATEGORY = {
    "Procesadores": 15,
    "Tarjetas Madre": 15,
    "Tarjetas de Video": 15,
    "Memorias RAM": 30,
    "Almacenamiento (SSD)": 25,
    "Almacenamiento (HDD)": 10,
    "Fuentes de Poder": 20,
    "Gabinetes": 40,
    "Enfriamiento": 25,
    "Disipadores CPU": 20,
    "Ventilación": 20
}

def filter_components_intelligently(components, budget, brand_pref, is_dev_profile=False):
    """
    Filtra y limita los componentes de forma inteligente para evitar saturar tokens
    y mejorar la calidad de las recomendaciones de la IA.
    - Elimina componentes que individualmente exceden un % realista del presupuesto.
    - Filtra por preferencia de marca.
    - Aplica límites dinámicos por categoría (más variedad a RAM, gabinetes, etc.).
    - Si is_dev_profile=True, excluye hardware de entrada (RAM <16GB, SSD <500GB, coolers básicos).
    """
    brand_pref_lower = brand_pref.lower()

    by_category = {}
    for c in components:
        cat = c["categoria"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(c)

    filtered = []

    for cat, items in by_category.items():
        cat_lower = cat.lower()
        max_items = LIMITS_BY_CATEGORY.get(cat, 12)
        cat_items = []

        for item in items:
            price = item["precio"]
            specs = item["especificaciones"]
            brand = specs.get("marca", "").lower()

            # --- FILTRADO POR PRESUPUESTO REALISTA ---
            if "procesador" in cat_lower and price > (budget * 0.45):
                continue
            if "madre" in cat_lower and price > (budget * 0.25):
                continue
            if "ram" in cat_lower and price > (budget * 0.20):
                continue
            if "video" in cat_lower and price > (budget * 0.60):
                continue
            if "fuente" in cat_lower and price > (budget * 0.15):
                continue
            if "gabinete" in cat_lower and price > (budget * 0.12):
                continue
            if "almacenamiento" in cat_lower and price > (budget * 0.20):
                continue
            if "enfriamiento" in cat_lower and price > (budget * 0.15):
                continue

            # --- FILTRADO POR PREFERENCIA DE MARCA ---
            if "intel" in brand_pref_lower and "procesador" in cat_lower and "intel" not in brand:
                continue
            if "amd" in brand_pref_lower and "procesador" in cat_lower and "amd" not in brand:
                continue

            if "video" in cat_lower or "gpu" in cat_lower or "tarjeta de video" in cat_lower:
                arquitectura = specs.get("arquitectura", "").lower()
                if "nvidia" in brand_pref_lower and "amd" in (arquitectura or ""):
                    continue
                if "radeon" in brand_pref_lower and "nvidia" in (arquitectura or ""):
                    continue

            # --- EXCLUSIONES PARA PERFIL DE DESARROLLADOR (AI DEV) ---
            if is_dev_profile:
                # RAM: solo módulos de 16GB o más (excluir 4GB, 8GB)
                if "ram" in cat_lower:
                    nombre_lower = item["nombre"].lower()
                    cap_match = __import__("re").search(r"(\d+)\s*gb", nombre_lower)
                    if cap_match:
                        gb_value = int(cap_match.group(1))
                        if "x" in nombre_lower:
                            parts = nombre_lower.split("x")
                            gb_value = int(__import__("re").search(r"(\d+)", parts[1]).group(1))
                        if gb_value < 16:
                            continue
                # SSD: solo unidades de 500GB o más
                if "almacenamiento" in cat_lower or "ssd" in cat_lower or "nvme" in cat_lower or "m.2" in cat_lower:
                    nombre_lower = item["nombre"].lower()
                    cap_match = __import__("re").search(r"(\d+)\s*(tb|gb)", nombre_lower)
                    if cap_match:
                        valor = int(cap_match.group(1))
                        unidad = cap_match.group(2)
                        if unidad == "gb" and valor < 500:
                            continue
                        if unidad == "tb":
                            pass
                    else:
                        continue
                # Enfriamiento: excluir disipadores de entrada (precio < 300 MXN asume gama baja)
                if "enfriamiento" in cat_lower or "disipador" in cat_lower:
                    if price < 300:
                        continue

            cat_items.append(item)

        cat_items.sort(key=lambda x: x["precio"])

        # Muestreo representativo usando límites dinámicos
        if len(cat_items) > max_items:
            step = len(cat_items) / max_items
            sampled = []
            for i in range(max_items):
                idx = int(i * step)
                idx = min(idx, len(cat_items) - 1)
                sampled.append(cat_items[idx])
            seen_ids = set()
            deduped = []
            for item in sampled:
                if item["id"] not in seen_ids:
                    seen_ids.add(item["id"])
                    deduped.append(item)
            filtered.extend(deduped)
        else:
            filtered.extend(cat_items)

    return filtered

def generate_compact_data(components):
    compact = []
    for c in components:
        compact.append({
            "id": c["id"],
            "cat": c["categoria"],
            "nom": c["nombre"],
            "p": c["precio"],
            "url": c["url"],
            "specs": c["especificaciones"]
        })
    return compact

def build_system_prompt():
    return (
        "Eres un experto Ingeniero de Hardware y un asistente especializado en armar configuraciones de computadoras (PC Building Expert).\n"
        "Tu misión es armar la MEJOR configuración de PC posible utilizando EXCLUSIVAMENTE la lista de componentes reales en stock suministrada en el JSON.\n"
        "Debes apegarte ESTRICTAMENTE a las siguientes reglas de compatibilidad de hardware:\n"
        "1. PROCESADOR Y TARJETA MADRE: Deben usar exactamente el mismo socket (ej. Socket AM4 con placa AM4, Socket AM5 con placa AM5, LGA1700 con placa LGA1700).\n"
        "2. PLACA MADRE Y MEMORIA RAM: El tipo de memoria de la RAM (DDR4 o DDR5) debe ser idéntico al tipo de memoria que soporta la tarjeta madre.\n"
        "3. FUENTE DE PODER: Debe tener suficiente potencia en Watts para alimentar la tarjeta de video (GPU) y el procesador elegidos. Suma el TDP estimado y añade un 30% de margen de seguridad.\n"
        "4. GABINETE: Debe tener un factor de forma que admita la tarjeta madre (ej. Un gabinete Micro-ATX no puede llevar una placa ATX).\n"
        "5. COMPONENTES REQUERIDOS: Para que una PC encienda y funcione, debes incluir de forma obligatoria:\n"
        "   - 1 Procesador\n"
        "   - 1 Enfriamiento (Disipador de Aire o Enfriamiento Líquido, a menos que el procesador incluya su propio disipador)\n"
        "   - 1 Tarjeta Madre\n"
        "   - Al menos 1 módulo de Memoria RAM (lo ideal son 2 para Dual Channel si el presupuesto lo permite)\n"
        "   - 1 Unidad de Almacenamiento (SSD preferiblemente)\n"
        "   - 1 Fuente de Poder\n"
        "   - 1 Gabinete\n"
        "   - 1 Tarjeta de Video Dedicada (OBLIGATORIA a menos que el procesador seleccionado tenga gráficos integrados y el presupuesto sea muy bajo).\n"
    )

def build_user_prompt(budget, usage, brand_pref, compact_components):
    components_str = json.dumps(compact_components, ensure_ascii=False, indent=1)

    prompt = (
        f"ARMA UNA CONFIGURACIÓN DE PC CON LOS SIGUIENTES REQUISITOS DEL USUARIO:\n"
        f"- Presupuesto Máximo: ${budget:,.2f} MXN (No puedes pasarte de esta cantidad bajo ninguna circunstancia, y debes tratar de optimizar cada peso).\n"
        f"- Uso Principal de la PC: {usage}\n"
        f"- Preferencia de Marcas: {brand_pref}\n\n"
        f"LISTA DE COMPONENTES DISPONIBLES EN DDTECH (JSON):\n"
        f"```json\n{components_str}\n```\n\n"
        f"INSTRUCCIONES DE RESPUESTA:\n"
        f"Presenta tu respuesta en formato Markdown elegante con la siguiente estructura:\n"
        f"1. **Resumen de la Configuración**: Tabla con Categoría, Nombre del componente, Enlace de compra (usar la URL exacta del JSON), y Precio en MXN.\n"
        f"2. **Costo Total**: El total exacto de la suma de los componentes elegidos en pesos mexicanos (MXN) y cuánto presupuesto sobró.\n"
        f"3. **Justificación Técnica**: Explica brevemente por qué elegiste estos componentes específicos para el uso de '{usage}' y cómo aseguraste la compatibilidad física entre ellos (Sockets, memorias DDR, wattage de fuente, etc.).\n"
        f"4. **Ruta de Mejora Futura (Upgrade)**: Qué componente le recomendarías cambiar primero si en el futuro quiere mejorar su PC."
    )
    return prompt

def ask_user_inputs():
    # ===================================================================
    # PERFIL AUTOMÁTICO: Si la bandera está activa, se salta las preguntas
    # y devuelve la configuración predefinida de Julio Villa / AI Dev.
    # ===================================================================
    if PERFIL_AI_DEV_ACTIVO:
        print("\n====================================================")
        print("    ⚡ PERFIL AI DEV ACTIVO - JULIO VILLA / AI DEV  ")
        print("====================================================")
        print(f"💰 Presupuesto asignado: ${PRESUPUESTO_DEV:,.2f} MXN")
        print("🎯 Estación de trabajo pesada: Visual Studio, SQL Server,")
        print("   Docker, VS Code, Firefox/Chrome/Edge, consolas, Opencode")
        print("   y Modelos de IA Locales (Ollama, LLaMA) con CUDA.")
        print("🏷️ Preferencia: Procesador AMD (AM5) + NVIDIA RTX (CUDA)")
        print("====================================================\n")
        usage = (
            "Estación de trabajo pesada de desarrollo de software. "
            "Debe poder ejecutar simultáneamente múltiples instancias de "
            "Visual Studio, SQL Server Management Studio, contenedores de Docker, "
            "múltiples navegadores (Firefox, Chrome, Edge) con pestañas pesadas, "
            "consolas de comandos, Opencode y ejecución de Modelos de IA Locales "
            "(Ollama, LLaMA) que requieren aceleración por hardware CUDA. "
            "Se busca una RTX 5060 Ti de 16GB VRAM y 32GB de RAM DDR5 "
            "con posibilidad de expandir a 64GB en el futuro."
        )
        brand = (
            "Procesador AMD Ryzen (priorizar sockets AM5 serie 7000 o 9000 "
            "de 8 a 12 núcleos) y Tarjeta de Video NVIDIA GeForce RTX "
            "(OBLIGATORIA con mínimo 12GB de VRAM para CUDA e IA local)."
        )
        return PRESUPUESTO_DEV, usage, brand

    print("\n----------------------------------------------------")
    print("      CONFIGURADOR INTERACTIVO CON IA DE DDTECH     ")
    print("----------------------------------------------------")

    while True:
        try:
            budget_str = input("💰 ¿Cuál es tu presupuesto máximo en MXN? (ej. 15000, 25000): ").strip()
            budget = float(budget_str.replace(",", "").replace("$", ""))
            if budget < 5000:
                print("⚠️ El presupuesto mínimo recomendado para armar una PC funcional es de $5,000 MXN.")
                continue
            break
        except ValueError:
            print("⚠️ Por favor, introduce un número válido.")

    print("\n🎯 ¿Cuál será el uso principal de la PC?")
    print("1) Gaming (Juegos modernos, esports)")
    print("2) Creación de contenido / Streaming (Edición de video, renderizado, Photoshop)")
    print("3) Productividad / Oficina / Escuela (Excel, navegación, multitarea básica)")
    print("4) Programación / Desarrollo de Software / Ciencia de Datos")

    usage_map = {
        "1": "Gaming (Juegos modernos a buenos FPS, esports)",
        "2": "Edición de video, diseño gráfico, modelado 3D y streaming en vivo",
        "3": "Oficina, escuela, consumo de multimedia y tareas cotidianas rápidas",
        "4": "Programación pesada, compilación de código, bases de datos y ciencia de datos básica"
    }

    while True:
        usage_choice = input("Selecciona una opción (1-4): ").strip()
        if usage_choice in usage_map:
            usage = usage_map[usage_choice]
            break
        elif usage_choice:
            usage = usage_choice
            break
        print("⚠️ Opción no válida.")

    print("\n🏷️ ¿Tienes alguna preferencia de marcas de componentes?")
    print("1) Sin preferencia (Mejor costo-beneficio) - RECOMENDADO")
    print("2) Procesador AMD / Tarjeta de Video AMD")
    print("3) Procesador AMD / Tarjeta de Video NVIDIA")
    print("4) Procesador Intel / Tarjeta de Video NVIDIA")

    brand_map = {
        "1": "Sin preferencia de marca, priorizar la mejor relación calidad-precio y compatibilidad.",
        "2": "Preferencia estricta por Procesador AMD y Tarjeta Gráfica AMD (Radeon).",
        "3": "Preferencia por Procesador AMD y Tarjeta Gráfica NVIDIA GeForce.",
        "4": "Preferencia por Procesador Intel y Tarjeta Gráfica NVIDIA GeForce."
    }

    while True:
        brand_choice = input("Selecciona una opción (1-4): ").strip()
        if brand_choice in brand_map:
            brand_pref = brand_map[brand_choice]
            break
        elif brand_choice:
            brand_pref = brand_choice
            break
        print("⚠️ Opción no válida.")

    return budget, usage, brand_pref

def select_provider():
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    providers = []
    if openai_key:
        providers.append(("1", "OpenAI (GPT-4o-mini)", "openai"))
    if gemini_key:
        providers.append(("2", "Google Gemini (Gemini 2.5 Flash)", "gemini"))

    if not providers:
        return None, None

    if len(providers) == 1:
        print(f"\n🔑 Se detectó clave API para: {providers[0][1]}")
        run_api = input("🤖 ¿Te gustaría enviar este prompt automáticamente para obtener tu recomendación? (s/n): ").strip().lower()
        if run_api == 's':
            return providers[0][2], openai_key if providers[0][2] == "openai" else gemini_key
        return None, None

    print("\n🔑 Se detectaron múltiples proveedores de IA disponibles:")
    print("1) OpenAI (GPT-4o-mini)")
    print("2) Google Gemini (Gemini 2.5 Flash)")
    print("3) Ninguno (solo guardar prompt)")
    choice = input("Selecciona una opción (1-3): ").strip()
    if choice == "1":
        return "openai", openai_key
    elif choice == "2":
        return "gemini", gemini_key
    else:
        return None, None

def call_openai_api(system_prompt, user_prompt, api_key):
    try:
        from openai import OpenAI
        print("\n[IA] Conectando con OpenAI (GPT-4o-mini)...")
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"\n[ERROR] Error al comunicarse con OpenAI: {e}")
        return None

def call_gemini_api(system_prompt, user_prompt, api_key):
    try:
        from openai import OpenAI
        print("\n[IA] Conectando con Google Gemini (Gemini 2.5 Flash)...")
        client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"\n[ERROR] Error al comunicarse con Gemini: {e}")
        return None

def main():
    db = DDTechDB()
    components = db.get_latest_components(only_in_stock=True)

    if not components:
        json_path = "data/ddtech_components.json"
        if os.path.exists(json_path):
            print(f"[INFO] Cargando componentes en stock desde el archivo local {json_path}...")
            with open(json_path, "r", encoding="utf-8") as f:
                components = json.load(f)
        else:
            print("[ERROR] No se encontraron componentes de DDTech guardados.")
            print("Por favor, ejecuta primero el scraper ejecutando: python main.py")
            sys.exit(1)

    print(f"[OK] Cargados {len(components)} componentes actualmente en stock.")

    budget, usage, brand_pref = ask_user_inputs()

    filtered_components = filter_components_intelligently(components, budget, brand_pref, is_dev_profile=PERFIL_AI_DEV_ACTIVO)
    print(f"[FILTRO INTELIGENTE] Componentes reducidos de {len(components)} a {len(filtered_components)} para evitar saturar tokens de la IA.")

    compact_components = generate_compact_data(filtered_components)

    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(budget, usage, brand_pref, compact_components)

    os.makedirs("data", exist_ok=True)
    prompt_file_path = "data/ai_prompt.txt"
    with open(prompt_file_path, "w", encoding="utf-8") as f:
        f.write(f"--- SYSTEM PROMPT ---\n{system_prompt}\n\n--- USER PROMPT ---\n{user_prompt}")

    print(f"\n[PROMPT MAESTRO CREADO] El prompt para la IA se ha guardado en: {prompt_file_path}")
    print("👉 Puedes copiar el contenido de ese archivo y pegarlo en ChatGPT (GPT-4), Claude (3.5 Sonnet) o Gemini.")

    provider, api_key = select_provider()

    if provider == "openai":
        response_text = call_openai_api(system_prompt, user_prompt, api_key)
        if response_text:
            print("\n====================================================")
            print("      RECOMENDACIÓN DE OPENAI (GPT-4o-mini)         ")
            print("====================================================")
            print(response_text)
            print("====================================================")
            rec_file = "data/pc_recomendacion.md"
            with open(rec_file, "w", encoding="utf-8") as f:
                f.write(response_text)
            print(f"\n[OK] La recomendación se ha guardado en: {rec_file}")
        else:
            print("⚠️ No se pudo obtener la respuesta automática, pero puedes usar el archivo 'data/ai_prompt.txt' de forma manual.")

    elif provider == "gemini":
        response_text = call_gemini_api(system_prompt, user_prompt, api_key)
        if response_text:
            print("\n====================================================")
            print("      RECOMENDACIÓN DE GOOGLE GEMINI                ")
            print("====================================================")
            print(response_text)
            print("====================================================")
            rec_file = "data/pc_recomendacion.md"
            with open(rec_file, "w", encoding="utf-8") as f:
                f.write(response_text)
            print(f"\n[OK] La recomendación se ha guardado en: {rec_file}")
        else:
            print("⚠️ No se pudo obtener la respuesta automática, pero puedes usar el archivo 'data/ai_prompt.txt' de forma manual.")

    else:
        if os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY"):
            print("\n💡 Puedes ejecutar este script de nuevo y seleccionar la IA cuando estés listo.")
        else:
            print("\n💡 Sugerencia: Configura tus API Keys siguiendo las instrucciones en:")
            print("   CONFIGURAR_LLAVES_SISTEMA.md")
            print("   para usar la recomendación automatizada por IA directamente en consola.")

if __name__ == "__main__":
    main()
