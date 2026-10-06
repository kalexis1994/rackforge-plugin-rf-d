# Seis correcciones sobre memoria temporal

2026-10-06. Primera fase del [protocolo previo](VOZ_NOTA_LARGA_SEIS_CORRECCIONES_PROTOCOLO.md).
Todavía no se mide la variante que publique seis correcciones.

## Build10 y controles de identidad

Se deriva de build09 con el mismo GCC, flags, dispositivos, matrices,
selección de captura y tres correcciones publicadas. Sólo cambia
`RFLinearSolve` para guardar los pares tras la tercera corrección,
calcular tres adicionales con el mismo factor SMP/KLU y restaurar los
pares originales antes de publicar. Se activa con flag propio y sólo
dentro de las cuatro capturas; no refactoriza ni evalúa dispositivos.
Las doce correcciones adicionales se registran con etiqueta `RFSHADOW`.

El [build](../evidence/voice_full_note_shadow_build01.json) registra
4338 archivos fuente, copia, almacenamiento, compiler, runtime y hashes.
Ambos controles tienen presupuesto previo de 900 s:

- Desactivado: Gear500 de 40 ms, 191714 filas y 18 vectores/reloj exactos.
- Activado: Trap125 rechazado, 155680 filas, mismo error y cuatro matrices.
  Los stamps, RHS, contextos, soluciones publicadas y tres correcciones
  originales también son exactamente iguales a las capturas de build09.

La [auditoría](../evidence/voice_full_note_shadow_validation01.json)
reconstruye controles y fuentes sin nuevos solves. Se conserva el intento
de preparación que comenzó antes de terminar la compilación y no lanzó
SPICE: [recibo](../evidence/voice_full_note_shadow_preparation_rejection01.json).
El helper inicial y su deck quedan preservados; el reintento sólo usa
otra carpeta y otro recibo, con gates idénticos.

## Contraste con las raíces existentes

Se selecciona la misma última pareja 100/101 de 226 incógnitas que en
el [contraste de tres correcciones](VOZ_NOTA_LARGA_MATRIZ_RESULTADOS.md).
Se reutilizan sus dos raíces Decimal 80/120 y auditoría, sin nuevas
factorizaciones. El [análisis](../evidence/voice_full_note_shadow_analysis01.json)
verifica exactamente cada residual compensado, corrección, actualización
y publicación hipotética de seis. Pasan los gates originales por unidad
en todas las filas de esas dos matrices.

El error máximo de voltaje pasa de **9,850629 µV** con tres a
**0,537473 nV** con seis. El máximo de corriente es **0,548123 pA**.
Son errores frente a las raíces de esas matrices, no diferencias de
audio ni una cota para otras factorizaciones o estados.

El [replay](../evidence/voice_full_note_shadow_analysis_validation01.json)
reproduce las decisiones sin SPICE, evaluación no lineal ni factorización.
Los resultados numéricos completos, incluyendo corrientes, están en el
recibo; el valor calculado sobre la copia nunca se publica a la trayectoria.

La regresión sintética inicial omitía una incógnita de corriente; se
conservan los bytes y el [intento fallido](../evidence/voice_full_note_shadow_regression_attempt01.json).
La fixture corregida incluye voltaje y corriente. Las seis pruebas pasan,
incluyendo residual falso, actualización incoherente y pasos faltantes;
no se modifica el comparador ni sus límites.

## Próxima fase

El ensayo admite seis correcciones sólo en las dos matrices contrastadas.
No identifica la causa completa del aborto y no admite 350 ms, audio nuevo
o tiempo real. Se conserva el banco largo con publicación de tres.
Siguiente: candidato activo separado, identidad desactivada, control
nominal y cuatro escenas cortas; luego nuevo banco de 350 ms y balances.
No cambiar parámetros físicos, tarjetas, `itl4` ni gates para promoverlo.
