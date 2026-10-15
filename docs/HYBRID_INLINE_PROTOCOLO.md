# Fronteras internas de la evaluación eléctrica

## Decisión previa

El perfil vigente `hybrid_electrical_profile01.json` separa modos FULL y
residual. En FULL mide validación/proyección 0,1108 s, audio 1,4385 s,
contorno 1,0017 s y transferencia/construcción 1,6897 s. En residual mide
0,0706/0,6121/0,5325/0,1739 s respectivamente. Incluye replays y overhead
de timers; no acredita ahorro ni atribución causal de copias en el binario.

El candidato añade inline(always) a cinco fronteras: linearize de cadena,
DC/parts de contorno, linearize de volumen y filtro. Permite al compilador
ver el uso de estructuras devueltas grandes y eliminar temporales/campos
no consumidos. La transformación no cambia ninguna instrucción eléctrica,
validación, fórmula, orden de suma, solver, flag de compilación o constante.
Todos los fuentes admitidos permanecen intactos, con variantes derivadas.

Voz nominal CA3046/SVC-204D, 40–100 ms, KEY OFF 75 ms, misma semilla,
perfil VCO, 118 estados HIGH/LOW, puertos y cargas. Fuentes físicas
heredadas SVC-9 pp.9/13/19 y p.10. Los helpers siguen dentro de su dominio
prevalidado; no ampliar arranque, CV general ni fidelidad física.

## Gates fijados antes del benchmark

- Derivación exacta desde los fuentes anteriores; diferencias limitadas
  a cinco anotaciones y enlaces de módulos. 48 etapas: DC/dQ
  ≤20 pA+1e-7·abs(ref); Jacobiano/masa ≤2e-9 S+2e-7·abs(ref), estado
  reconstruido exacto. FULL/residual conservan DC/dQ dentro del gate.
- 472 columnas FD ±1 µV, incluidas fronteras compartidas:
  ≤2e-9 S+2e-5·abs(FD). Tres configuraciones inválidas y 26 entradas de
  etapa inválidas, con retries exactos en ambos modos.
- Dos trayectorias propias, techos full 64/32 µs: 962 observaciones y
  estado final frente a directo. Nodos 20 µV+2e-6·abs(ref), cargas
  2 nA+2e-5·abs(ref), J7 RMS 0,1 %, pico 0,3 %, media 1 µV. Mantener
  gates heredados de voz completa y refinamiento temporal.
- Auditoría original de 24 pares/5712 filas con Amount: 20 pA/2 nV;
  candidatos nativos auditados, sin otra trayectoria original independiente.
- Newton 1 pA/2 nV, backward ≤1e-11, hasta tres refinamientos y mismo
  estimador. Heap cero en integración, ocho replays y diez rechazos atómicos.
- Control directo fresco al techo 32 µs; mismos compiler/rlib/flags/equipo,
  sin timers internos. Costo candidato/control ≤0,90. Un único ensayo no
  demuestra estabilidad estadística, otro host o deadline de producción.

Un `tmp/lab-current`; retirar semilla/ejecutables tras guardar recibos,
fallos con fuente/entrada/replay antes de corregir. Sin nuevos WAV, muestras,
Cargo o biblioteca. Código fuente inline no prueba layout ni stack máximo.

## Primer rechazo y siguiente transformación

Las cinco anotaciones pasan todos los gates numéricos pero cuestan
1,005726 del control fresco: rechazo por el mismo gate 0,90, fuente,
entrada y replay guardados en `hybrid_inline_native01.json`.

El siguiente conserva las cinco anotaciones y cambia la transferencia
de matrices de hijos: copia filas de contorno tras verificar finitud;
las filas propias de audio, inicialmente cero, reciben sus 68 columnas
por siete tramos contiguos de la permutación original. Se usa +0+valor
para conservar la acumulación previa, incluido cero con signo. Las filas
compartidas VCA_BASE/TAIL mantienen suma de contribuciones no nulas y
comprobación posterior de overflow. No se omiten columnas ni se aprende
soporte de una escena; se mantienen finitud, leyes y cargas originales.
Mismos contrastes eléctricos/FD/guardas/voz y control fresco, sin cambiar
el gate 0,90. El costo eventual corresponde al conjunto de cambios.
