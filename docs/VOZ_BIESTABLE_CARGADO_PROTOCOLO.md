# Biestable cargado en la voz nativa

Protocolo previo a medición, 2026-10-12. Revisión CA3046 de
[objetivo](OBJETIVO.md), sin unidad física. Continúa el
[gatillo cargado](VOZ_GATILLO_CARGADO_RESULTADOS.md).

## Circuito y dispositivo

SVC-9 figura 9-7, PDF p.9; panel figura 9-17 p.19 y tabla 7-6 pp.26–27.
Se usa el grafo revisado `evidence/loudness_contour_graph.json` completo:
Q25/Q15, R38/R39 10 kΩ y R56 33 kΩ cierran los tres terminales antes
impuestos. R59 68 kΩ sigue cargando la base del VCA de la cadena.
C2 10 µF, C7 0.1 µF y C4 0.01 µF conservan sus memorias; C4 queda entre
C4_LEFT y SET_BASE, con las cuatro entradas de su matriz de masa.
R25 3.3 kΩ y resistencia de base Q12 10 kΩ siguen siendo alternativas
documentales condicionadas. Ataque 10 kΩ, decay 100 kΩ y sustain inferior
2.5 kΩ/total 5 kΩ son posiciones eléctricas de laboratorio.

Todos los diez BJT de esta placa mantienen Ebers–Moll: Is=10⁻¹⁴ A,
βF=100, βR=5, T=298.15 K; CR6/8/10 Is=10⁻⁸ A y CR4/9 Is=10⁻¹² A,
n=1.5. Son hipótesis explícitas. Sólo Q25/Q15 reciben almacenamiento
intrínseco compatible: BE C0=7 pF, Vp=.75 V, m=.5; BC C0=5 pF,
Vp=.7 V, m=.33; FC=.4; TF=1 ns y TR=3 ns.
Procedencia y limitaciones: [banco de carga](BIESTABLE_CARGA_NO_LINEAL.md),
[modelo intrínseco](BJT_INTRINSECO_CARGA_CONSERVATIVA.md).
No son parámetros identificados del 2N3392. Q=Qdepleción+T·Is·expm1(V/Vt),
dQ/dV=Cdepleción+T·Is·exp(V/Vt)/Vt; corriente estática sin doble conteo.
Incrementos nativos integran C por regiones y usan expm1 para difusión;
correcciones high/low de primer orden conservan la historia.
Dominio de juntura ±40 V y exponente ≤45. Se audita contra Q a Decimal100.
Las otras junturas de placa 2 siguen sin carga intrínseca.

## Inicialización, calendario y refutación

229 coordenadas, high/low normalizados. Se heredan por bits las 450
coordenadas del final225 propio para final decay ON/OFF y paso 125/62.5 ns.
Cuatro nuevos nodos tienen bias inicial declarado: SET_BASE=.01 V,
RESET_COLLECTOR=8.3 V, RESET_BASE=.7 V, ATTACK_GATE_LOWER=.05 V.
No es un equilibrio completo; se inicia su relajación conservando C2/C7/C4.
Las cuatro cargas BE/BC nuevas se inicializan con ese bias y su ley fija.

Inicio absoluto 2790260736 ticks de 125 ns/65536. Cinco tramos de 2 µs.
KEY=[0,10,10,0,0] V; S cerrado=[false,false,true,false,false]. No se impone
ningún estado del latch ni se conmuta RESET_BASE desde una fuente.
Cuatro perfiles: final decay ON/OFF × h=31.25/15.625 ns. Herencia desde
125/62.5 ns respectivamente, con cambio de paso declarado.
Newton conserva 64 iteraciones/24 halvings y gates de 10⁻¹³ A,
10⁻¹¹ V para restricciones; corrección 2 nV/2 pA. Semilla de Newton cero;
ningún predictor elige nodos del latch con almacenamiento.

Auditor independiente de grafo original/FD y VCO Decimal100 en primer y
último par de cada tramo. Gate 20 pA/0.2 nV, corrección 1 µV/1 nA.
Refinamiento de todas las coordenadas al mismo reloj: 2 µV/2 nA.
Balance C2/C7/C4 y cargas terminales Q25/Q15: 1 pA × duración.
Dos restores por tramo repiten todos los pasos restantes por bits,
incluidos incrementos, candidatos, Newton y contadores. Cuatro corrupciones
por perfil se rechazan. Fronteras preservan 458 coordenadas por bits.

Presupuesto por perfil 300 s; campaña 1500 s, compilación 120 s;
auditor 300 s, salidas privadas ≤32 MiB con reserva de 1 GiB.
Fallos y repetición idéntica se preservan antes de reparar. Estos gates
admiten la ventana local del circuito condicionado; no una trayectoria
de contorno completa, NOTE ON por KEY, fidelidad vintage, audio nuevo ni RT.
