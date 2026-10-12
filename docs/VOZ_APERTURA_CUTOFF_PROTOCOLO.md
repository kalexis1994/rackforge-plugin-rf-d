# Apertura del cutoff: diagnóstico de nivel de la cadena

2026-10-12, contrato previo. La escena de voz tiene OSC1 ON a alpha=0,5,
R61=200 Ω, RANGE=0,1, cutoff=0,5 y ambos controles de VCA=2 V.
J7 aparece en decenas de µV: estudiar el control físico de cutoff antes
de aplicar ganancia de escucha. No cambiar componentes ni trims.

Usar los tres puntos DC de66 nodos ya admitidos de
`evidence/circuit66_dc_vectors.json`: cutoff=0/0,5/1, mismo RANGE/R61.
Extender cada uno con BUS=0 V y C10_LEFT=pin6 (nodo22), capacitores abiertos.
El kernel nativo exporta DC, G en S y C en F, desde `chain_charge` a125 ns.
El oráculo anterior monta sus KCL y diferencias centrales a1/2 µV;
estampa C desde las incidencias originales. No resolver una nueva raíz ni
mezclar el estado corregido de la voz con estos DC independientes.

BUS es una fuente ideal de1 V **de normalización infinitesimal**, y las
otras fuentes/control/rieles tienen movimiento AC cero. Resolver
(G+jωC)v=0 en los67 nodos restantes, con vBUS=1. Frecuencias: fundamental
del candidato fijo anterior y armónicos2/4/8. Observar todas las tensiones,
J7, carga vista en BUS y corrientes de capacitores. Comparar matrices y
soluciones, con residuos de cada operador; ambos solves complejos usan
NumPy, no son dos implementaciones independientes de álgebra lineal.

Gates: DC≤2e−11 A; matriz G≤1e−10 S +1e−4 relativo; C≤1e−16 F;
estado AC≤1e−10 V/V +5e−4 relativo; entrada≤1e−10 S +5e−4 relativo;
residuo complejo≤1e−11 A/V. Repetir las FD a ambos tamaños. Estos gates
contrastan numeración y linealización; no son tolerancias vintage ni
predicción no lineal de una onda de1 V. No inferir el nivel de una nota
desde pequeña señal ni generar WAV desde fasores.

Biblioteca/compilador congelados, sin biblioteca nueva. Compile≤120 s,
export≤120 s, auditor≤120 s; presupuesto total480 s, reserva disco1 GiB,
estimación8 MiB, stack32 MiB. Conservar logs, inputs, matrices y hashes.
Fallo: fuente y excepción/repetición idéntica antes de reparar el auditor.
La siguiente trayectoria debe usar el control elegido y sus cargas propias.
