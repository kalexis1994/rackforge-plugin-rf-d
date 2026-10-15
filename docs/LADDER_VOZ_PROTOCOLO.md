# Ladder reconstruido dentro de las dos etapas de voz

## Contrato previo al ensayo

Integrar el kernel [local admitido](LADDER_ALGEBRAICO_RESULTADOS.md) en la
misma voz nominal CA3046/SVC-204D 40–100 ms, KEY OFF 75 ms. Semilla,
VCO, controles, fuentes SVC-9 pp.9/13/19 y p.10, leyes y cargas originales.
No ampliar arranque/CV general/fidelidad física/RT. No descartar memoria.

Retener 111 coordenadas por etapa: todos los nodos físicos salvo los
siete algebraicos, sustituyendo los tres nodos derechos 67/68/69 de voz
por las diferencias de ladder V8−V12, V9−V13, V10−V14. Los nodos de
voz 54 VCA_BASE y 55 TAIL conservan identidad. Cuatro memorias internas,
cinco puertos y todos los capacitores del padre aparecen una sola vez.

En cada evaluación, avanzar las coordenadas compensadas desde el estado
anterior, resolver siete ecuaciones locales y reconstruir 118 nodos.
Retener el incremento HIGH/LOW de las coordenadas; reconstruir los
incrementos algebraicos desde el estado anterior. Para cada rama derecha,
incremento físico = incremento izquierdo − incremento diferencial. No
calcular los incrementos dinámicos restando endpoints redondeados.

Con x=T[z,y], las filas retenidas son T_yᵀF: tres filas negativas de las
ramas derechas y las otras filas físicas directas. Evaluar el grafo completo
reconstruido; J reducido = T_yᵀ J (T_y+T_z dz/dy). Masa reducida =
T_yᵀ M T_y, verificando M T_z=0 y T_zᵀM=0 en la unión completa.
La memoria dinámica no depende de z. Usar ambas etapas y B original;
el sistema temporal tiene 222 incógnitas, frente a 236 del control.

Derivar el solver directo para 108 incógnitas de contorno, 110 de audio
y cuatro puertos temporales. Conservar inspección de todas las entradas,
CSR, backward 1e-11, máximo tres refinamientos, pivoteo, capacidades,
limpieza entre solves y rechazo de enlaces entre interiores.

## Gates heredados y comprobaciones nuevas

- Fixtures de 24 ROOT/48 etapas directas: reconstrucción ≤2 nV, pertenencia
  de masa y filas algebraicas sin carga exactas, DC/cargas ≤20 pA. FD de
  coordenadas del sistema reducido: 2 nS+2e-5·abs(FD), paso 1 µV.
- Comparar direcciones temporales reconstruidas con el sistema completo:
  2 nV+1e-7·abs(ref), con mismo residual y estado localmente reconstruido.
  Esto incluye el residual algebraico remanente al interpretar la comparación.
- Trayectorias propias 64/32 µs, 481 observaciones cada una; comparar con el
  directo: nodos/estados 20 µV+2e-6·abs(ref), cargas 2 nA+2e-5·abs(ref),
  J7 RMS 0,1 %, pico 0,3 %, media 1 µV. Conservar también gates de voz
  completa reservada y refinamiento del ensayo anterior.
- Newton original 1 pA/2 nV: el criterio de salida comprueba el residual
  físico completo y su corrección con el solver directo original, además
  de la dirección reconstruida del reducido. No converger sólo por las
  filas retenidas ni cambiar su unidad. Estimador original en 118 nodos.
- Auditoría independiente de 24 pares/5712 filas originales con Amount:
  20 pA/2 nV; no es otra trayectoria independiente. Ocho replays, diez
  rechazos atómicos de paso y heap cero en las dos trayectorias.
- Control directo fresco 32 µs, mismo compilador/rlib/flags/equipo, sin
  timers internos: ratio candidato/control ≤0,90. Separar unión numérica
  verificada de admisión por costo; conservar motor activo si falla.

El solve local parte del z del estado anterior en cada evaluación; no
reutiliza factores ni publica semillas de intentos rechazados. Probar
entradas no finitas, estados no canónicos, h/presupuesto/controles y
recuperación válida exacta. El estado del llamador se publica sólo si el
paso completo y el estimador pasan. Área única `tmp/lab-current`; retirar
binarios después de recibos, sin nuevos WAV/Cargo/rlib/inputs privados de
sonido. Antes de cualquier corrección, preservar fuentes/input/replay.
