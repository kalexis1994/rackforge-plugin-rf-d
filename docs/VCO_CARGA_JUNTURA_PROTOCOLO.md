# Cargas de juntura: contrato previo del núcleo VCO

2026-10-07. Primitive de carga de depleción para las tarjetas condicionadas
de [VCO1](VCO1_ORACULO_CIRCUITO.md). No es un BJT/JFET completo.
NG-46 pp. 138–145/152–154; parámetros y procedencia en
[las tarjetas](../evidence/vco1_laboratory_devices.json). Código primario
ngspice46 `jfetload.c`/`jfettemp.c` coteja el caso M=0.5 y su continuación.

## Ley, unidades y memoria

Para capacitancia C0 (F), potencial PB (V), grading M y FC adimensional:
`C(v)=C0·(1−v/PB)^(−M)` y
`Q(v)=C0·PB/(1−M)·[1−(1−v/PB)^(1−M)]`, cuando `v<FC·PB`.
Para `v≥vf=FC·PB`, usar continuación cuadrática de Q y lineal de C,
con `Cf=C0·(1−FC)^(−M)` y `Sf=Cf·M/[PB·(1−FC)]`:
`Q(v)=Q(vf)+Cf·(v−vf)+Sf·(v−vf)²/2`; `C(v)=Cf+Sf·(v−vf)`.
Q y C son continuas. El voltaje es de ánodo a cátodo; Q e I son entrantes
al ánodo. El terminal opuesto recibe −Q/−I.

Euler implícito: `I=[Q(v)−Q(vprev)]/dt`, `G=C(v)/dt`. La historia es el
voltaje de juntura aceptado que determina Q(vprev), fijo durante Newton.
El helper entrega candidato Q, C, ΔQ, I y G; no modifica ni confirma estado.
Implementar ΔQ mediante integrales por regiones y log1p/expm1, evitando
restar dos cargas próximas. No sustituir ΔQ por C(v)·Δv.

Dominio de la primitive: v/vprev −40..40 V, C0≥0, PB>0, 0≤M<1,
0≤FC≤0.95; inputs/outputs finitos y dt>0. Validar overflow y rechazarlo.
Esta extensión de carga no admite voltajes directos del dispositivo
exponencial, nuevas temperaturas o parámetros físicos. Su futuro binding
deberá conservar las correcciones térmicas del modelo operativo.

## Banco previo

Cuatro tarjetas a su temperatura nominal: CJE=7 pF/PB=.75 V/M=.5/FC=.4,
CJC=3 pF/PB=.7 V/M=.33/FC=.4, CGS=3.3 pF/PB=1 V/M=.5/FC=.5 y
CGD=5.4990908339470075 pF con el resto como CGS. Son las hipótesis de
laboratorio existentes, sin identificarlas como población vintage.

Por tarjeta: 20 voltajes con polaridad inversa/directa, casi cero y tres
floats alrededor del splice; ocho historias (incluyendo el float vecino,
historia igual y cruces del splice); dt=125/500 ns. **1280 vectores**.
Referencia Decimal de 100 cifras: Q directa y ΔQ por resta a esa precisión,
independiente de la integral estable del helper. Convertir inputs con
Decimal.from_float para preservar los floats realmente evaluados.

Gates por valor esperado: Q `1e−24 + 1e−12·abs(Q)` C,
C `5e−24 + 1e−12·abs(C)` F,
ΔQ `1e−30 + 1e−12·abs(ΔQ)` C,
I `1e−22 + 1e−12·abs(I)` A,
G `5e−20 + 1e−12·abs(G)` S. Derivadas centrales ±1 µV:
C/G con `1e−21 + 1e−5·abs(FD)` F o el correspondiente valor dividido por dt.
Probar continuidad, memoria fija, historia igual, capacitancia cero,
rechazos y pasos en el splice. Heap aislado: 10000 companions con cero
asignaciones. Compiler/comandos/binarios se conservan; sin SPICE/audio.

No agregar corriente de transporte/difusión, transconductancia, temperatura,
limiting o GMIN por este resultado. Las cuatro tarjetas y el helper son
un componente del futuro VCO; no admiten el oscilador o su sonido completo.
