# Instachef Recipe Pipeline — Design Notes (v0)

## Objetivo
Construir un flujo programático que reciba **inputs** (URLs o extractos estructurados de Cookidoo México) y genere un **Excel compatible con la plantilla del proveedor**, minimizando errores técnicos y permitiendo correcciones de contenido rápidas.

## Observaciones clave de la plantilla
Las hojas principales de la plantilla actual son:
- Recipe List
- Ingredients List
- Cooking Steps
- Nutrient
- Category List
- Label List
- Accessories List
- Unit For Ingredients
- Working Mode List

Cada receta se representa en **tres hojas** (Recipe List, Ingredients List y Cooking Steps), con referencias por `Recipe NO`, `Language`, `Recipe Type` y `Recipe Name`. La plantilla incluye listas maestras (categorías, etiquetas, accesorios, unidades y working modes) que se deben usar para valores válidos.

### Columnas críticas
**Recipe List** contiene los campos principales como nombre, categoría, tiempos y accesorios. **Ingredients List** define cada ingrediente con cantidad/unidad/nombre. **Cooking Steps** define secuencia de pasos con `Working Mode`, texto descriptivo y/o parámetros de máquina (temperatura, dirección, velocidad, tiempos).

### Valores fijos y disciplina de listas maestras
- `Language` siempre debe ser `ES`.
- `Recipe Type` siempre debe ser `汤机(Robot Cooker)`.
- **Recipe List (columna Q)**: accesorios deben salir de *配件列表Accessories List*. Si hay equivalencias de Thermomix, se ajustan al nombre válido en la lista (ej. *Varoma* → *cesta de vapor* si así aparece en la lista maestra).
- **Ingredients List (columna G)**: unidades deben salir únicamente de *食材单位列表Unit For Ingredients*.
- **Cooking Steps (columna F)**: working mode debe salir de *自动程序Working Mode List*. Para mantener compatibilidad con el archivo histórico, solo se usarán `自适应烹饪(Adapted Cooking)`, `称重(Weigh)` y `描述(Description)`.

### Working Modes (observación del archivo con 413 recetas)
En el archivo histórico, la hoja *Cooking Steps* usa principalmente:
- `描述(Description)` → tiene descripción textual; rara vez usa parámetros de máquina.
- `自适应烹饪(Adapted Cooking)` → casi siempre usa parámetros de máquina (temperatura/velocidad/tiempo) y raramente descripción.
- `称重(Weigh)` → usa descripción; no usa parámetros de máquina.

Se observa además un modo minoritario `间歇搅拌(Brown)` con parámetros de máquina. Este patrón debe replicarse en el flujo: **Description** para pasos narrativos, **Adapted Cooking** para pasos que fijan variables de cocción y **Weigh** para pasos de pesar.

## Flujo propuesto (fases)

### Fase 0 — Auditoría de plantillas
1. **Extraer esquema y listas maestras** desde la plantilla oficial.
2. **Comparar** con el archivo histórico para validar rangos y valores permitidos.

Salida: JSON con headers y listas maestras.

### Fase 1 — Modelo de datos interno
Definir un modelo interno (JSON) que sea estable y fácil de validar. Ejemplo:

```json
{
  "recipe": {
    "recipe_no": 101,
    "language": "ES",
    "recipe_type": "Main",
    "name": "Tinga de pollo",
    "category_id": "C-05",
    "labels": ["L-02", "L-08"],
    "accessories": ["A-01"],
    "servings": 4,
    "times": {"prep_min": 15, "cook_min": 35, "rest_min": 0},
    "overview": "Sofrito, cocción y deshebrado del pollo."
  },
  "ingredients": [
    {"no": 1, "qty": 300, "unit": "g", "name": "pechuga de pollo"},
    {"no": 2, "qty": 1, "unit": "pz", "name": "cebolla"}
  ],
  "steps": [
    {"no": 1, "mode": "Weigh", "description": "Pesa la cebolla."},
    {"no": 2, "mode": "Description", "description": "Agrega aceite al vaso."},
    {"no": 3, "mode": "Adapted Cooking", "temperature": 120, "speed": 2, "direction": "R", "minutes": 5, "seconds": 0}
  ]
}
```

### Fase 2 — Ingesta desde Cookidoo (mexicanizado)
1. **Extraer** ingredientes, pasos y tiempos desde el input (URL o texto).
2. **Parafrasear** cambiando verbos para evitar textos idénticos (sin cambiar la lógica culinaria).
3. **Normalizar** unidades y nombres según lista maestra.

### Fase 3 — Validación automática
Validaciones mínimas:
- Todos los ingredientes usados en los pasos aparecen en Ingredients List.
- Todos los `Working Mode` pertenecen a Working Mode List.
- Para `Adapted Cooking`, se exigen variables (temp/vel/tiempo).
- Para `Description` y `Weigh`, se exige descripción y se vacían variables.

### Fase 4 — Export a Excel
1. Escribir Recipe List, Ingredients List y Cooking Steps.
2. Guardar como **valores estáticos** (sin fórmulas).
3. Generar **un solo Excel** con todas las recetas del batch (no un archivo por receta).

## Entregables iniciales (MVP)
1. **Script de esquema** para leer la plantilla y capturar listas maestras.
2. **Validador mínimo** de cooking steps y working modes.
3. **Piloto** con 2–3 recetas para confirmar formato con proveedor.

## Pendientes para definir contigo
- Credenciales de acceso a Cookidoo (si se automatiza lectura de URLs).
- Catálogo de unidades y equivalencias (g, ml, pz, etc.).
- Criterios de “parafraseo” aceptables.
- Si se desea soporte multibatch (varios xlsx en un folder).

---

> Este documento se actualizará con los hallazgos de la plantilla y el comportamiento real de la máquina.
