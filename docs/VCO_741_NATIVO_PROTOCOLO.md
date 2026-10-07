# LM741 nominal: stamp completo con memoria

Protocolo previo a medición. Base RF b7f5a898df245ea29b8f26de02f982386513b8ae; QA anterior 205 tests. Objetivo: residuo y Jacobiano completo del macromodelo TI LM741 usado por el VCO. No es el circuito transistor por transistor del integrado ni una medición física.

## Fuente y dimensiones

Fuente TI-LM741, archivo original local `references-local/datasheets/ti_lm741_lm741.lib`, SHA256 f58370983c8bd22bf6a59ddd05a1dd492f1a0ea60f673ffd460a356da5e693dc, subcircuito LM741 y tarjetas DX/QX; archivo de texto sin paginación. Defaults del motor ngspice 46: bjtsetup/bjtload/bjttemp, diosetup/dioload y const.h, fijados por hash en el recibo. TEMP=TNOM=25 °C y GMIN=1e-12 S, como en la referencia operativa.

26 tensiones (cinco externas, 21 internas, incluyendo nodo 49), nueve corrientes de fuentes ideales y dos corrientes de inductores: 37 incógnitas. Se conserva cada ecuación original. L2=530.5m H=0.5305 H; L3=100p H=1e-10 H. Son elementos del macromodelo, no inductores físicos del Moog. Tres voltajes de capacitor y dos corrientes de inductor son la memoria. Q=Cv y flujo=Li; el llamador sólo acepta la memoria candidata después de converger.

QX: NPN IS=1e-16 A, BF=625, BR=1, NF=NR=1; sin Early, resistencias serie, cargas de unión o tránsito. DX: IS=1e-15 A, N=1, RS=CJO=TT=0. Las tarjetas BJT del VCO son distintas. Cada unión usa exponencial hasta -3VT y continuación cúbica inversa del motor; GMIN no genera carga. Los colectores QX tienen GMIN al sustrato conectado a tierra. VT=(1.38064852e-23/1.6021766208e-19)*298.15 V. Todos los otros valores y conexiones se extraen del original inalterado y se contrastan con el stamp.

## Dominio y gates fijos

Tensiones nodales ±40 V; corrientes ideales ±1 A; cada unión semiconductor entre -40 y +0.9 V. Historia: capacitores ±80 V, inductores ±1 A. Euler implícito entre 125 ns y 1 ms. Se rechaza NaN, infinito y dominio excedido. API por valor, sin commit interno ni heap.

Banco: seis DC independientes ngspice con cinco terminales impuestos, dos candidatos por raíz, DC y cuatro modos Euler (dos historias por dos pasos): 60 stamps. Decimal100 por incidencia, sin resultados nativos como semilla. Todas las 37 columnas se contrastan con diferencias centrales, historia fija. Memoria igual al candidato anula sólo las contribuciones reactivas.

Gates Decimal: residuo nodal 1e-14 A +3e-12 relativo; filas de restricción 1e-11 V +3e-12 relativo; Jacobiano nodal 1e-12 en unidades de columna +3e-12 relativo; restricciones 1e-10 +3e-12 relativo. DC independiente: KCL interno ≤1e-11 A; restricción ≤1e-11 V; corriente externa 2e-14 A +1e-7 relativo. FD: paso 1e-6 V o 1e-9 A; error nodal 2e-9 +2e-6 relativo, restricciones 1e-6 +2e-6 relativo. Conservación incluye explícitamente corriente a tierra. Test aislado: 10000 stamps, cero asignaciones heap. No prueba deadline.

Todo intento fallido conserva fuentes, comando, salidas y repetición sin cambios antes de reparar. La admisión es del stamp y su memoria; quedan pendientes Newton propio, trayectoria del 741, integración con BJT/JFET y voz audible completa. El gate de nota larga sigue rechazado.
