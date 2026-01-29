# Sistema propuesto: pipeline de recetas Instachef (vista modular)

> Objetivo: convertir inputs de Cookidoo (URLs/texto estructurado) en **un solo Excel** válido para el proveedor, usando listas maestras estrictas y reglas de `Working Mode` compatibles.

## Estructura visual (propuesta)

```
instachef_recipe_pipeline/
├── data/
│   ├── raw/                     # Inputs: URLs, capturas, texto estructurado
│   ├── templates/               # Excel template del proveedor
│   └── lookups/                 # Copias JSON de listas maestras (unidades, accesorios, modos)
├── docs/
│   ├── recipe_pipeline.md       # Diseño general y reglas clave
│   └── system_architecture.md   # Esta guía visual
├── scripts/
│   ├── schema_snapshot.py       # Extrae headers + listas maestras de la plantilla
│   └── inspect_working_modes.py # Analiza uso real de working modes en recetas históricas
├── src/
│   ├── parsers/
│   │   ├── cookidoo_reader.py   # Lee URL/texto y extrae ingredientes + pasos
│   │   └── step_parser.py       # Normaliza pasos a estructura interna
│   ├── transformers/
│   │   ├── legal_rewriter.py    # Parafrasea verbos (evita texto idéntico)
│   │   ├── technical_mapper.py  # Convierte variables Thermomix → Instachef
│   │   └── list_normalizer.py   # Ajusta unidades/accesorios/modos a listas maestras
│   ├── validators/
│   │   ├── rule_validator.py    # Reglas duras: listas maestras + campos obligatorios
│   │   └── content_validator.py # Coherencia básica: ingredientes vs pasos
│   ├── generators/
│   │   └── excel_writer.py      # Genera un solo Excel con el batch completo
│   └── utils/
│       ├── constants.py         # Valores fijos (Language=ES, RecipeType=汤机...)
│       └── io.py                # Lectura/escritura de JSON y cache de lookups
├── output/
│   └── instachef_recipes.xlsx   # ✅ Excel final listo para proveedor
└── main.py                      # Orquesta el pipeline end-to-end
```

## Módulos y funciones (cadena de montaje)

### 1) **Inputs y lectura**
- **`cookidoo_reader.py`**: recibe URL o texto y extrae título, ingredientes, tiempos y pasos.
- **`step_parser.py`**: convierte pasos en estructura interna (JSON) con `Description/Weigh/Adapted Cooking`.

### 2) **Transformación legal y técnica**
- **`legal_rewriter.py`**: cambia verbos para reducir riesgo de copia literal.
- **`technical_mapper.py`**: ajusta variables (velocidad/temperatura/tiempo) a Instachef.
- **`list_normalizer.py`**: fuerza que unidades/accesorios/modos estén en listas maestras.

### 3) **Validación**
- **`rule_validator.py`**: reglas duras de plantilla.
  - `Language = ES`.
  - `Recipe Type = 汤机(Robot Cooker)`.
  - Unidades solo de `Unit For Ingredients`.
  - Accesorios solo de `Accessories List`.
  - Working Mode solo `Description / Weigh / Adapted Cooking`.
- **`content_validator.py`**: coherencia básica (ingredientes usados vs listados).

### 4) **Generación de Excel**
- **`excel_writer.py`**: escribe **un solo Excel** con el batch completo (valores estáticos).

### 5) **Orquestación**
- **`main.py`**: pipeline completo → input → parseo → transformación → validación → Excel final.

## Flujo end-to-end (resumen)
1. **Entrada** (URL/texto).
2. **Parser** extrae ingredientes/pasos.
3. **Transformers** reescriben verbos + ajustan parámetros.
4. **Normalizer** fuerza listas maestras.
5. **Validator** bloquea errores técnicos.
6. **Excel Writer** genera el archivo final.

---

## Por qué este diseño es útil
- Cada módulo tiene **una sola responsabilidad**.
- Los errores se detectan temprano (antes de tocar Excel).
- El sistema puede escalar con nuevas reglas sin romper el pipeline.
