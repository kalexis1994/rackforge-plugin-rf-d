# Entrada Q29/C27 directa: protocolo previo

2026-10-07. Perfil nominal CA3046 y cadena condicionada de 66 nodos.
SVC-9 Fig. 9-11, p. 13, Fig. 9-8, p. 10, panel Fig. 9-17, p. 19.
R54=470 Ω, C27=10 µF; [partes](../evidence/filter_input_board4.json).
Tarjetas BJT, R61=200 Ω/200 kΩ, controles y demás ramas permanecen
como en [el cierre anterior](MEZCLADOR_CADENA_PROTOCOLO.md).

## Cambio y dominio solicitado

Agregar `mixer_chain66_direct` y `mixer_chain_port_direct`; conservar los
módulos anteriores y el núcleo `circuit66` por bytes exactos. Reutilizar
el puerto pasivo ON/C27, sus corrientes y memoria. Reconstruir sólo la fila
BASE_Q29 en el Jacobiano natural: R54 + base Q29 + corriente del puerto.
Así no se resta `C27/dt` de una diagonal que ya contiene ese término.

`r6=(x6−x4)/470 + IS·[expm1((x6−x5)/VT)/BF + expm1((x6−x8)/VT)/BR] + I_BASE`.
`VT=kB·T/q`; `gf=IS·exp((x6−x5)/VT)/VT`, `gr=IS·exp((x6−x8)/VT)/VT`.
Columnas 4/5/6/8: `−1/470`, `−gf/BF`,
`1/470+gf/BF+gr/BR+Y_BASE_BASE`, `−gr/BR`, en siemens.
IS/BF/BR/T provienen de la tarjeta condicionada de la cadena; no se
identifican como valores de transistores vintage. Las demás filas se
conservan de `circuit66::linearize` con el BUS provisional.

Dominio solicitado del nuevo adaptador: **125 ns..1 ms**. El adaptador
antiguo conserva **0.5 µs..1 ms**. Ningún resultado de este banco admite
pasos menores o el VCO completo. No se cambia Euler implícito, Newton,
presupuesto 1..16 iteraciones/halvings, predictor o fallback.

## Banco y gates

Referencia independiente: BUS y cursores como incógnitas, sistema completo
67/71 nodos, DC y trayectoria propios. Dos R61 × una/cinco rutas ON ×
500/250/125 ns = **12 escenas de 16 pasos**. α=0.5; fuentes bipolares
impuestas ±[0.08,−0.05,0.03,−0.02,0.04] V, con cambio cada cuatro pasos.
No contiene oscilación autónoma ni cobertura de una nota musical.

Conservar gates anteriores: nodos y memorias <1 µV, corrientes <1 nA;
KCL <10 pA, constraint <10 pV y corrección completa <10 nV. Contrastar
J4/J5/J7, BUS, 17 memorias, C10 y seis corrientes. Repetir 64 pasos del
oráculo anterior a 48 kHz para verificar la zona compartida del dominio.

Verificar las 66 columnas del Jacobiano a historia fija mediante diferencias
centrales ±1 µV en los doce estados del cuarto paso. Gate original:
`1e−8 + 2e−5·|FD|`, unidades de cada fila. Contrastar también la fila
directa contra el stamp físico R54/Q29/C27 bajo su frontera.

Puerto cargado: en esos doce estados, cinco fuentes ±1 mV y raíces nodales
independientes. Gates originales de admitancia `1e−8 + 1e−3·|FD|` S y
gradientes `1e−6 + 1e−3·|FD|` V/V. Verificar repetición y fuentes omitidas.
Una red activa no requiere reciprocidad. La memoria anterior permanece
fija durante todos los trials; sólo se confirma el candidato final conjunto.
Fallo de presupuesto o dominio conserva el estado del llamador.

Heap: 32 pasos completos y 16 solves de puerto por cada paso temporal,
con asignador aislado después del constructor. Cero asignaciones no prueba
deadline. Conservar compilador, flags, comandos, stdout y binarios privados.
No lanzar SPICE ni producir audio por este banco.

El productor de oráculos fija sus fuentes antes/después; preservar su
primer rechazo y replay intacto antes de cualquier reparación. La QA
hereda 185 controles con sus inputs numéricos idénticos, registra los
exports añadidos y sólo agrega tests nuevos ejecutados en producción.
