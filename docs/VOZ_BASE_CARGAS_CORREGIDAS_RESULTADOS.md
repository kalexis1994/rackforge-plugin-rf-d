# Base condicionada de las semillas corregidas y liberación inicial

2026-10-11. Model D clásico CA3046.
[Protocolo previo](VOZ_BASE_CARGAS_CORREGIDAS_PROTOCOLO.md),
[inputs](../evidence/voice_charge_basis_inputs01.json),
[nativo](../evidence/voice_charge_basis_native01.json),
[contraste independiente](../evidence/voice_charge_basis_reference01.json)
y [QA](../evidence/voice_charge_basis_tests01.json).

## Función y dominio

El [condicionador de 218 filas](VOZ_CARGAS_SEMILLA_PROTOCOLO.md) y las
[dos semillas corregidas](VOZ_CARGAS_CORREGIDAS_PROTOCOLO.md) permanecen
intactos. Se reproducen por bits ambos estados HIGH/LOW y sus 18 corrientes
de retención. Ahora se diferencia la raíz en esas semillas corregidas,
manteniendo la fase x43=0 y variando las 18 tensiones objetivo v.

Resolver `[J,E;Eᵀ,0]·B=[0;I18]`. Bx son 200 respuestas de estado;
Bi son 18 respuestas de corrientes de retención. Cada columna se expresa
en V/V o A/V según la fila. E tiene rango 18 y EᵀBx=I dentro de 1e−9.
La respuesta de fase escalada por 125 µV es≤1e−18 V. Para expresar
respuestas respecto de carga en coulombs, dividir la columna por su C.
Con riel fijo, ΔQ=C·Δv; el voltaje objetivo de condicionamiento es una
coordenada de incidencia, no necesariamente la tensión física absoluta
contra el riel. [Distinción de rieles](VOZ_CARGAS_RIELES_NOTA.md).

Esta base de 36 columnas/7848 entradas conserva la restauración algebraica.
No se obtiene inyectando sólo una tensión en un nodo del estado.

## Contraste y liberación

146 raíces nuevas (31828 ecuaciones): dos bases y 144 raíces propias para
18 ramas, dos tamaños 125/62,5 µV y dos signos en ambas memorias. El oráculo
heredado audita todas las filas, fase/cargas y corriente retenida de C1.
DC VCO Decimal100 y cadena Python; evalúa candidatos nativos, sin buscar
raíces no lineales independientes. Los gates Newton no cambian.

Se propaga Bx por los primeros dos medios pasos del calendario original
125 ns de cada memoria. Duraciones reales: memoria 0 1.5625e-08 s,
memoria 1 1.5625e-08 s. Cuatro pasos reproducen por bits los cinco
estados HIGH/LOW de sus fixtures. 288 pasos perturbados nuevos encadenan
las raíces propias hasta sus dos endpoints.

El oráculo propaga su propia base inicial mediante masa antigua y
Jacobianos independientes en los cuatro pasos: 72 direcciones/28800
coordenadas de etapas y 1600 ecuaciones dinámicas. El adaptador nativo
de 18 RHS sólo cambia el ancho: 28800 coordenadas coinciden por bits
con dos lotes de nueve del helper anterior. Cuatro controles de historia
nula dan respuesta cero exacta. Se conservan las bases, las raíces propias
completas con corrientes y ambos endpoints para reconstruir FD.

| Contraste | Peor ratio frente a gate 1 |
|---|---:|
| Base condicionada, oráculo | 4.55280363e-05 |
| Base condicionada, FD | 0.109311981 |
| Etapas, propagación independiente | 0.00258448578 |
| Endpoints, raíces e historias propias | 0.0707469689 |

Gates de base/FD de raíces heredados: 1e−6 V/V / 1e−10 A/V + 3e−4 relativo.
Gates de cambio de etapas/FD temporal: 1e−8 V / 1e−11 A + 1e−4 relativo,
escalados por el tamaño. Los tamaños están fijados antes de medir.

## Control de inyección de C27

Se compara la columna 5 condicionada con la dirección unitaria 139 usada
en el intervalo anterior. Ambas cambian inicialmente la coordenada de C27,
pero la raíz condicionada permite que se muevan los nodos necesarios para
cerrar el sistema. La diferencia máxima de voltaje escalada por 125 µV
supera el gate 1e−8 V en ambas memorias:

| Memoria | Diferencia de estado V | Respuesta BUS V/V | Respuesta J7 V/V | Error EᵀBx−I |
|---|---:|---:|---:|---:|
| 0 | 0.000123539621 | -0.98831697 | 1.04213604e-10 | 5.55111512e-17 |
| 1 | 0.000123539621 | -0.988316968 | 1.05744485e-10 | 5.55111512e-17 |

El [intervalo completo anterior](VOZ_INTERVALO_RETORNO_RESULTADOS.md)
parte de otro estado, previo al primer bracket, y mantiene BUS/rampa
iniciales fijos. Sus sensibilidades no se pueden identificar con esta
columna condicionada ni reutilizar directamente como mapa de cargas.

## Alcance y siguiente bloque

Admitido: base de las semillas corregidas y liberación inicial de dos
pasos. Biblioteca y leyes intactas, 248 tests Rust heredados por identidad.
Falta propagar desde estas raíces hasta ambos resets y observar sus eventos
propios para obtener la dependencia de la deriva respecto del dominio de
cargas. Todavía no se admite retorno completo desde la raíz condicionada,
memoria periódica asentada, mapa de Poincaré, adaptación, fidelidad ni RT.
Sin nuevo audio o SPICE.

Nativo 4.812100 s; oráculo 52.616283 s. Salidas nativas
3331548 bytes. Reserva 1 GiB, estimación 16 MiB, stack 32 MiB,
vigilancia 250 ms; compilación≤120 s, ejecución≤600 s, éxito≤760 s,
auditor≤300 s. Sin borrar evidencia anterior.
