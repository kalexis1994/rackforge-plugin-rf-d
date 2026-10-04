# Tres intervalos contiguos y diagnóstico del primer hueco

## Fuente y experimento

Modelo nominal documental CA3046 con parámetros sintéticos. Se parte
del certificado secundario [1,1] del [banco anterior](BIESTABLE_MEMORIA_COORDENADA_RESULTADOS.md),
ya aceptado y declarado antes de medir. La selección primaria histórica
[1,0] queda intacta. Misma trayectoria publicada, leyes, P, pesos y
normalización; se transportan las 22 cotas finales anclaje+forcing.

[Protocolo](BIESTABLE_PREFIJO_22_PROTOCOLO.md),
[helper](../tools/loudness_latch_fine_prefix.py) y
[productor](../tools/loudness_latch_bdf_static_precision_fine_prefix.py)
se congelan en `5c4a0b1`. El primer lanzamiento mide el tercer intervalo,
pero interrumpe al mostrar como float la cota rechazada de radio 10 µV.
No guarda un informe completo. Fuente exacta, fase y salida observada se
archivan en `19dd529`, antes de corregir. Los contadores completos de
ese intento no se recuperaron y no se inventan.

La conversión de diagnóstico se corrige y congela en `b7b3879`; la cota
racional permanece completa, sin cambiar aritmética o gates. La nueva
ejecución completa se identifica por esa revisión. El [recibo del fallo](../evidence/loudness_latch_bdf_static_precision_fine_prefix_measurement_attempt.json)
no equivale a un certificado publicado. Datos, ocho tests y validator
de la ejecución completa se congelan en `db976c3`, antes de validar.

## Banco completo y parada

Máximo previsto: ocho intervalos adicionales desde 390,625 ns. Se intentan
dos y se detiene en el primero sin cierre, índice 3 (cuarto intervalo
contado desde el origen). Radios fijos: 0,1; 1; 10 µV. Una variante por
radio, con P retenida y todos los coeficientes recalculados para 22 grupos.

| Soporte aproximado | Radio | Presupuesto nodal | Resultado |
| --- | --- | --- | --- |
| 390,625→781,25 ns | 0,1 µV | Cota entrante no cabe | Rechazo previo |
| 390,625→781,25 ns | 1 µV | ≈0,753298754 µV | Aceptado, selección índice 1 |
| 390,625→781,25 ns | 10 µV | ≈3,861766e531 V | Rechazado |
| 781,25→1562,5 ns | 0,1 µV | Cota entrante no cabe | Rechazo previo |
| 781,25→1562,5 ns | 1 µV | ≈1,004374301 µV | Rechazado |
| 781,25→1562,5 ns | 10 µV | ≈7,019062e1067 V | Rechazado |

Se certifican **tres intervalos contiguos hasta aproximadamente 781,25 ns**,
con cota exterior redondeada hacia arriba **≤0,754 µV**. El informe
conserva tiempos racionales exactos del reloj binary64. El endpoint
intentado es aproximadamente 1562,5 ns; no aumenta la duración probada.
El cuarto intervalo no aporta memorias para continuar. Los presupuestos
rechazados son comparaciones condicionales, no errores reales medidos.

## Inversas, norma y costes

**16 nuevos precondicionadores**, **32 recintos de inversa** y **3168
consultas LDL de tasa**. Cero solves nuevos de trayectoria y cero sistemas
de métrica. Los 32 recintos medios son invertibles: q máximo ≈0,058211704
en 1 µV y ≈0,582117839 en 10 µV. La invertibilidad sola no cierra el tubo.

P es común a todo este prefijo. Se certifican nuevamente las tasas
isotrópica, dirigida y balanceada en cada celda, sin heredar disipación.
En 1 µV la cota final de junturas sigue alrededor de −20,0874e6 s^-1.
En 10 µV pasa a ≈+3,15716e9 s^-1: ese radio produce presupuestos
enormes y rechaza. No se interpreta ninguna de estas tasas internas
como estabilidad o inestabilidad del circuito acoplado completo.

## Causa del hueco en este presupuesto

El pico del cuarto intervalo se alcanza en celda 7, nodo índice 28.
Anclaje en ese pico: ≈0,000272251 µV; forcing: ≈1,004102050 µV.
La parte algebraica directa es ≈1,003961522 µV; la memoria forzada
aporta ≈0,000140527 µV. Los máximos independientes del anclaje y
forcing son ≈0,033332466 y ≈1,004102050 µV, respectivamente; no se
suman como si correspondieran al mismo nodo.

El residual nodal máximo del cuarto soporte es ≈3,802695 nA; la
restricción lineal máxima, ≈1,241078e-16 V. Pero el término directo
dominante no viene de esa mayor corriente: las cotas de RHS en nodos
27 y 28 son ≈7,771895e-20 A, multiplicadas individualmente por
ganancias de inversa de ≈6,458924e12 V/A. Cada término aporta
≈0,501980759 µV; las restricciones aportan sólo ≈4,251e-21 V.

La suma de magnitudes pierde información de dirección. Esto motiva
investigar acciones certificadas de la inversa sobre el residual
vectorial, conservando signos y correlaciones justificadas. No prueba
que esos dos errores cancelen: las leyes y restos completos deben
demostrarlo. No eliminar corrientes pequeñas, modificar R35 o regularizar
el circuito para hacer pasar el presupuesto. El
[siguiente plan](BIESTABLE_ACCION_RESIDUAL_PLAN.md) fija esa investigación.

## Evidencia y alcance

Las **ocho regresiones primarias pasan al primer intento en
254,3650355 s**, con fuentes idénticas antes y después. Reproducen
32 inversas y sus hashes, todas las cubiertas/residual, las tasas y
conversiones de 22 grupos, la fuente secundaria, interfaces, transporte,
cierres y parada. Incluyen sucesión no lineal conocida con cambios de h,
dirección anisótropa, rechazo de pruebas condicionales y recuperación
exacta de la fuente del lanzamiento fallido.
[Recibo primario](../evidence/loudness_latch_bdf_static_precision_fine_prefix_validation.json).
[Corpus ampliado](BIESTABLE_PREFIJO_22_ENTRADAS.md): 507 entradas de
88 informes, 122 hashes propios y trece versiones históricas fallidas.
Sus dos pruebas pasan al primer intento en 92,9207176 s; diez pruebas
nuevas aceptadas en total. No cambian datos o fuentes entre intentos.

[Datos](../evidence/loudness_latch_bdf_static_precision_fine_prefix.json.gz):
**34568033 bytes**, SHA comprimido
`67fcee9651ab30d8ebbea829ed2ff105ab871e4885a2bd2d66cd5afca2ca8d8b`,
canónico `d29addfe31cf153ccf51bd73525f01be6bd5c5a8406bcc4628f111c09b177d53`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_fine_prefix_summary.json).

El cierre pertenece al modelo nominal y estos tres intervalos. Precisión
global de 1 mV, trayectoria completa, parámetros físicos, audio, motor
nativo y deadline mantienen sus gates separados.
