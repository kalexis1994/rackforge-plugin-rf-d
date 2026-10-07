# LM741: stamp nominal completo admitido

2026-10-07. [Protocolo previo](VCO_741_NATIVO_PROTOCOLO.md), [fuentes y DC independientes](../evidence/voice_lm741_reference09.json), [compilación de producción](../evidence/voice_lm741_native02.json), [QA vigente](../evidence/voice_lm741_tests01.json). Admisión de cálculo y memoria del macromodelo TI a TEMP=TNOM=25 °C.

## Qué se implementó

`lm741.rs` entrega residuo y Jacobiano de 37 incógnitas: 26 voltajes, nueve corrientes de fuentes ideales y dos corrientes de inductores. Conserva el nodo 49, las fuentes POLY/controladas, las uniones QX/DX y sus límites, tres capacitores y dos inductores. Los cinco estados son candidatos por valor; cada intento de Newton recibe la misma historia aceptada. Se mantienen todas las filas, sin reducción del polo L2.

QX tiene BF=625, BR=1 e IS=1e-16 A y no tiene carga semiconductor en esta tarjeta. Por ello se implementa su ley nominal específica, distinta al BJT del VCO. El retorno de sustrato GMIN a tierra participa en conservación. Las cinco memorias pertenecen a C4/C3/C5/L2/L3. El macromodelo no equivale a transistores físicos del 741 ni identifica la unidad Moog ausente.

## Evidencia ejecutada

- Seis DC ngspice independientes con los cinco terminales impuestos: offsets, modo común, regiones lineales y sobrecarga diferencial. Se extraen todas las incógnitas y las cinco corrientes externas. EOS es convertido por ngspice a XSPICE; su corriente se extrae como `-@q.xop.q2[ib]`, KCL del nodo 7, que sólo conecta base Q2 y EOS. Esta extracción usa datos de ngspice, sin resultados nativos.
- 60 casos Decimal100 por incidencia obtenida del original: dos candidatos por raíz, DC y cuatro historias/pasos Euler. Se contrastan las 1369 entradas del Jacobiano en cada caso y todas las 37 columnas con diferencias centrales manteniendo historia fija.
- Historia igual al candidato, dependencia de cada uno de los cinco estados, pureza de llamadas repetidas y rechazo de dominio. Corriente total incluyendo tierra conservada.
- Cuatro tests nuevos de producción: tres funcionales y uno aislado, 10000 stamps con cero asignaciones heap. 209 cubiertos = cuatro nuevos +205 heredados por identidad; los heredados no se reejecutaron.

| Medición máxima | Error absoluto |
|---|---:|
| Residuo nodal vs Decimal100 | 8.649561644182013e-17 A |
| Restricciones vs Decimal100 | 7.571559752870410e-16 V |
| Jacobiano nodal vs Decimal100 | 3.330669073875470e-15, según unidades de columna |
| Jacobiano de restricciones vs Decimal100 | 0 |
| Corrientes externas vs ngspice | 1.040834085586084e-17 A |

## Intentos conservados

Los recibos reference01/02 conservaron un conteo de inventario erróneo (42 en lugar de 41 dispositivos); se repitió sin cambios antes de corregir. reference03..07 conservaron fallos de exportación: nombre POLY de XSPICE, sustitución de `$` y comillas del path de wrdata. Cada proceso fallido conserva repetición del mismo comando, fuentes y logs; un diagnóstico `display` se conserva en el caso03. Los gates físicos y numéricos permanecieron iguales.

reference08 pasó, y native01 preservó/reprodujo errores de compilación por literales Rust sin cero inicial. La auditoría conserva también un error de sintaxis propio y una comparación
bit a bit del voltaje impuesto cuyo export difiere por una ULP; para este
último se usa el gate previo de restricción ideal de 1e-11 V. No se cambió
el gate del circuito. Ambos fallos tienen fuente exacta y replays.

La corrección de sintaxis motivó reference09 fresco para ligar el banco al módulo definitivo. Los bancos08/09 son idénticos por bytes; native02 pasó. Se conserva la compilación fallida, no se presenta como un fallo del circuito.

Hubo 23 lanzamientos ngspice locales en este bloque: doce DC completos (seis por cada banco exitoso), cinco extracciones fallidas con cinco replays y un diagnóstico. La admisión final usa seis DC del recibo09. No se generó audio.

## Siguiente cierre

Implementar y contrastar Newton del 741 con sus cinco puertos externos y evolución de estado, antes de integrarlo con BJT/JFET en VCO1. Este bloque no resuelve una trayectoria propia, no reproduce todavía el oscilador autónomo y no mide deadlines. La nota larga conjunta sigue rechazada; las escuchas históricas conservan su alcance. Ningún algoritmo nativo anterior cambió.
