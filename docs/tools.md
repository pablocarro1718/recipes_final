# Herramientas locales (sin dependencias externas)

## 1) Snapshot de la plantilla
Extrae headers y listas maestras desde la plantilla oficial en JSON.

```bash
python scripts/schema_snapshot.py "Excel template recetas.xlsx" -o schema_snapshot.json
```

Salida: `schema_snapshot.json` con los headers de cada hoja y las filas de listas maestras.

## 2) Resumen de working modes
Resume cómo se usan los working modes en la hoja de Cooking Steps del archivo histórico.

```bash
python scripts/inspect_working_modes.py "Current recipe (1).xlsx" -o working_mode_summary.json
```

Salida: `working_mode_summary.json` con conteos por modo, y cuántos pasos incluyen descripción o parámetros de máquina.
