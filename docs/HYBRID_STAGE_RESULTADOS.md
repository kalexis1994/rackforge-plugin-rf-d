# Radau contiguo: mismo sistema y menor costo

## Perfil y transformación

Sobre la voz preparada nominal CA3046/SVC-204D, 40–100 ms, el
[perfil](../evidence/hybrid_linear_profile01.json) midió:

| Sección instrumentada | Segundos acumulados |
|---|---:|
| Evaluación eléctrica completa de Newton | 6,5756 |
| Ensamblado Radau de Newton | 3,6221 |
| Inspección/CSR del solver | 1,8637 |
| Factorización de interiores y frontera | 4,4326 |
| Sustitución triangular inicial | 0,8636 |
| Residual compensado inicial | 0,1482 |
| Refinamiento | 0,0048 |

Los timers incluyen los cuatro replays exactos. No cubren de forma
separada todo el line search ni solves rechazados; no sumar esta tabla
como desglose exhaustivo del tiempo sin instrumentar. El costo de armar
matrices justificó cambiar su recorrido antes de alterar el solver.

El [generador](../tools/prepare_hybrid_stage.py) deriva una variante del
evaluador preparado. Recorre bloques de etapa contiguos y mantiene una
referencia a la fila de masa/Jacobiano, evitando seleccionar dinámicamente
Parts de gran tamaño por celda. Conserva la fórmula f64 de cada entrada,
todos sus ceros y chequeos; el solver Schur admitido sigue intacto.
No modifica leyes eléctricas, HIGH/LOW, cargas, perfil VCO o constantes.

## Verificación

[Protocolo previo](HYBRID_STAGE_PROTOCOLO.md),
[recibo nativo](../evidence/hybrid_stage_native01.json) y
[auditoría original](../evidence/hybrid_stage_audit01.json):

- 24 matrices/1.336.704 coeficientes iguales bit a bit entre las fórmulas.
- 192 direcciones frente a solve monolítico refinado: máximo 0,972279
  del gate 2 nV+1e-7·abs(ref). Es un contraste numérico condicionado,
  cercano al gate en una dirección; no identifica parámetros físicos.
- 24 NaN de matriz, dos enlaces inesperados entre interiores y un NaN
  del RHS rechazados, cada uno seguido de recuperación válida exacta.
- Dos trayectorias propias a techo 64/32 µs: 962 observaciones, 24 pares
  seleccionados y estados finales iguales al preparado. También iguales
  sus líneas ROOT/GRID/SOLVER serializadas, antes del FINAL cronometrado.
- 99.922 solves, 499 refinamientos; backward máximo ≤9,9852e-12.
  Newton ≤0,999722 pA/1,87210 nV; estimador máximo 0,950788.
- Auditoría de 5712 filas originales, Amount retenido:
  ≤0,719007 pA/0,325050 nV. Evalúa candidatos nativos contra ecuaciones
  originales; no produce una segunda trayectoria original independiente.
- J7 frente a voz completa: RMS ≤1,067158 %, pico ≤2,607925 %,
  media ≤0,088947 µV. C2/C5, BUS y R59/R60 pasan; refinamiento temporal
  pasa con J7 RMS 5,926e-8 relativo. Gates exteriores intactos.
- Heap cero en integración, ocho replays de paso exactos y diez rechazos
  atómicos. Las 48 etapas, 472 columnas FD y 26 guardas eléctricas del
  bloque previo se heredan por identidad de los fuentes, sin reejecutarlas.

## Costo sin instrumentación

| Ejecución | Tiempo por 60 ms simulados |
|---|---:|
| Preparado fresco, techo 32 µs | 21,1009861 s |
| Contiguo, techo 64 µs | 18,4173257 s |
| Contiguo, techo 32 µs | 18,7063310 s |

Ratio comparable **0,886515**, bajo el gate previo 0,90: **11,35 % menos
costo en este ensayo**. Un único benchmark secuencial; sin inferencia
estadística, otro host/escena o deadline. Sigue siendo una cadena offline.

Compiler/rlib congelados, sin Cargo, biblioteca ni audio nuevos. Recibos
nuevos ~1,35 MB antes de QA; un área temporal, vacía tras retirar semilla
y ejecutables. Se conservan las 4012 fuentes y 8769 inputs privados previos.
[QA](../evidence/hybrid_stage_tests01.json).

Siguiente paso: reducir materialización e inspección densa de la matriz
sobre el mismo sistema, empezando por el costo CSR/factorización medido.
Mantener todas las entradas reales, puertos y cargas; una estructura
dispersa debe rechazar enlaces nuevos inesperados. Arranque, CV general,
antialias de producción, fidelidad física y tiempo real siguen pendientes.
