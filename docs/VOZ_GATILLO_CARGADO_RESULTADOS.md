# Gatillo común cargado: Q12/Q20, C7 y C4 en la voz

2026-10-12, Model D CA3046. [Contrato](VOZ_GATILLO_CARGADO_PROTOCOLO.md),
[addendum del predictor](VOZ_GATILLO_SEMILLA_PROTOCOLO.md),
[inputs](../evidence/voice_trigger_charge_inputs02.json),
[nativo](../evidence/voice_trigger_charge_native02.json),
[oráculo](../evidence/voice_trigger_charge_reference02.json),
[QA](../evidence/voice_trigger_charge_tests01.json).

## Frontera que se cierra

RESET_DRIVER deja de ser una fuente ideal. El colector Q12 recibe CR9 y
la rama1500 Ω/CR4 del circuito C2, R25 de polarización y R28/C4. Q20,
CR10, C7/R60/R55, base Q12 y R23 producen el estado del driver a partir
del teclado y del contacto S-trigger. R36/CR8 carga RESET_BASE y se suma
al puerto CR6 existente. Es un solve simultáneo225, sin onda de reset impuesta.

Se conservan434 coordenadas del circuito217 por bytes. C7 nuevo se inicia
a0 V y C4 desde su preparación algebraica con el colector Q12 cargado;
ambas condiciones nuevas quedan declaradas, sin historia anterior de esas
cargas. Q25 colector8,3 V, SET_BASE0,01 V y RESET_BASE0,01/0,7 V siguen
impuestos. Alimentación9,3 V y las hipótesis Ebers–Moll permanecen iguales.
Q25/Q15, sus cargas de dispositivo y contorno de filtro todavía no se cierran.

## Respuesta temporal a62,5 ns

Cuatro historias propias, final decay ON/OFF, pasos125/62,5 ns, cinco tramos
de2 µs/10 µs nuevos desde5,312 ms. Las450 coordenadas se conservan en
cada cambio de estímulo. KEY alto en tramos1/2; S-trigger cerrado sólo
tramo2; RESET_BASE sube a0,7 V en tramo4. Q25/SET_BASE no se cambian.
Corriente SET_BASE positiva desde su fuente hacia el capacitor C4.

| Final decay | Tramo | C7 mV | RESET_DRIVER V | C4 V | C2 V | SET_BASE µA |
|---|---:|---:|---:|---:|---:|---:|
| ON | 0 | 3.99998988266e-11 | 0.0299571662424 | 0.0199632459931 | 3.20054519743 | 0.000607975072124 |
| ON | 1 | 1.92909329383 | 0.0299571660091 | 0.0199631256036 | 3.20054049066 | 0.00059595944927 |
| ON | 2 | 3.85780234264 | 6.92141456045 | 0.15609055503 | 3.20053986532 | -675.532400542 |
| ON | 3 | 3.85778372932 | 0.0300100643473 | 0.153395991277 | 3.20053515867 | 13.338592693 |
| ON | 4 | 3.85776511609 | 0.0295510426338 | 0.150745693913 | 3.20053045112 | 13.119465128 |
| OFF | 0 | 3.99998988266e-11 | 0.0356916921894 | 0.025029621486 | 3.19709515357 | -0.0662070703351 |
| OFF | 1 | 1.92909329383 | 0.0356909793157 | 0.0250427242829 | 3.19677774969 | -0.0648255032813 |
| OFF | 2 | 3.85780234264 | 6.92265609865 | 0.161094340172 | 3.19677713188 | -675.156175847 |
| OFF | 3 | 3.85778372932 | 0.035735505286 | 0.158414071667 | 3.19645977634 | 13.2678566381 |
| OFF | 4 | 3.85776511609 | 0.0352039498096 | 0.155776350194 | 3.19614239228 | 13.0572400384 |

El colector Q12 resuelve≈0,02996 V ON/0,03569 V OFF inicialmente, en vez

de mantenerse en0,03 V. Con S-trigger cerrado llega≈6,92 V; C4 transporta
un impulso≈−675 µA hacia SET_BASE. La carga de C4 persiste al reabrir el
contacto. No hay reset de ese capacitor o selección digital de fase.
C7 sólo llega≈3,858 mV en esta ventana: no se ha ejecutado el umbral de
teclado ni una nota completa. Estos endpoints no acreditan tiempos ADSR.

## Newton, fallo preservado y predictor

El [intento01](../evidence/voice_trigger_charge_native01.json) agota64
iteraciones en tramo2/paso0; el replay desde la misma semilla rechaza
idénticamente. El [diagnóstico](../evidence/voice_trigger_charge_diagnostic01.json)
reproduce las64 rondas mediante sólo logging. Sus voltajes son iteraciones
de Newton y no una evolución temporal del circuito.

El [predictor](../tools/repair_trigger_seed.py) mueve exclusivamente nodos
sin almacenamiento ante el salto de S-trigger. Los guesses no cambian
C2/C7/C4 ni la memoria entrante, y no fuerzan la raíz aceptada a su tensión.
Mismos64/24 presupuestos, ecuaciones y gates. Los dos primeros tramos,
incluida la frontera del fallo, siguen idénticos por bytes en el registro
textual y los checkpoints. [Fuente/bytes anteriores](../evidence/voice_trigger_charge_failure_bytes01.json)
conservados antes de reparar. Ese predictor no elige un estado de Q25/Q15.

## Contraste y restauración

480 pasos originales/720 repetidos,40 restores completos de tramo desde
inicio/mitad: candidatos, incrementos, ratios, iteraciones/trials y
checkpoint final por bits. RFLTRG01/3664 bytes conserva reloj/paso/tramo,
cuatro fuentes, contactos y450 componentes; demás parámetros por receta
protegida. Dieciséis corrupciones concretas rechazadas. Alcance de escena
condicionada y replay de tramo, sin preset genérico o calendario completo.

40 pares seleccionados/80 candidatos,**18000 ecuaciones independientes**:
VCO Decimal100 y grafo Python/FD central1 µV. Mayor ratio residual
0.00215553301397; corrección
4.20977853022e-07, gates1.
40 endpoints contrastan400 corrientes a1 nA: ramas C2, Q25, interfaz interna
del driver, RESET_BASE total, KEY, SET_BASE/C4 y suministro9,3 V.
SET_BASE/C4 se calcula desde los incrementos de ambas etapas, no sólo
inferido por KCL. La interfaz interna del driver sigue observada y no se
cuenta como una fuente externa después de cerrar Q12.

C2/C18/C27/C7/C4 cierran ΔQ+∫I_dc por cada tramo y total a1 pA·duración.
Las ramas C2 y la reacción de C4/SET_BASE cierran sus identidades. La
cuadratura de etapas nativas3/4,1/4 es explícita; no es integración
independiente de todos los pasos. Doce comparaciones al mismo reloj pasan
2 µV/2 nA, máximo ratio0.000270476076766.

## Reparación del adaptador de observaciones

El [auditor01](../evidence/voice_trigger_charge_reference01.json) rechaza
la presentación de C4 por un ULP: convertía a float después de restar
SET_BASE en Decimal; Rust suma high/low a float y luego resta SET_BASE.
[Prueba del adaptador](../evidence/voice_trigger_charge_observer_adapter01.json)
retiene ambos bits, error3,469e−18 V y corrientes que ya pasaban. Se cambia
sólo esa expresión de formato: el intento02 usa las mismas fuentes/datos,
KCL/corrección, gates numéricos y campaña nativa sin reintegrarla.

Campaña49.822 s, oráculo14.7004 s. Biblioteca congelada;
248 tests Rust heredados por identidad, no reejecutados. Sin audio nuevo,
SPICE, identificación vintage, heap/deadline o RT. El antiguo banco SPICE
Gummel–Poon conserva su admisión propia; no se traslada a estos BJTs sin
las cargas de dispositivo correspondientes.

## Próximo cierre

Incorporar Q25/Q15 y su carga no lineal coherente con las corrientes,
conservando C2/C4/C7 y los puertos que ahora reciben cargas reales. Mantener
la selección causal y refinamiento de conmutación como gates explícitos.
El gatillo cargado está admitido en esta ventana; latch causal, ADSR
completo, contorno de filtro, VCO2/3 y adaptación225 siguen pendientes.
