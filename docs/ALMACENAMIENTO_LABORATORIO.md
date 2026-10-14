# Datos de laboratorio sin acumulación

Instrucción del usuario, 2026-10-14: retirar la cantidad de carpetas con
muestras generadas y evitar nueva acumulación. Aplica a RF-D.

## Referencias y salidas temporales

- Conservar fuentes documentales originales, capturas externas irrepetibles,
  biblioteca/compiler de referencia y entradas admitidas aún usadas por QA.
- Retirar exports regenerables y copias de compilación que no pertenecen
  al inventario admitido. Guardar metadatos y fuentes necesarios para repetir
  el experimento; no prometer recuperar los bytes retirados.
- Evitar copiar árboles ngspice/Cargo por cada ensayo. Usar el runtime de
  referencia existente o compilación directa y un único `tmp/lab-current`.
- Al terminar un experimento nuevo, retirar ejecutable, stdout/exports y
  fixtures temporales después de guardar métricas. Si falla, guardar fuentes,
  entrada mínima y replay antes de retirar esos intermedios. Un fixture de
  fallo grande necesita una justificación concreta y un presupuesto acotado.
- Conservar sólo audio útil para comparación actual. No generar variantes
  WAV ni carpetas de muestras como comprobación rutinaria de cada bloque.
  Una referencia ya admitida requiere un retiro explícito de su dependencia;
  esta limpieza mantiene todas las entradas declaradas por la QA vigente.

## Limpieza aplicada

Plan sobre `references-local/voice-circuit`, `vco1-circuit`,
`filter-vca-circuit` y `artifacts`, con exclusión de los 8769 inputs
admitidos. Mantener decks, informes y logs pequeños fuera de árboles de
compilación; retirar grandes exports y caches no admitidos. Un archivo
sin hash en el catálogo no acredita su identidad histórica: el plan
registra rutas, tamaños y mtime, sin inventar hashes de contenido.

[Planificador](../tools/plan_lab_cleanup.py) produce una lista privada;
[limpiador PowerShell](../tools/clean_lab_outputs.ps1) verifica todo el
alcance antes de borrar: rutas absolutas resueltas bajo RF-D, áreas exactas,
ancestros sin enlaces, QA/fuentes inmóviles, tamaño/mtime y exclusión de
entradas admitidas. Usa `Remove-Item -LiteralPath`, después retira sólo
directorios vacíos. Nunca borra código del repo, Git ni otro proyecto.
La lista completa queda comprimida en privado; el recibo público conserva
conteos, tamaños, alcance y SHA256. No se archivan las muestras borradas.

El banco nuevo del [puerto VCO](VCO_PUERTO_PANEL_PROTOCOLO.md) aplica la
política: ejecutable y exports existen sólo durante la comprobación,
`tmp/lab-current` queda vacío y el recibo conserva resultados. No crea
otra carpeta permanente de muestras ni una biblioteca nueva.
