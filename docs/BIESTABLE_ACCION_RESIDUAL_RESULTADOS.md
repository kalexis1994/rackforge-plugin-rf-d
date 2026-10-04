# Acción dirigida del residual y cuarto intervalo certificado

## Soporte y congelación

Modelo nominal documental CA3046 y parámetros sintéticos intactos. Se
parte del último resultado realmente admitido del [prefijo fino](BIESTABLE_PREFIJO_22_RESULTADOS.md),
con tres intervalos hasta ≈781,25 ns. Se intenta sólo el cuarto soporte
archivado, índice 3, sin volver a resolver la trayectoria ni modificar
circuito, reconstrucción, radios, memoria entrante, pesos o P.

[Protocolo](BIESTABLE_ACCION_RESIDUAL_PROTOCOLO.md),
[helper](../tools/loudness_latch_residual_action.py) y
[productor](../tools/loudness_latch_bdf_static_precision_residual_action.py)
se congelan en `01ecdcb`, antes de medir. Datos, ocho tests y validator
se fijan en `984392b`, antes de validar. Se reutilizan por certificado y
SHA **16 recintos de inversa y 16 certificados de tasa**; no hay nuevos
solves de trayectoria, precondicionadores, métricas o consultas LDL.

## Qué prueba la nueva acción

Se conserva el polinomio firmado del RHS completo de 119 ecuaciones,
con sus errores uniformes y corrección constitutiva de las junturas.
El precondicionamiento combina sus coeficientes exactamente antes de
Bernstein. El resto se cubre por magnitudes independientes; no se cancela.

La identidad Hbar^-1*b=D^-1*(I-E)^-1*(D*X*b), con defecto intervalar
E y q<1, permite encerrar la acción completa. Se registra primer término,
corrección E*Y y cola exterior desde E^2, más la intersección de orden
cero para la misma acción. Son **128 certificados de subcelda** (16×8),
con potenciales puntuales y forcing L1 de memoria convertidos a sus normas.
No se usa X_binary*b como inversa exacta ni se elimina una corriente.

El nodo índice 28, celda 7, dominaba el rechazo anterior con término
directo ≈1,003961522 µV. La acción dirigida lo acota por
**≈4,49212424e-15 V**, manteniendo incertidumbre y restos. En las ocho
celdas de radio 1 µV mejora 86 de 94 términos directos y las 22 cotas
L1 de memoria: **688 términos directos y 176 de memoria** más pequeños.
Los presupuestos finales usan mínimos sólo entre cotas del mismo término.

## Banco fijado y cierre

Dos variantes por radio, en orden anterior a la medición: direct_only
y direct_and_memory. Ambas conservan comparación, ganancias de memoria,
tasas y anclaje. La primera cambia sólo el término directo; la segunda
también intersecta el forcing de memoria con la acción integrada.

| Radio | Variante | Presupuesto total | Resultado |
| --- | --- | --- | --- |
| 0,1 µV | Ambas | Cota entrante no cabe | Rechazo previo |
| 1 µV | direct_only | ≈0,753298754 µV | Aceptado, seleccionado [1,0] |
| 1 µV | direct_and_memory | ≈0,753298754 µV | Aceptado, secundario |
| 10 µV | Ambas | Fuera del rango de pantalla binary64; racional archivado | Rechazado |

La variante primaria certifica **cuatro intervalos contiguos desde t=0+
hasta aproximadamente 1,5625 µs**, con error nodal exterior **≤0,754 µV**.
Los tiempos racionales exactos del reloj permanecen en el informe.
No hay un hueco en este cuarto soporte; no se extrapola a un quinto.

El presupuesto anterior del cuarto intervalo era ≈1,004374301 µV
en radio 1 µV. Ahora basta cambiar el término directo para cerrar.
La mejora del forcing L1 no era necesaria para este corte; aporta
otra memoria final válida para el [siguiente prefijo](BIESTABLE_PREFIJO_ACCION_PLAN.md),
sin reescribir la selección primaria [1,0].

## Pico local y pico heredado

La variante primaria tiene pico **local ≈40,73903994 nV**, celda 7,
nodo índice 21. Allí el anclaje aporta ≈30,61426492 nV y el forcing
≈10,12477501 nV. Sus máximos separados son ≈33,33246611 y
≈23,76939691 nV; no se suman como si fueran el mismo nodo.

La secundaria reduce el pico local a **≈33,35281898 nV**, celda 0,
nodo índice 21, con ≈33,33246611 nV de anclaje y ≈0,02035287 nV de
forcing en ese punto. Pero ambas incluyen el pico entrante probado,
≈753,2987539 nV. Por eso el máximo total se mantiene igual mientras
se duplica la duración certificada. Esto no mide parecido con hardware.

## Validación y evidencia

**Ocho regresiones primarias pasan al primer intento en 193,2137798 s**,
con fuentes intactas antes y después. Incluyen sistema exacto sensible a
modo común y RHS dirigido, control sin cancelación, matriz incierta y
cola, restos independientes adversos, polinomio con integral conocida,
conversiones de las 119 coordenadas, recintos y cierres completos.
[Recibo](../evidence/loudness_latch_bdf_static_precision_residual_action_validation.json).
[Corpus ampliado](BIESTABLE_ACCION_RESIDUAL_ENTRADAS.md): 518 entradas
de 90 informes, 125 hashes propios y trece versiones históricas fallidas.
Sus dos pruebas pasan al primer intento en 85,3391684 s; diez pruebas
nuevas aceptadas en total, sin cambiar fuentes o datos entre intentos.

[Datos](../evidence/loudness_latch_bdf_static_precision_residual_action.json.gz):
**29886285 bytes**, SHA comprimido
`48f339e37811b83b7032fc2a93c9f382d7a60d8b46ceec9a5302f932d9009211`,
canónico `2a1ab2c3432eaced3b2358d1ab62aeec5f56f04c17916a1bc1d7fbdc1d814daa`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_residual_action_summary.json).

Los radios rechazados siguen siendo presupuestos condicionales. El
resultado prueba error del modelo nominal en estos cuatro soportes;
trayectoria completa, 1 mV global, identificación física, sonido vintage,
motor nativo y deadline mantienen sus gates independientes.
