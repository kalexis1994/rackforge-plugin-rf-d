# JFET nominal E402 del VCO: contrato previo

2026-10-07. Perfil CA3046 documental; una mitad NJF del E402 dual.
La otra mitad usa la misma tarjeta, con fuente común en el grafo y mismatch
cero impuesto. No hay instrumento físico de referencia.
[Tarjeta y derivación](../evidence/vco1_laboratory_devices.json): NG-46
pp. 152–154, eq. 7.25; DS-E402-S77 PDF p.114/impresa 3-81. Código primario
local ngspice46: jfetload.c, jfettemp.c, jfetacld.c, jfetask.c y jfetset.c.
Los originales y exports de laboratorio quedan ignorados, fuera de Git.

## Leyes y dominio

LEVEL=1, B=1, VTO=−2.5 V, BETA=.0003018867924528302 A/V²,
LAMBDA=.003/V, RD=RS=0 Ω, IS=1e−14 A, N=1, GMIN=1e−12 S.
CGS=3.3 pF, CGD=5.4990908339470075 pF, PB=1 V, FC=.5, grading=.5.
TEMP=TNOM=25 °C: conservar VT=(1.38064852e−23/1.6021766208e−19)·298.15 V.
La corrección térmica nominal cancela; otras temperaturas/varianzas pendientes.
Estos valores son hipótesis condicionadas, no fit de población física E402.

Terminales **[D,G,S]**, voltajes −40..40 V, vGS/vGD −40..0.9 V,
vDS=vGS−vGD en −40..40 V. dt Euler 125 ns..1 ms; historia igual dominio.
Rejectar no finitos, voltajes fuera de dominio y pasos inválidos. Sin clamps,
limiting, resistencias o relajación de gates para conseguir convergencia.

Orientar el canal al extremo con menor voltaje: h=abs(vDS),
u=(vGS si vDS≥0; vGD si vDS<0)−VTO y s=signo de vDS (positivo en cero).
Para u≤0: Icanal=0. Para 0≤h≤u: F=h·(2u−h); para h>u: F=u².
I_D→S=s·BETA·(1+LAMBDA·h)·F. Derivar analíticamente respecto de los
terminales físicos, incluyendo derivadas de h/u en modo inverso.
Es la reducción exacta de la ley Sydney University de ngspice con B=1,
porque Bfac=(1−B)/(PB−VTO)=0. No promoverla como modelo para otro B.

Corrientes G→S/G→D: f(v)+GMIN·v. f(v)=IS·[exp(v/VT)−1] si v≥−3VT;
si v<−3VT: f(v)=−IS·[1+(3VT/(e·v))³]. GMIN no pertenece a la carga.
Corrientes entrantes: [Icanal−IGD,IGS+IGD,−Icanal−IGS].
QGS/QGD son las leyes de depleción ya admitidas; no hay difusión JFET.
Cargas terminales [−QGD,QGS+QGD,−QGS]. **No intercambiar CGS/CGD al
invertir el canal.** Matrices dI/dV en S y dQ/dV en F, completas 3×3.
Euler añade ΔQ/dt por las ramas físicas con historia fija; candidato sin
publicación de estado. Reutilizar la primitiva estable sin modificarla.

## Banco antes de medir

Decimal100 por ramas/incidencias, preservando floats de juntura formados
por el interfaz binary64. Trece biases de cada juntura: −20 V, tres floats
alrededor de VTO, −.2 V, tres alrededor de −3VT, 0 V, tres alrededor de .5 V
y .85 V. Dos gates comunes −.25/.25 V, tres historias: igual, GS/GD=−1/−3
y −3/−1; dt125/500 ns. **2028 vectores**. Incluyen corte, regiones lineales,
saturación, inversión, vDS=0 y fronteras. Veinte vecinos extra: diez
voltajes (−20,−3,−2.5,−.2,−3VT,0,1e−24,.49,.5,.85) por GS/GD.

Gates por valor esperado: I `1e−14+3e−12·abs(I)` A; Q `1e−24+3e−12·abs(Q)` C;
J `1e−12+3e−12·abs(J)` S; C `5e−24+3e−12·abs(C)` F;
ΔQ `1e−30+3e−12·abs(ΔQ)` C. Vecinos no nulos: relativo ≤3e−12, sin piso.
FD terminal ±1 µV: J `2e−9+2e−6·abs(FD)` S; C `1e−21+2e−6·abs(FD)` F.
Conservación/gauge: `1e−14+1e−14·sum(abs)` A/S y `1e−23+1e−14·sum(abs)` C/F.
Verificar memoria fija, historia igual, simetría DC al permutar D/S, y
asimetría de capacitancia física. Tres tests eléctricos, más 10.000 stamps
completos sin heap en un test aislado. Heap cero no acredita deadline.

Ngspice46 independiente: doce GS/GD: (0,0), (−3,−4), (−4,−3),
(−1,−1.5), (−1.5,−1), (−1,−2.5), (−2.5,−1), (−1,−4), (−4,−1),
(.5,.2), (.2,.5), (−.2,−1). Gate común .17 V y tres pines explícitos.
DC y AC1kHz por excitación de cada pin, Y=Jdc+j2πfC. Gates: I
`2e−14+1e−7·abs(I)` A, Q `1e−20+1e−7·abs(Q)` C,
C `1e−19+1e−7·abs(C)` F, Y `2e−12+1e−7·abs(Y)` S.

**Semántica del export:** en MODEINITSMSIG, ngspice guarda capacitancia en
JFETqgs/qgd, aunque @j[qgs]/[qgd] conserven etiqueta de carga. Leerlos como
C sólo después de AC. Para Q, hacer transitorio de bias constante 250 ns
con paso máximo125 ns, comprobar cobertura/export de voltajes y leer las
cargas de estado finales antes de AC. No confundir F y C ni presentar este
transitorio impuesto como oscilador autónomo.

Congelar fuentes/modelos/protocolo antes/después; conservar compiler,
comandos, outputs, logs y binarios. Fallo: snapshot y replay idéntico antes
de reparar, manteniendo física y gates. Resultado nominal de una mitad;
741, unión de las mitades en circuito y oscilación nativa requieren sus
propias pruebas. No amplía fidelidad física, audio o la campaña larga.
