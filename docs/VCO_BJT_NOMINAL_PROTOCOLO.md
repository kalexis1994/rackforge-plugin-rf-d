# BJT nominal del VCO: contrato previo

2026-10-07. Perfil documental CA3046, sin instrumento físico. Tarjetas
condicionadas de [VCO1](../evidence/vco1_laboratory_devices.json), NG-46
pp. 138–145, cotejadas con bjtload.c, bjttemp.c, bjtsetup.c, inp2q.c y
const.h de la fuente local ngspice46. No se distribuyen originales.

## Tarjeta, unidades y fronteras

IS=1e−14 A, BF=100, BR=5, VAF/IKF=0, NF/NR=1, RB/RC/RE=0,
ISE/ISC/CJS=0, XCJC=1, XTF/PTF=0. TF=1 ns y TR=3 ns.
BE: C0=7 pF/PB=.75 V/M=.5/FC=.4; BC: 3 pF/.7 V/.33/.4.
TEMP=TNOM=25 °C. Conservar la escala de la referencia:
VT=(1.38064852e−23 J/K / 1.6021766208e−19 C)·298.15 K.
No sustituir estas constantes del oráculo por otra escala ni ajustar NF/NR.
La corrección térmica nominal cancela; no se admiten otras temperaturas.

Terminales **[C,B,E,S]**, todos en −40..40 V; uBE=σ(VB−VE),
uBC=σ(VB−VC), σ=+1 NPN/−1 PNP, ambos −40..0.9 V.
Paso Euler 125 ns..1 ms; estado anterior dentro del mismo dominio.
Rechazar inputs no finitos, voltajes fuera de dominio y pasos inválidos.
No clamp, limiting o difusión alternativa para conseguir convergencia.

## Leyes y conservación

Para cada juntura, f(v)=IS·[exp(v/VT)−1] si v≥−3VT; si v<−3VT,
f(v)=−IS·[1+(3VT/(e·v))³]. Derivar ambas ramas analíticamente.
La continuación y su derivada son continuas en −3VT. qB=1 en esta tarjeta.
Corriente de transporte de C a E: σ[f(uBE)−f(uBC)].
Corrientes B→E y B→C: σ[f(uBE)/BF+GMIN·uBE] y
σ[f(uBC)/BR+GMIN·uBC], con GMIN=1e−12 S de las opciones operativas.

El sustrato omitido en una netlist de tres pines se conecta a masa por
inp2q.c. Los defaults son vertical NPN (retorno C) y lateral PNP (retorno B).
Agregar la rama GMIN entre ese retorno y S explícito; con CJS/ISS ausentes
no hay carga de sustrato. GMIN no es corriente de transporte ni difusión.
No sumar sólo tres corrientes ni afirmar aislamiento físico por este default.

QBE=Qdepl_BE+TF·f(uBE), QBC=Qdepl_BC+TR·f(uBC); sus derivadas son
Cdepl+τ·f'. Usar la primitiva de [depleción](VCO_CARGA_JUNTURA_RESULTADOS.md)
sin cambiarla. Cargas terminales: σ[−QBC,QBE+QBC,−QBE,0].
Euler añade σ·ΔQBE/dt en B→E y σ·ΔQBC/dt en B→C.
Para difusión, calcular el incremento de f por regiones con expm1 o
factorización del cociente cúbico; no restar corrientes próximas.
Historia fija durante Newton, entrega de candidato, ninguna publicación.
Jacobian físico dI/dV (S) y dQ/dV (F) 4×4; conservación de cuatro terminales.

## Banco previo y gates

Decimal100 independiente por ramas/incidencias, inputs exactos binary64.
Ocho biases por juntura: −20 V, tres floats alrededor de −3VT, 0, .3, .7,
.85 V; ambas polaridades, bases −.25/.25 V y sustrato .125 V.
Tres historias: igual, uBE=.6/uBC=−2 y uBE=−2/uBC=.6; dt125/500 ns.
**1536 vectores** con corrientes DC/transitorias, Q, ΔQ y matrices completas.
Gates por valor esperado: corriente `1e−14+3e−12·abs(I)` A;
carga `1e−23+3e−12·abs(Q)` C; ΔQ `1e−30+3e−12·abs(ΔQ)` C;
J `1e−12+3e−12·abs(J)` S; C `1e−23+3e−12·abs(C)` F.
FD terminal ±1 µV: J `2e−9+2e−6·abs(FD)` S,
C `1e−21+2e−6·abs(FD)` F. Conservación y gauge: `1e−14+1e−14·sum(abs)`
en A/S, o `1e−23+1e−14·sum(abs)` en C/F.
Probar memoria fija, historia igual, NPN/PNP, cuatro retornos, errores y
vecinos no nulos de voltaje (ΔQ error relativo ≤3e−12 sin piso absoluto).
Veinte vectores adicionales de vecinos (cinco biases por juntura y
polaridad) contrastan ΔQ directamente contra Decimal100.
Tres tests de cálculo y un test heap aislado: 10.000 stamps sin asignaciones.

Contraste independiente ejecutable ngspice46: doce escenas (seis biases:
0/0, .65/−1, −.2/.65, .65/.62, .3/.28, −.2/−1; ambas polaridades),
cuatro terminales explícitos, mismo modelo y GMIN. Q/capacidad y corriente
DC después de AC; Y=Jdc+j2π·1kHz·C por excitación separada de cuatro pines.
Gates por valor esperado: I `2e−14+1e−7·abs(I)` A, Q `1e−20+1e−7·abs(Q)` C,
C `1e−19+1e−7·abs(C)` F, Y `2e−12+1e−7·abs(Y)` S.
Usar corrientes de fuentes para incluir la rama S, no sólo @q[ic]/[ib]/[ie].
Conservar intentos, decks, exports, logs, identidad del ejecutable oficial,
compiler, fuentes antes/después y binarios. Fallo: snapshot y replay sin
cambios antes de reparar; no modificar gates para aprobar.

Alcance: subset BJT nominal con transporte, depleción y difusión; no
identifica una población CA3046 o PNP real. No admite JFET, 741 completo,
oscilación nativa, audio, deadlines ni el banco largo de voz.
