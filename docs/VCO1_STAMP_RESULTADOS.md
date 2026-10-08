# VCO1: circuito nativo ensamblado

2026-10-07. Pasó el [protocolo previo](VCO1_STAMP_PROTOCOLO.md), para el
perfil CA3046 nominal a 25 °C. El
[módulo](../crates/rf-d-circuit/src/vco1_stamp.rs) reúne convertidor,
ambos 741 completos, las dos mitades E402 con fuente común, Schmitt/reset,
waveformers, panel y referencia −4 V. No hay timers ni rampas impuestas
en sus ecuaciones. Aún no ejecuta una trayectoria autónoma nativa.

## Grafo y memoria

100 elementos de placa/panel y dos macromodelos TI de 41 elementos:
180 elementos expandidos, 98 voltajes y 36 corrientes, **134 incógnitas**.
Las filas de pines se acumulan en los nodos físicos compartidos y en masa,
incluidos suministro de IC1 y sustratos BJT. Los trims conservan corrientes
explícitas y admiten contactos exactos R=0. C4 conserva perfiles 10/100 pF.

El estado entrante conserva por identidad de nodo seis capacitores
exteriores, seis de 741, cuatro corrientes de inductores, 28 cargas BE/BC
y cuatro GS/GD. Historia fija, candidato completo sin mutación entrante.
La frontera actual posee R6/R45, SW6 3/10, alpha=.5 y ON con bus impuesto;
para unirla con el mixer activo habrá que transferir esas cargas una vez.
Los seis CV son voltios independientes de placa, sin interpretación MIDI.

## Contrastes

[Referencia independiente](../evidence/voice_vco1_stamp_reference08.json):
netlist congelada más incidencias Decimal100, sin leer el algoritmo Rust.
40 casos × 949 columnas, incluyendo DC, Euler125/250/500 ns, historia
igual/distinta, endpoints R8/R11, CV separados, carga NEG4 y bus.
Las 534 posiciones potencialmente no nulas se guardan como formato disperso;
el test reconstruye **las 718.240 entradas, incluidas las cero**.

| Medición nativa | Máximo |
|---|---:|
| Diferencia de residuos frente a Decimal100 | 2,7852795807e-17, en unidades de cada fila |
| Diferencia de Jacobiano | 9,9920072216e-16, en unidades de cada entrada |
| Balance de 98 KCL más retorno a masa | 5,0483163656e-18 A |

[Producción](../evidence/voice_vco1_stamp_native02.json): tres tests
eléctricos y uno de heap aislado. Pasaron las 5.360 columnas por FD,
repetición pura, controles independientes, candidatos y rechazo de dominios.
1.000 stamps completos, cero asignaciones; no mide Newton ni deadline.

Cuatro procesos ngspice frescos en el último banco: DC condicionado de
arranque C1=0 y transitorio original de 200 us para cada C4. La corriente
de la fuente que impone C1=0 se exporta: −16,3999493384 uA. Se incluye en
KCL y retorno; máximo DC 5,6675620114e-14 A y restricciones
8,8817841970e-16 V. Transitorios completos con 515/513 filas, misma
frontera nominal. Sus snapshots excitan stamps; no prueban trayectoria
Euler nativa, refinamiento temporal, frecuencia o calibración nativa.

## Rechazos conservados

- Reference01: DC libre falla; mismo comando repetido. No se admite ese DC.
- Reference02: DC condicionado queda en 1,1652e-11 A; falla gate 1e-11.
- Reference03: DC más estricto pasa; transitorio estricto aborta a 5 ns.
- Reference04: nominal completo pasa; arranque con trims calibrados y
  CV=-1.1 V falla. Ese alcance sigue abierto.
- Reference05: cuatro procesos completos; adaptador de endpoints cuenta
  contactos V como fuentes nuevas. Se corrige sólo identidad R/V.
- Native01: derivación Eq incompatible con el Error del 741 congelado;
  compile y replay exactos retenidos. Se quita Eq sólo del nuevo módulo.
- Un error de sintaxis intermedio del helper tiene fuente y replay privados.

Los exports fallidos existentes se copiaron/hasharon antes del replay;
no se sobrescribe su original. References06/07/08 pasaron; 08 liga el
módulo final después de corregir Eq. **27 procesos SPICE en total**, incluidos
cuatro replays fallidos. Los gates eléctricos permanecieron iguales.
Se conservan las fuentes medidas de los ocho bancos y ambas compilaciones.

## Admisión y siguiente bloque

[QA de publicación](../evidence/voice_vco1_stamp_tests01.json):
**217 controles, cuatro ejecutados y 213 heredados por identidad**.
Reconstruye el banco, reabre los exports completos y verifica compiler,
fuentes/binaries, archivos privados y el
[snapshot de portadas](../evidence/voice_vco1_stamp_documentation01.json).

Admitido el ensamblaje DC/Euler del circuito para su frontera documentada.
Sigue Newton conjunto con arranque propio y rechazo atómico, seguido por
trayectoria autónoma/refinamiento y carga activa del mixer. No admite voz
instalable, RT o fidelidad vintage. La nota larga previa sigue rechazada;
no hay audio nuevo ni se cambia el alcance de las escuchas existentes.
