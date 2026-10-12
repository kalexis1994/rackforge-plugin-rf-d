# C2 dinámico con ataque, decay, sustain y seguidor cargado

Contrato previo, 2026-10-12. Model D CA3046. Extender el
[circuito205](VOZ_SEGUIDOR_CONTROL_RESULTADOS.md) a217 incógnitas.
SVC-9 Fig.9-7 p.9, tabla7-6 pp.26–27; panel Fig.9-17 p.19 y tabla7-3
p.21; decay final Fig.9-15 p.17. Conectividad revisada en el
[grafo de contorno](../evidence/loudness_contour_graph.json) y
[derivación](CONTORNO_VOLUMEN_CIRCUITO.md).

C2=10 µF a masa, tolerancia documental−10/+50 % sin barrido en este
banco nominal. R13 ataque10 kΩ, R16 decay100 kΩ, R19 sustain inferior
2500 Ω/total5000 Ω: resistencias eléctricas, no curvas de potenciómetro.
Q16/Q19 PNP, Q17/Q18 NPN; Ebers–Moll Is1e−14 A, βF100/βR5,298,15 K.
CR9/CR4 silicon Is1e−12 A, n1,5. Hipótesis heredadas sin identificación
vintage; sin capacitancias de juntura nuevas. Alimentación9,3 V impuesta.

Tres terminales ideales quedan separados: RESET_COLLECTOR (Q25 colector),
RESET_DRIVER (Q12 colector) y RESET_BASE (Q15 base/CR6). Se omiten latch,
gatillo, Q26 y cargas del contorno de filtro. No seleccionar raíces del
biestable mediante este calendario de fuentes.

| Tramo,10 µs | Q25 colector V | Reset driver V | Reset base V |
|---|---:|---:|---:|
| 0 | 8,3 | 9 | 0,7 |
| 1 | 0,05 | 9 | 0,7 |
| 2 | 8,3 | 9 | 0,7 |
| 3 | 8,3 | 0,03 | 0,7 |
| 4 | 8,3 | 0,03 | 0,01 |

Valores heredados de guesses/escenarios del laboratorio anterior; no
estados de latch identificados ni tiempos attack/decay físicos. Cuatro
perfiles: final decay ON/OFF, h125/62,5 ns, duración nueva50 µs.
Inicio2758803456 ticks, tick125 ns/65536. Semillas propias finales del
banco205;410 coordenadas preservadas por bytes. C2 nuevo se pre-carga a
3,2 V (32 µC nominal) desde la frontera anterior: condición inicial
declarada, no carga obtenida por integrar la historia del capacitor.
Preparar sólo once nodos algebraicos nuevos a C2 fijo mediante el grafo
Python independiente; no recalcular las cargas previas de la voz.

Nodos205..216: C2, base/colector Q16, panel attack, emisor Q17, base y
colector Q18, wiper/base/emisor/colector Q19, cátodo CR4. Acoplar C2↔base
Q3 por R16 placa10 kΩ en ambas KCL/Jacobiano; nuevo almacenamiento sólo
en205. ON elimina CR4; el slot de cátodo se conserva con R1500 hacia el
driver, como rama terminal sin corriente. Es algebraicamente equivalente
a eliminar esa rama muerta, sin resistor epsilon o carga del capacitor.

Radau de dos etapas, gates Newton originales. Cuando cambia una fuente,
una semilla algebraica limitada a junturas≤0,5/0,6 V puede recuperar el
dominio exponencial; sólo modifica el guess en209/210/214/216, nunca el
historial o delta inicial205. Umbrales de guess numéricos, no parámetros
del sonido. Todos los trials reutilizan la misma memoria entrante.

Checkpoint3528 bytes: magic RFLC2C01, ticks, half_ticks, tramo, tres
fuentes f64, final_decay u32/reservado0 y434 componentes high/low.
Receta restante fija y protegida. Inicio/mitad de cada tramo:40 restores
con replay completo de tramo,3600 pasos repetidos frente a2400 originales.
Conservar cambios de fuente por bytes y rechazar magic/NaN/tramo/fuente.
Refinamiento de217 incógnitas:2 µV/2 nA al mismo reloj, semillas y cinco
finales por ON/OFF. Primer/último par:40 pares/80 candidatos/17360 ecuaciones
independientes (VCO Decimal100, grafo Python y FD central1 µV).
Gates seleccionados2e−11 A/2e−10 V, corrección1 µV/1 nA, puertos1 nA.

Cada tramo y total: ΔQ_C2+∫I_dc205=0, además de C18/C27, a1 pA·duración.
Descomponer I_C2 en ataque, decay, seguidor y CR4, signos salientes de C2.
Integrar corrientes hacia la red desde Q25/reset driver/reset base.
Cuadratura Radau nativa3/4,1/4; no alegar oráculo de todos los pasos.
La influencia ON/OFF y signos de ramas se reportan; no ajustar valores
para obtener una curva de contorno ni presentar50 µs como una nota larga.

Compilación120 s, cada perfil300 s, campaña1500 s, referencia300 s;
stack32 MiB, disco reserva1 GiB/salida estimada32 MiB. Archivar errores,
fuentes y replay antes de reparar; no relajar gates. Biblioteca congelada,
248 tests Rust heredados por identidad, sin nuevo audio/SPICE/RT.
