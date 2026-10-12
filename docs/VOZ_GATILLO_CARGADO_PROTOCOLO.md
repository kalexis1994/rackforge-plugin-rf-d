# Gatillo común cargado y memorias C7/C4

Contrato previo, 2026-10-12, Model D CA3046. Cerrar RESET_DRIVER/Q12
sobre el [circuito217](VOZ_C2_CARGA_RESULTADOS.md), manteniendo explícitos
Q25 colector, SET_BASE/Q25 base y RESET_BASE/Q15 base. La admisión
[SPICE de contorno](CONTORNO_PLACA4_RESULTADOS.md) usa Gummel–Poon;
no se hereda a estos BJTs Ebers–Moll sin sus cargas de dispositivo.

Fuentes: SVC-9 Fig.9-7 p.9, tabla7-6 pp.26–27 y Fig.9-15 p.17;
[grafo revisado](../evidence/loudness_contour_graph.json). Q12/Q20 NPN,
CR10/CR8 1N34A con las mismas hipótesis: IsBJT1e−14 A, βF100/βR5,
298,15 K; diodos Is1e−8 A/n1,5, sin cargas de juntura identificadas.
R25=3300 Ω y base Q12=10000 Ω, candidatos del esquema con conflicto BOM
conservado; no barrer ni adjudicar una población vintage en este banco.

Nodos217..224: RESET_DRIVER, TRIGGER_COLLECTOR, Q12_BASE, Q20_BASE,
KEY_RC, KEY_DIODE_K, C4_LEFT, RESET_DIODE_A. C7=0,1 µF a masa en221;
C4=0,01 µF entre223 y SET_BASE=0,01 V fijo. Tolerancias±10 % documentadas,
nominales aquí. R23/R25 hacia9,3 V, R55=47 kΩ, R60=100 kΩ,
R28/R36=10 kΩ, R49=220 Ω hacia masa sólo con S-trigger cerrado.
C4 y CR8 exponen sus corrientes hacia el biestable todavía impuesto.

RESET_DRIVER deja de ser fuente: su fila recibe la carga CR9/1500 Ω de
la red C2, con ambos términos cruzados y componentes low. Incorporar
CR8 al total de corriente de RESET_BASE, además de CR6. No duplicar
conductancia o corriente estática del driver de C2 al cerrar sus puertos.

Cuatro perfiles propios, final decay ON/OFF y h125/62,5 ns. Preservar434
componentes del final217 por bytes; sólo ocho incógnitas nuevas se añaden.
Preparar siete nodos algebraicos con C7=0 impuesto y C4 abierto a DC,
recibiendo las tensiones entrantes de SUSTAIN_DRIVER_EMITTER/FAST_DIODE_K.
La nueva condición C7=0 y C4=(C4_LEFT−0,01) se declara como inicialización,
sin historia dinámica previa. No recalcular ninguna carga anterior.

Inicio2785017856 ticks, tick125 ns/65536. Cinco tramos2 µs,10 µs nuevos:

| Tramo | KEY V | S-trigger | RESET_BASE V |
|---|---:|---|---:|
| 0 | 0 | abierto | 0,01 |
| 1 | 10 | abierto | 0,01 |
| 2 | 10 | cerrado | 0,01 |
| 3 | 0 | abierto | 0,01 |
| 4 | 0 | abierto | 0,7 |

Q25 colector8,3 V y SET_BASE0,01 V son fronteras independientes,
no estado de un latch identificado. Teclado/S-trigger son estímulos,
sin atribuir a10 µs un Note On/Off completo. Al saltar KEY, recuperar el
dominio de CR10 sólo con guess KEY_DIODE_K≈KEY−0,5 V; nunca alterar C7.
Retirar el guess destinado a una fuente RESET_DRIVER que ya no existe.

225 incógnitas/dos etapas Radau. Primer/último par:40 pares/80 candidatos,
18000 ecuaciones independientes, gates2e−11 A/2e−10 V y corrección
1 µV/1 nA.480 pasos originales y720 repetidos,40 restores
completos de tramo. Checkpoint3664 bytes: magic RFLTRG01, reloj/paso/tramo,
Q25/KEY/RESET_BASE/SET_BASE, flags final_decay/S-trigger, reservado0,
450 componentes. Receta restante protegida. Dieciséis corrupciones
magic/NaN/tramo/fuente se rechazan antes de avanzar.

Refinamiento de225 incógnitas, semillas y cinco finales por ON/OFF:
2 µV/2 nA.40 endpoints contrastan400 corrientes (cuatro ramas C2,
Q25, carga interna RESET_DRIVER, RESET_BASE total, KEY, SET_BASE/C4 y9,3 V),
gate1 nA, más voltajes. SET_BASE/C4 medido por incrementos de etapas,
no sólo inferido desde KCL. Balances C2/C18/C27/C7/C4 por tramo/total
a1 pA·duración y composición de ramas. Cuadratura Radau nativa3/4,1/4,
sin afirmar integración independiente de todos los pasos.

Compilación120 s, perfil300 s, campaña1500 s, oráculo300 s; stack32 MiB,
reserva1 GiB/salida32 MiB. Fallos/fuentes/replay conservados antes de
reparar, mismos gates. Biblioteca congelada y248 tests heredados por
identidad. Sin nuevo audio/SPICE, ADSR completo, latch causal, hardware o RT.
