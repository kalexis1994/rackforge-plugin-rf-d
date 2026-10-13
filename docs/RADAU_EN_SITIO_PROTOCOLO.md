# Ensamblaje de Radau en dos destinos inicializados

2026-10-13, antes de medir. Base9b89edb, QA3350 fuentes/7884 privados.
El perfil privado del conjunto reducido sitúa linearize≈50.26% del step.
Una intervención: cambiar la vida del Stamp y su publicación interna,
manteniendo Parts, ecuaciones, solver Schur y controlador intactos.

## Alcance eléctrico y numérico

CA3046 condicionado: VCO1→BUS→ladder/VCAs/J7 y contorno cargado por R59/Q18.
[Partición admitida](SCHUR_CADENA_RESULTADOS.md), fuentes y revisiones allí
documentadas. No añade constantes físicas, elimina cargas o identifica
semiconductores vintage. Estado229 HIGH/LOW,458 correcciones, masas,
historia, puertos compartidos y fronteras impuestas conservados.

Stamp::initialize escribe residual/J/candidatas en un destino inicializado.
Misma evaluación parts0? antes de parts1?, mismos rechazos tempranos.
Residual: dc_i+B_i0·Q0/h+B_i1·Q1/h. J_ij=B_ij·M_j/h+δij·G_i;
conservar multiplicaciones/sumas y el cero del término diagonal ausente.
No omitir coeficientes cero, dividir fórmulas por escalas o cambiar precisión.
Reponer cada uno de los458×458 coeficientes antes de resolver.

En step, dos buffers locales seguros contienen Stamp actual y trial.
Aceptar sólo (incrementos,corrección) y permutar referencias a buffers;
no devolver el Stamp grande en Option ni intercambiar sus matrices por valor.
Un trial rechazado no modifica el Stamp actual o estado publicado. La
inicialización posterior repone todo su destino. linearize conserva una
fachada compatible. blank devuelve un inicializador constante; no afirmar
copias eliminadas del binario sin inspección adicional. Sin unsafe/heap nuevo,
cache de factores/J, cambio de line search, tolerancias o presupuesto.

## Experimento finito

84 parejas congeladas ON/OFF,2/1 µs, coarse/mid/end. Exigir identidad por
bits de1834 campos, iteraciones y trials contra el Schur de cadena intacto.
Conservar también LU original/packet y sus gates de candidatos. Warmup
separado y cinco rondas alternadas, mediana>1; si1<mediana≤1.10, confirmar
una sola vez el mismo ejecutable/packet y exigir ambas medianas>1.
Si falla utilidad, conservar la variante y seguir con el motor admitido,
sin otra hipótesis de optimización en este bloque.

Exigir identidad de396 J/b/correcciones de banco con la traza admitida;
sólo entonces heredar181368 filas Decimal100. Raíces84 por bytes permiten
heredar38472 ecuaciones; contar la herencia, sin llamarla reejecución.
Probar inicialización fresca/repetida, matrices y residual completos por
bits, HIGH/LOW, candidatas, cambio de historia/control/dt, fallo en cada
etapa y recuperación de scratch. Probar rechazo atómico y no reutilizar
un Jacobiano de otro trial.

Si pasa precisión/costo, reejecutar cuatro recorridos propios8.438→11.442 ms
con el mismo controlador. Comparar todos los archivos de estados, etapas,
replays, checkpoints, balances y eventos con la campaña admitida por bytes,
separando ejecutables/timers de datos. Si todo coincide, heredar sus gates
del grafo y comparaciones229 al mismo reloj; si no, no heredar y conservar
el rechazo antes de cualquier reparación/admisión. Sin extender duración.

Compilar120 s, banco/auditor600 s, perfil990 s, campaña4000 s; stack32 MiB,
64 MiB nuevos privados, reserva1 GiB.248 tests Rust heredados por identidad.
Preservar fallo/replay antes de reparar. Sin biblioteca/SPICE/audio nuevos,
arranque de contorno desde silencio, fidelidad física o DSP/RT admitidos.
