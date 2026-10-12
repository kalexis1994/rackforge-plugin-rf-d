# C2 y carga/descarga conectados a la voz

2026-10-12, Model D CA3046. [Contrato previo](VOZ_C2_CARGA_PROTOCOLO.md),
[inputs](../evidence/voice_c2_charge_inputs02.json),
[nativo](../evidence/voice_c2_charge_native02.json),
[oráculo](../evidence/voice_c2_charge_reference01.json),
[QA](../evidence/voice_c2_charge_tests01.json).

## Cambio del modelo

C2 deja de ser fuente ideal dentro de VCO1→J7. El estado217 contiene
C2=10 µF, Q16/Q17/Q18/Q19, resistencias de ataque/decay/sustain, CR9 y
CR4/1500 Ω para decay final OFF. La corriente del seguidor Q3 se devuelve
a C2 con ambos signos y derivadas cruzadas. Panel recibido en resistencias
eléctricas, sin taper inventado. Valores/dispositivos y su incertidumbre
son los del contrato, sin ajustes nuevos para obtener una curva.

Biestable/gatillo separados mediante colector Q25, colector Q12/reset
driver y base Q15/reset. Se impone9,3 V; Q26 y contorno de filtro ausentes.
Un calendario de fuentes no constituye selección causal de rama o nota MIDI.

## Memoria e inicialización

Cuatro perfiles propios desde los finales del banco205, pasos125/62,5 ns
y final decay ON/OFF. Las410 coordenadas anteriores permanecen por bytes.
C2 nuevo recibe3,2 V/32 µC nominal: pre-carga declarada desde la frontera
previa, sin historia dinámica anterior de este capacitor. Sólo once nodos
algebraicos nuevos se preparan mediante el grafo Python a C2 fijo.

Cada perfil continúa50 µs, cinco tramos de10 µs, desde5,262 ms absolutos.
Cambiar una fuente conserva434 componentes. El guess de Newton puede
mover209/210/214/216 para recuperar el dominio de junturas tras un salto;
no modifica el historial ni delta inicial205. Sus límites0,5/0,6 V son
decisiones numéricas, no umbrales de ataque o límites del capacitor.

## Resultados a62,5 ns

Corrientes positivas desde C2 hacia cada rama. J7 mantiene tip/ring32 Ω y
R21 inferior2000 Ω. Endpoints transitorios, no amplitudes por ciclo ni
tiempos de un contorno identificado.

| Final decay | Tramo | C2 V | Volumen V | J7 mV | Ataque µA | Decay µA | CR4 µA |
|---|---:|---:|---:|---:|---:|---:|---:|
| ON | 0 | 3,19999687871 | 2,05159732508 | 2,99197650020 | −0,00000283549 | 3,07120106179 | 0 |
| ON | 1 | 3,20060009895 | 2,05219788986 | 2,92634453944 | −603,240457939 | ≈0 | 0 |
| ON | 2 | 3,20059697167 | 2,05219477634 | 2,85730829519 | −0,00000283549 | 3,07719875535 | 0 |
| ON | 3 | 3,20057343782 | 2,05217134609 | 2,78679815615 | −0,00000283549 | 23,4836556514 | 0 |
| ON | 4 | 3,20054990421 | 2,05214791608 | 2,71576869596 | −0,00000283549 | 23,4834203789 | 0 |
| OFF | 0 | 3,19999687872 | 2,05159732508 | 2,99197650020 | −0,00000283549 | 3,07120106180 | −0,000001 |
| OFF | 1 | 3,20060009895 | 2,05219788986 | 2,92634453944 | −603,240457939 | ≈0 | −0,000001 |
| OFF | 2 | 3,20059697167 | 2,05219477634 | 2,85730829520 | −0,00000283549 | 3,07719875538 | −0,000001 |
| OFF | 3 | 3,19900425551 | 2,05060907184 | 2,78475776170 | −0,00000283549 | 23,4679680666 | 1568,66786962 |
| OFF | 4 | 3,19741259963 | 2,04902442387 | 2,71184304497 | −0,00000283549 | 23,4520558068 | 1567,62387063 |

ON omite CR4: corriente exactamente cero. Su slot algebraico de cátodo
queda como extremo muerto de R1500 al driver; no carga C2 ni añade un
resistor epsilon. El grafo de referencia reproduce esa reducción.
OFF conserva fuga inversa del modelo, conecta la rama real y descarga C2.
ΔC2(OFF−ON) final=−3,13730458683 mV en ambas resoluciones; integral de
CR4≈31,373359718 nC. Las otras ramas también responden, por lo que no
se atribuye toda la diferencia de estado exclusivamente a esa integral.

El reset driver recibe≈1,6283 mA ON y≈3,1959 mA OFF al final. Estas cargas
deberán entrar en el cierre de Q12: mantener ideal su voltaje aquí no
demuestra que el gatillo completo pueda mantenerlo. Los tres puertos se
registran separados y no se ocultan bajo las fuentes impuestas.

## Admisión numérica y checkpoint

2400 pasos originales,3600 repeticiones y40 restores de inicio/mitad:
todos los pares restantes hasta el final del tramo reproducen por bits
candidatos, incrementos, ratios, iteraciones/trials y checkpoint final.
RFLC2C01/3528 bytes guarda reloj/paso/tramo, tres fuentes, decay final y
434 componentes; otros parámetros por receta protegida. Dieciséis
corrupciones concretas se rechazan. Alcance de escena y replay de tramo,
sin afirmar preset genérico o replay de todo el calendario desde cualquier punto.

40 pares seleccionados/80 candidatos: **17360 ecuaciones independientes**,
VCO Decimal100 y grafo Python/FD central1 µV de cadena/seguidor/drivers.
Mayor ratio residual0,00215583294; corrección4,21036171e−7, gates1.
40 endpoints emitidos por Rust contrastan280 corrientes (cuatro ramas de
C2/tres fuentes), gate1 nA, además de C2/volumen/J7.

C2/C18/C27 cierran ΔQ+∫I_dc por tramo y total a1 pA·duración. Las integrales
de ataque/decay/seguidor/CR4 cierran la integral DC205. Cuadratura nativa
Radau3/4,1/4, sin propagación independiente de cada paso. Doce comparaciones
de semillas/finales al mismo reloj pasan2 µV/2 nA, ratio máximo0,000270077633.

## Fallo y recursos

[Intento01](../evidence/voice_c2_charge_native01.json) y replay idéntico:
declaración de módulo anterior a comentarios internos e índice sin tipo
usize. [Bytes y fuentes originales](../evidence/voice_c2_charge_failure_source_bytes01.json)
preservados; reparación sólo de declaraciones, mismas leyes/Newton/gates.
El wrapper selecciona otro recibo/directorio. No se recompiló la biblioteca.

Perfiles:71,395/146,086/68,358/170,668 s, campaña457,645 s;
oráculo15,378 s. Stack32 MiB/reserva1 GiB.248 tests Rust heredados por
identidad y no reejecutados; sin tests nuevos de biblioteca, audio, SPICE,
medición de heap/deadline, identificación vintage o RT.

## Próximo cierre

Conectar biestable/gatillo causal con C2 y los tres puertos ya cargados,
manteniendo explícita la ambigüedad y dinámica rápida omitida. No usar el
calendario como emulación de fases ADSR. Contorno de filtro, VCO2/3 y
controlador adaptativo217 continúan pendientes.
