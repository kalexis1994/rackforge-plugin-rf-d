# Ensamblado Radau por etapas contiguas

## Decisión y dominio previos

El perfil `hybrid_linear_profile01.json` del evaluador preparado atribuye
3,6221 s al ensamblado de matrices y 4,4326 s a la factorización. Los
timers incluyen cuatro replays; no sirven como benchmark de aceleración.
El candidato recorre etapa de fila, etapa de columna, fila local y columna
local. Referencias contiguas evitan seleccionar dinámicamente una enorme
estructura Parts por cada celda. Cada coeficiente conserva exactamente
`B[i][jj]*mass[jj][a][b] + (i==jj ? j[jj][a][b] : 0)`.

Mismas 236 filas y 118 estados HIGH/LOW, historia, cargas, frontera Schur,
perfil VCO y tarjetas CA3046/SVC-204D del control preparado. Fuentes físicas
heredadas SVC-9 pp.9/13/19 y p.10. No cambia constante audible, ley eléctrica,
integración, finitud, pivoteo, refinamiento ni condición de publicación.
Dominio de admisión nominal 40–100 ms, KEY OFF 75 ms, sin nuevo arranque/CV.

## Gates fijados antes del benchmark

- 24 pares heredados: igualdad bit a bit de todos los 236×236 coeficientes;
  192 direcciones contra solve monolítico refinado, ≤2 nV+1e-7·abs(ref).
- Rechazar enlaces inesperados entre interiores, NaN de matriz/RHS y
  recuperar el resultado válido exacto. Backward ≤1e-11, máximo tres
  refinamientos. Newton 1 pA/2 nV, estimador y cargas sin cambios.
- Dos trayectorias propias 40–100 ms, techos 64/32 µs, frente a preparado:
  nodos/estados finales ≤20 µV+2e-6·abs(ref), cargas ≤2 nA+2e-5·abs(ref),
  J7 RMS 0,1 %, pico 0,3 %, media 1 µV. Mantener los gates heredados de
  refinamiento temporal y de voz completa de 250 nodos.
- Auditar 24 pares/5712 filas originales con Amount explícito: 20 pA/2 nV.
  Se auditan candidatos nativos; no se afirma otra trayectoria original.
- Heap cero durante integración; ocho replays exactos y diez rechazos
  atómicos de paso entre las dos trayectorias.
- Benchmark sin timers internos, compilador/rlib/flags congelados y
  control preparado fresco al techo 32 µs. Ratio candidato/control ≤0,90.
  Un único ensayo acredita sólo ese costo, sin inferencia estadística/RT.

Un `tmp/lab-current`, sin WAV, biblioteca/Cargo ni muestras nuevas. Fallos
con fuentes/entrada/replay conservados antes de corregir o retirar binarios.
