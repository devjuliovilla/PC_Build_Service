import re

def clean_price(price_str):
    """
    Limpia una cadena de precio como '$3,499.00' y la convierte en float.
    """
    if not price_str:
        return 0.0
    try:
        # Remover signo de pesos, comas y espacios
        cleaned = re.sub(r"[^\d.]", "", price_str)
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

def generate_component_id(category, name, url):
    """
    Genera un ID único y limpio para el componente.
    Intenta extraer el slug del producto de la URL de DDTech.
    """
    # DDTech URL usualmente tiene este formato: https://ddtech.mx/producto/slug-del-producto
    url_match = re.search(r"/producto/([^/?#]+)", url)
    if url_match:
        slug = url_match.group(1).lower()
        return slug
    
    # Fallback si la URL no tiene el formato esperado
    clean_name = re.sub(r"[^\w\s-]", "", name).strip().lower()
    clean_name = re.sub(r"[_\s]+", "-", clean_name)
    category_slug = re.sub(r"[^\w\s-]", "", category).strip().lower().replace(" ", "-")
    return f"{category_slug}-{clean_name}"[:100]

def extract_specifications(category, name):
    """
    Extrae especificaciones técnicas clave basadas en la categoría y el nombre del producto.
    Esto permite a la IA comprender las compatibilidades de inmediato.
    """
    name_lower = name.lower()
    specs = {
        "marca": "Genérico",
        "especificaciones_encontradas": False
    }
    
    # 1. Extracción de Marcas Comunes
    brands = ["amd", "intel", "nvidia", "asus", "gigabyte", "msi", "kingston", "corsair", "xpg", "adata", 
              "evga", "cougar", "thermaltake", "nzxt", "cooler master", "deepcool", "be quiet", "aerocool", 
              "pny", "zotac", "powercolor", "asrock", "crucial", "g.skill", "western digital", "wd", "seagate", 
              "samsung", "teamgroup", "adata", "spectrix", "fury", "yeyian", "acteck", "balam rush", "game factor"]
    
    for brand in brands:
        if re.search(rf"\b{brand}\b", name_lower):
            # Normalizar nombres comunes
            if brand == "wd":
                specs["marca"] = "Western Digital"
            elif brand == "g.skill":
                specs["marca"] = "G.Skill"
            else:
                specs["marca"] = brand.upper() if len(brand) <= 4 else brand.capitalize()
            break

    category_lower = category.lower()

    # --- PROCESADORES ---
    if "procesador" in category_lower:
        specs["tipo"] = "Procesador"
        
        # Sockets
        if "am4" in name_lower:
            specs["socket"] = "AM4"
        elif "am5" in name_lower:
            specs["socket"] = "AM5"
        elif "1700" in name_lower or "lga1700" in name_lower:
            specs["socket"] = "LGA1700"
        elif "1200" in name_lower or "lga1200" in name_lower:
            specs["socket"] = "LGA1200"
        elif "1151" in name_lower or "lga1151" in name_lower:
            specs["socket"] = "LGA1151"
        elif "1851" in name_lower or "lga1851" in name_lower:
            specs["socket"] = "LGA1851"
            
        # Línea de Procesador
        if "ryzen 9" in name_lower:
            specs["linea"] = "Ryzen 9"
        elif "ryzen 7" in name_lower:
            specs["linea"] = "Ryzen 7"
        elif "ryzen 5" in name_lower:
            specs["linea"] = "Ryzen 5"
        elif "ryzen 3" in name_lower:
            specs["linea"] = "Ryzen 3"
        elif "core i9" in name_lower:
            specs["linea"] = "Core i9"
        elif "core i7" in name_lower:
            specs["linea"] = "Core i7"
        elif "core i5" in name_lower:
            specs["linea"] = "Core i5"
        elif "core i3" in name_lower:
            specs["linea"] = "Core i3"
        elif "celeron" in name_lower:
            specs["linea"] = "Celeron"
        elif "pentium" in name_lower:
            specs["linea"] = "Pentium"
            
        # Gráficos integrados
        # En AMD la terminación "g" indica gráficos integrados, y "x" o normal no (excepto Ryzen 7000/9000 que casi todos tienen básicos).
        # En Intel la terminación "f" indica SIN gráficos integrados.
        if "intel" in specs.get("marca", "").lower():
            specs["graficos_integrados"] = False if re.search(r"\b\d+f\b", name_lower) else True
        elif "amd" in specs.get("marca", "").lower():
            if "ryzen" in name_lower:
                # Serie 7000 y 9000 (AM5) tienen integrados básicos por defecto a menos que sea F o similar
                if "am5" in specs.get("socket", ""):
                    specs["graficos_integrados"] = False if "7500f" in name_lower else True
                else:
                    # AM4
                    specs["graficos_integrados"] = True if re.search(r"\b\d+g\b", name_lower) else False
            else:
                specs["graficos_integrados"] = False
        
        specs["especificaciones_encontradas"] = True

    # --- TARJETAS MADRE ---
    elif "tarjeta madre" in category_lower or "placa madre" in category_lower or "motherboard" in category_lower:
        specs["tipo"] = "Tarjeta Madre"
        
        # Sockets
        if "am4" in name_lower:
            specs["socket"] = "AM4"
        elif "am5" in name_lower:
            specs["socket"] = "AM5"
        elif "1700" in name_lower or "lga1700" in name_lower:
            specs["socket"] = "LGA1700"
        elif "1200" in name_lower or "lga1200" in name_lower:
            specs["socket"] = "LGA1200"
        elif "1151" in name_lower or "lga1151" in name_lower:
            specs["socket"] = "LGA1151"
        elif "1851" in name_lower or "lga1851" in name_lower:
            specs["socket"] = "LGA1851"
            
        # Chipset
        chipsets = ["a320", "b450", "b550", "x570", "a620", "b650", "x670", 
                    "h410", "b460", "h470", "z490", "h510", "b560", "h570", "z590", 
                    "h610", "b660", "h670", "z690", "b760", "z790", "z890"]
        for chipset in chipsets:
            if chipset in name_lower:
                specs["chipset"] = chipset.upper()
                break
                
        # Tipo de Memoria
        if "ddr5" in name_lower:
            specs["tipo_ram"] = "DDR5"
        elif "ddr4" in name_lower:
            specs["tipo_ram"] = "DDR4"
        else:
            # Por descarte de socket e historia
            if specs.get("socket") in ["AM5", "LGA1851"]:
                specs["tipo_ram"] = "DDR5"
            elif specs.get("socket") in ["AM4", "LGA1200", "LGA1151"]:
                specs["tipo_ram"] = "DDR4"
                
        # Factor de forma
        if "mini-itx" in name_lower or "itx" in name_lower:
            specs["factor_forma"] = "Mini-ITX"
        elif "micro-atx" in name_lower or "matx" in name_lower or "m-atx" in name_lower:
            specs["factor_forma"] = "Micro-ATX"
        elif "atx" in name_lower:
            specs["factor_forma"] = "ATX"
            
        specs["especificaciones_encontradas"] = True

    # --- MEMORIAS RAM ---
    elif "ram" in category_lower or "memoria ram" in category_lower:
        specs["tipo"] = "Memoria RAM"
        
        # Tipo DDR
        if "ddr5" in name_lower:
            specs["tipo_ram"] = "DDR5"
        elif "ddr4" in name_lower:
            specs["tipo_ram"] = "DDR4"
        elif "ddr3" in name_lower:
            specs["tipo_ram"] = "DDR3"
            
        # Capacidad (ej. 8gb, 16gb, 32gb, 2x8gb, 2x16gb)
        capacity_match = re.search(r"(\d+x\d+|\d+)\s*(gb|g)\b", name_lower)
        if capacity_match:
            specs["capacidad"] = capacity_match.group(0).upper()
            
        # Velocidad (ej. 3200mhz, 5200mhz, 6000mhz)
        speed_match = re.search(r"(\d+)\s*(mhz)\b", name_lower)
        if speed_match:
            specs["velocidad"] = speed_match.group(0).upper()
            
        specs["especificaciones_encontradas"] = True

    # --- TARJETAS DE VIDEO ---
    elif "tarjeta de video" in category_lower or "gpu" in category_lower or "video" in category_lower:
        specs["tipo"] = "Tarjeta de Video"
        
        # Chipset de video (NVIDIA, AMD Radeon, Intel Arc)
        if "rtx" in name_lower or "gtx" in name_lower:
            specs["arquitectura"] = "NVIDIA GeForce"
            # Buscar el modelo exacto
            model_match = re.search(r"(rtx\s*\d+\s*(ti|super)?|gtx\s*\d+\s*(ti)?)", name_lower)
            if model_match:
                specs["chipset_gpu"] = model_match.group(1).upper().replace(" ", "")
        elif "rx" in name_lower:
            specs["arquitectura"] = "AMD Radeon"
            model_match = re.search(r"(rx\s*\d+\s*(xt)?)", name_lower)
            if model_match:
                specs["chipset_gpu"] = model_match.group(1).upper().replace(" ", "")
        elif "arc" in name_lower:
            specs["arquitectura"] = "Intel Arc"
            model_match = re.search(r"(a\d{3})", name_lower)
            if model_match:
                specs["chipset_gpu"] = model_match.group(1).upper()
                
        # VRAM (ej. 8gb, 12gb, 16gb)
        vram_match = re.search(r"(\d+)\s*(gb|g)\b", name_lower)
        if vram_match:
            specs["vram"] = vram_match.group(0).upper()
            
        specs["especificaciones_encontradas"] = True

    # --- ALMACENAMIENTO ---
    elif "almacenamiento" in category_lower or "disco" in category_lower or "ssd" in name_lower or "m.2" in name_lower or "hdd" in name_lower:
        specs["tipo"] = "Almacenamiento"
        
        # Tipo exacto
        if "nvme" in name_lower or "m.2" in name_lower:
            specs["formato"] = "SSD M.2 NVMe"
        elif "ssd" in name_lower:
            specs["formato"] = "SSD SATA 2.5"
        elif "hdd" in name_lower or "mecanico" in name_lower or "duro" in name_lower:
            specs["formato"] = "HDD (Disco Duro)"
            
        # Capacidad
        cap_match = re.search(r"(\d+)\s*(tb|gb)\b", name_lower)
        if cap_match:
            specs["capacidad"] = cap_match.group(0).upper()
            
        specs["especificaciones_encontradas"] = True

    # --- FUENTES DE PODER ---
    elif "fuente" in category_lower or "poder" in category_lower or "power supply" in category_lower:
        specs["tipo"] = "Fuente de Poder"
        
        # Watts (ej. 500w, 650w, 750w)
        watts_match = re.search(r"(\d+)\s*(w|watts)\b", name_lower)
        if watts_match:
            specs["potencia"] = watts_match.group(1) + "W"
            
        # Certificación
        cert_match = re.search(r"80\s*plus\s*(bronze|gold|white|silver|platinum|titanium)?", name_lower)
        if cert_match:
            cert = cert_match.group(1)
            specs["certificacion"] = f"80 Plus {cert.capitalize()}" if cert else "80 Plus White/Standard"
        else:
            specs["certificacion"] = "Sin Certificación / Genérica"
            
        specs["especificaciones_encontradas"] = True

    # --- GABINETES ---
    elif "gabinete" in category_lower or "chasis" in category_lower or "case" in category_lower:
        specs["tipo"] = "Gabinete"
        
        # Formatos que soporta
        supports = []
        if "atx" in name_lower:
            supports.append("ATX")
        if "micro atx" in name_lower or "matx" in name_lower or "m-atx" in name_lower:
            supports.append("Micro-ATX")
        if "mini itx" in name_lower or "itx" in name_lower:
            supports.append("Mini-ITX")
            
        if supports:
            specs["soporte_placas"] = supports
        
        specs["especificaciones_encontradas"] = True

    # --- ENFRIAMIENTO ---
    elif "enfriamiento" in category_lower or "ventil" in category_lower or "ventilador" in category_lower or "cooler" in name_lower or "disipador" in name_lower:
        specs["tipo"] = "Enfriamiento"
        
        if "liquida" in name_lower or "liquid" in name_lower or "aio" in name_lower:
            specs["tipo_enfriamiento"] = "Líquido"
            # Tamaño de radiador
            rad_match = re.search(r"(120|240|280|360)\s*(mm)?", name_lower)
            if rad_match:
                specs["tamano_radiador"] = rad_match.group(1) + "mm"
        else:
            specs["tipo_enfriamiento"] = "Por Aire"
            
        specs["especificaciones_encontradas"] = True

    return specs
