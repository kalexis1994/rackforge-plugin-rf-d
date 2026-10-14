# Condensación dinámica de contornos y cadena de audio

## Resultado admitido

La voz híbrida nominal conserva sus **118 incógnitas HIGH/LOW y todas
sus cargas**. Se condensa cada Jacobiano Radau de 236 filas en dos
interiores de 108/124 incógnitas y una frontera exterior de **cuatro
incógnitas**: VCA_BASE y TAIL en ambas etapas. Se reconstruye la
dirección completa antes de Newton, publicación y estimación temporal.
Es una reducción del solve lineal; no reduce el número de memorias
físicas o reemplaza contornos/filtro/VCA por curvas impuestas.

La LU con frontera conserva el acoplamiento dinámico de ambas etapas.
Se verifica cada no cero real para rechazar enlaces entre interiores
fuera de los puertos. Se recalculan factores por Jacobiano; ningún
factor viejo se usa con otra historia o h. El perfil VCO, la escena
40–100 ms y el gatillo OFF a 75 ms permanecen iguales.

[Protocolo](HYBRID_SCHUR_PROTOCOLO.md),
[banco admitido](../evidence/hybrid_schur_native04.json),
[ecuaciones originales](../evidence/hybrid_schur_audit01.json).

## Equivalencia y cargas

Dos recorridos propios con techos full 64/32 µs, 5279/5280 pasos;
481 relojes de salida por recorrido y los 118 estados finales.
Frente a la voz híbrida previa:

| Métrica | Máximo observado |
|---|---:|
| J7 RMS relativo | 1,588e-14 |
| J7 pico relativo | 2,940e-14 |
| J7 error medio | 1,090e-18 V |
| J7/C2/C5/BUS fracción del gate | 3,111e-11 |
| R59/R60 fracción del gate | 1,362e-10 |
| Estado final completo, fracción del gate | 2,491e-11 |

El control fresco reproduce exactamente la grilla/estado final del
control archivado. Cargas, memorias, reloj y aceptación permanecen
contrastados; equivalencia numérica no significa igualdad de cada bit
de los dos métodos de factorización.

Siguen pasando los gates contra la referencia completa de 250
incógnitas: J7 RMS **1,0672 %**, pico **2,608 %**, C2/C5/BUS y R59/R60.
La nueva factorización conserva el error del VCO periódico ya admitido;
no acredita fidelidad al instrumento físico. Refinamiento de techos
mantiene la cobertura limitada descrita en la unión anterior.

24 pares reconstruidos, **5712 filas originales** con cursor Amount
explícito: máximo residual 0,71901 pA y corrección 0,32505 nV, gates
20 pA/2 nV. Auditoría independiente de candidatos, sin nueva trayectoria
original. 192 RHS en 24 sistemas locales: fracción de diferencia de
dirección ≤0,382687 frente al monolítico refinado, mismos gates.
Tres rechazos de frontera/RHS inválidos y retries exactos pasan.

99922 solves lineales observados entre los dos recorridos, con 501
refinamientos; incluyen replays seleccionados. Backward máximo final
9,993e-12 dentro de 1e-11. Inicial llega a 1,037e-8 en trayectoria:
comprobar reconstrucción y refinar es necesario. Máximo 1138 no ceros
reales. Newton conserva 1 pA/2 nV y el estimador previo sin cambios.
Ocho replays exactos y diez rechazos atómicos de paso entre candidatos.

## Costo y límites

Compiler, rlib, tramo, techo y plataforma iguales; control ejecutado
de nuevo en el mismo banco. Tiempo de integración, fuera de IO:

| Recorrido | Tiempo para 60 ms simulados |
|---|---:|
| Híbrido monolítico fresco, techo 32 µs | 28,1617 s |
| Condensado, techo 64 µs | 23,7264 s |
| Condensado, techo 32 µs | 23,7608 s |

Ratio comparable **0,843728**, gate previo ≤0,90: **15,63 % menos
costo** en este ensayo. La mejora incluye LU con frontera, paso de
matriz prestada y evitar la matriz Radau completa en trials que sólo
necesitan residual. No se atribuye toda la mejora a Schur aislado.
Cero heap durante integración. Medición de una plataforma/escena;
no es un benchmark estadístico ni un deadline garantizado.

La cadena sigue offline y mantiene el coste de sus stamps detallados.
Sin arranque autónomo, CV/panel generales, banda de producción, plugin
tocable o tiempo real. No se añadieron constantes audibles.

## Rechazos conservados y almacenamiento

1. La referencia lineal monolítica sin refinamiento produjo una
   diferencia de 22,069 veces el gate. Mismas matrices/RHS: tres
   refinamientos compensados del control reducen la fracción a 0,648,
   sin cambiar el Schur. [Diagnóstico](../evidence/hybrid_schur_diagnostic01.json)
   y [fallo/replay](../evidence/hybrid_schur_native01.json).
2. El primer Schur correcto tardó 1,03847 del control: rechazado por
   costo. [Recibo](../evidence/hybrid_schur_native02.json).
3. La frontera triangular bajó a 0,93493: también rechazada por el
   mismo gate 0,90. [Recibo](../evidence/hybrid_schur_native03.json).
4. La versión final evita construir Jacobiano completo en trials de
   residual y pasa matrices prestadas. Pasa los gates originales de
   precisión, memoria, señal/cargas y costo. No se aflojaron umbrales.

Fuentes, entradas acotadas, métricas y replays comprimidos conservados
con restitución SHA256. Un solo `tmp/lab-current`, vacío tras medir;
ejecutables y semilla retirados. Sin Cargo, biblioteca, cache, WAV,
carpeta de muestras ni input privado de sonido nuevos.

Siguiente: reducir el costo de evaluación eléctrica sobre esta frontera
verificada, conservando incidencias, cargas y Jacobiano; luego ampliar
arranque/ataque y controles con escenas reservadas. No asumir que una
frontera pequeña convierte por sí sola la cadena en un motor de audio.
