# LM741: Newton y puerto dinámico nominal admitidos

2026-10-07. [Protocolo previo](VCO_741_PUERTO_PROTOCOLO.md), [oráculo y exports](../evidence/voice_lm741_port_reference12.json), [producción](../evidence/voice_lm741_port_native05.json) y [QA213](../evidence/voice_lm741_port_tests01.json). No cambia el stamp TI de 37 incógnitas ni ningún algoritmo anterior.

## Nuevo motor

`lm741_port.rs` resuelve el interior con cinco tensiones terminales impuestas. Arranque DC analítico propio, Newton con pivotado escalado, búsqueda por corrección y cinco RHS para entregar gradientes37×5 y corrientes/tangentes5×5. Historia de tres capacitores/dos inductores fija; el estado convergido y las corrientes permanecen candidatos del solve exterior.

El predictor lineal usa L2 y su historia para las estimaciones de modo común; mantiene todas las filas en Newton. El gate final exige residuo y corrección, ambos sin cambios. Entradas no finitas o rieles invertidos en la semilla se rechazan sin panic. No se identifica otro régimen térmico ni un integrado físico.

## Contrastes ejecutados

- Seis DC desde semilla propia, contra todas las incógnitas y corrientes de las raíces ngspice heredadas.
- Nueve trayectorias propias Euler a125/250/500ns, 16µs: diferencial10µV, diferencial5mV y modo común1V. **672 pasos nuevos**, oracle Decimal100 por incidencia y eliminación independientes, desde DC, sin semilla nativa. Se comparan máximos de toda la trayectoria y corrientes externas.
- Nueve exports ngspice completos Gear orden1 y xtrtol=1000000000. Son **371 intervalos dentro del dominio** y **458 fuera**, contados por diferencia temporal real en f64. Los excluidos incluyen arranque/eventos y restas apenas inferiores a125ns; no se clampa ni interpola. Cada solve nativo conserva la historia ngspice anterior. Esto prueba raíces locales de Euler; el control LTE relajado no acredita precisión de trayectoria continua ni refinamiento.
- FD de cinco puertos, 37×5 y5×5, DC y nueve estados dinámicos con historia fija; pureza, retry atómico tras presupuesto insuficiente, memoria y dominio.
- Cuatro tests nuevos de producción (tres funcionales, uno aislado): **1000 solves completos con cinco RHS y cero asignaciones heap**. 213 cubiertos=4 nuevos+209 heredados, sin repetir los heredados. Deadline pendiente.

| Máximo | Trayectorias propias/DC vs oracle | Solves locales ngspice |
|---|---:|---:|
| Voltaje nodal | 5.983473161386144e-10 V | 2.223632389330987e-11 V |
| Corriente ideal | 1.254169318176462e-12 A | 6.891001983443112e-14 A |
| Corriente de puerto | 1.254169318176462e-12 A | 6.890996562432250e-14 A |
| Iteraciones | 7 | 5 |

## Rechazos y límites conservados

reference01 conserva/repite el fallo de extracción XSPICE tras completar136115 filas. Se guarda @Q2[ib] explícitamente en los siguientes para leer la historia de EOS. reference02 terminó sus cuatro escenas pero no logró20 intervalos admisibles en el diferencial grande125ns; su export fallido conservado es del replay, sin hash del original previo. Esta brecha de evidencia se declara en el protocolo; el helper final copia/hashing antes de repetir. El banco admitido12 no tiene replays y conserva sus nueve originales.

reference03/04 y05/06 conservan agotamiento del oráculo en modo común y la repetición con las mismas fuentes; el diagnóstico de04 guarda paso33, entradas/historia e iteraciones. El predictor lineal de L2 resuelve el arranque sin eliminar ninguna ecuación. Los bancos07..12 completos mantienen los mismos vectores por bytes.

native01 conserva/repite fallos de DC con semilla inadecuada. native02 conserva/repite el fallo de FD±1nV: la dirección Newton coincide con Decimal, pero el mérito por máximo de residuo frena el paso por curvatura de los diodos de salida. Se cambia únicamente la búsqueda a corrección normalizada. native03/04/05 pasan; el final añade rechazo previo sin panic para cada pin/rieles invertidos. Los diagnósticos y fuentes anteriores quedan ligados por hash, incluidos errores de path del adaptador de diagnóstico.

En total97 procesos ngspice del bloque, incluyendo dos replays; la admisión final usa nueve escenas de12. No se generó audio ni se repitió la nota larga.

## Próxima integración

Conectar IC1/IC3 con BJT/JFET, sus fuentes comunes, C1/C2 y Schmitt/reset en VCO1. Los puertos aquí están impuestos: todavía no se resuelve un follower con carga libre ni el VCO autónomo completo. Refinamiento, precisión continua, voz final, fidelidad física y RT siguen abiertos. La nota larga conjunta conserva su rechazo.
