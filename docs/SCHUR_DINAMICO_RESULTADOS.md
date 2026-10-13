# Condensación dinámica de LM741: banco y rechazo de admisión

2026-10-13. Base48543a7. Voz CA3046 condicionada de229 incógnitas;
no hay referencia física. [Contrato inicial](SCHUR_DINAMICO_PROTOCOLO.md),
[índices](SCHUR_DINAMICO_INDICES.md),
[puertos/memorias](SCHUR_DINAMICO_OBSERVACIONES.md) y
[revisión explícita de la escala residual](SCHUR_DINAMICO_ESCALA_RESIDUAL.md).

## Qué se condensa y qué se conserva

Se eliminan las correcciones interiores de los dos LM741 nominales:
32 incógnitas por integrado y etapa, formando dos bloques64×64 con las
dos etapas Radau. La matriz exterior pasa de458 a330 incógnitas.
Se factoriza cada interior una vez para11 RHS: diez columnas de puertos
y un RHS dinámico. Se reconstruyen las458 correcciones antes de Newton.
No se sustituye la dinámica por una función DC, ni se reduce el estado.

El Jacobiano completo mantiene G, masa B·M/h, historia HIGH/LOW, cargas
del BUS/filtro/VCAs/J7 y contorno. Cada integrado conserva sus cinco
terminales y su retorno a suelo; el V+ de IC1 es suelo, no el nodo134
de la voz conjunta. C4/C3/C5 y L2/L3 mantienen sus estados. Acoplamientos
fuera de los terminales y singularidades se rechazan; no hay fallback,
GMIN nuevo ni alteración de parámetros, fuentes, h o gates de Newton.
El macromodelo nominal no identifica las características de un741 vintage.

## Banco, costo y raíces

El primer intento no compila por ubicación de un módulo antes de los
comentarios internos Rust. Fallo, fuentes y replay quedan preservados;
la reparación sólo mueve esa declaración. La primera implementación
compilada pasa los candidatos pero su mediana es0.915739×: pierde costo.
Tablas de índices sustituyen búsquedas repetidas sin cambiar aritmética.
Los archivos de raíces de ambas variantes coinciden por bytes.

Cinco rondas alternadas, warmup separado,84 pares coarse/mid/end,
ON/OFF y h2/1 µs:

| Ronda | LU completa / Schur con tablas |
|---|---:|
| 1 | 1.159073× |
| 2 | 0.999933× |
| 3 | 1.134165× |
| 4 | 1.116166× |
| 5 | 1.284143× |

Mediana **1.134165×**; ganancia medida del banco, todavía sin admisión
para trayectoria. Diferencia máxima de candidatos/incrementos:
5.45805e-9 del gate2 µV/2 nA. No demuestra costo de deadline.
[Banco](../evidence/voice_dynamic_schur_bench_native03.json).

El auditor del grafo original con FD/Q Decimal100 reejecuta
**38472 ecuaciones nuevas de168 etapas/84 raíces**. Máximos de gates:
residual0.000735522 y corrección1.33894e-6. La primera ejecución del
adaptador falló por duplicar h_s en metadatos: fuente/replay preservados;
la reparación no cambia datos ni gates.
[Raíces](../evidence/voice_dynamic_schur_roots02.json).

## Correcciones, puertos y memoria

Diagnóstico separado del timing: misma J/b en396 solves. Comparación
Schur/LU completa a2 nV/2 pA: máximo0.000914976 del gate.
336 candidatas de integrado,1680 observaciones de memoria y2016
corrientes de terminal/suelo pasan. Máximo de memoria6.77626e-12 del
gate y de corriente4.33681e-19 A, frente al gate20 pA.
Estas observaciones usan la ley original sobre candidatos dinámicos;
no son un segundo oráculo físico ni un balance integrado de trayectoria.
[Observación completa](../evidence/voice_dynamic_schur_observations01.json).

Nueve regresiones finitas cubren identidad, puertos cargados con
acoplamiento entre etapas, pivotes interior/exterior, singularidades
interior/exterior y rechazo de acoplamiento extraño, entre integrados
y de retorno. [Regresiones](../evidence/voice_dynamic_schur_structure01.json).

## Gate residual rechazado, sin promoción

El cociente relativo puro alcanza1 en ambos métodos. El replay del
primer sistema conserva42 filas; Decimal100 confirma que26 también
rechazan la LU de referencia. Se registra el contraejemplo sin convertir
el rechazo en aprobado. El intento siguiente declara por anticipado un
denominador con la resolución2 nV/2 pA transportada por J.

Ese gate mixto1e-11 también falla:20 solves Schur y24 de referencia,
máximo6.13940e-8 en ambos. La observación exhaustiva no aplica un nuevo
gate ni admite los datos: registra todos los valores tras los rechazos
conservados. Una raíz Newton aceptada no borra este diagnóstico lineal.

El primer sistema que rechaza el gate mixto se guarda completo como
J/b/dSchur/dLU en binary64. Dos ejecuciones reproducen los mismos bytes
y rechazo canónico; las trazas originales siguen intactas. Decimal100
con operandos exactos confirma el rechazo: fila96 de Schur,
residuo2.5669994e-22 y cociente1.2834486e-10; fila76 de referencia,
4.4365798e-22 y2.2182873e-10.
[Sistema reproducible](../evidence/voice_dynamic_schur_scaled_inspection01.json).

**La condensación permanece como prototipo de laboratorio sin admitir
para las cuatro trayectorias completas.** La voz aceptada sigue usando
la LU anterior. No se ejecuta nueva duración, biblioteca, SPICE o audio;
248 tests Rust heredados por identidad, sin reejecutarlos. Tampoco hay
identificación física o admisión RT. [QA de alcance](../evidence/voice_dynamic_schur_tests01.json).

## Siguiente bloque acotado

Usar primero el J/b fallido guardado para ensayar refinamiento iterativo
con residuo compensado, conservando factores y reconstrucción de puertos.
Fijar antes su presupuesto y rechazo por estancamiento; no aflojar el gate
a partir del máximo observado. Luego repetir correcciones y las84 raíces,
medir costo y admitir el recorrido sólo si pasa. El gate de referencia
también requiere revisión explícita; no ocultar su rechazo con un fallback.
