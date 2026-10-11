# Base de cargas en las semillas corregidas y liberación inicial

Protocolo previo, 2026-10-11. Model D clásico CA3046, misma escena,
biblioteca y condicionador de 218 filas. Ambas memorias corregidas.

## Dominio

Reproducir por bits las dos raíces y sus 18 corrientes de retención del
acondicionamiento corregido. Diferenciar las 18 tensiones objetivo v,
manteniendo la fase x43=0. Si A=[J,E;Eᵀ,0], resolver
`A·B=[0;I18]`. B tiene 200 respuestas de estado y 18 de corrientes de
retención. Unidades V/V y A/V; para cargas en C, dividir cada columna
por su capacitancia. Rieles fijos cancelan en variaciones de tensión.

Propagar Bx por los dos primeros medios pasos reales del perfil 125 ns
de cada memoria, con calendario fijo. Reproducir cinco estados HIGH/LOW
por paso contra los fixtures anteriores. Adaptador de 18 RHS: misma
eliminación del helper de nueve; comparar sus 28800 coordenadas por bits
con dos lotes de nueve. Un RHS de historia nulo debe producir cero exacto.

Para cada memoria, rama, tamaño 125/62,5 µV y signo, resolver una raíz
propia condicionada y encadenar sus dos pasos. 146 raíces (31828 filas)
y 288 pasos perturbados. No inyectar una carga cambiando sólo un nodo.
Comparar explícitamente la columna C27 con la inyección 139: diferencia
escalada máxima de voltaje debe superar 1e-8 V en ambas memorias.

## Contraste independiente y gates

Incidencia de rango 18, EᵀBx=I dentro de 1e-9 V/V; respuesta de fase
escalada por 125 µV ≤1e-18 V. Newton sin cambios: 64 iteraciones,
24 mitades, residual 1e-13 A/1e-11 V, corrección 2e-9 V/2e-12 A.
Auditar cada raíz con el oráculo heredado de 218 filas, sus mismos gates
de residual/corrección/fase/cargas y la corriente de retención de C1.

Base y FD de raíces: piso 1e-6 V/V / 1e-10 A/V + 3e-4 relativo,
igual que el banco fino original. Oráculo de DC VCO Decimal100/cadena
Python heredada, candidatos nativos; no raíces no lineales independientes.
Propagar la base independiente durante los cuatro pasos con masa antigua
y Jacobianos independientes. Gate de cambio de etapa y de FD temporal:
1e-8 V / 1e-11 A + 1e-4 relativo, escalado por tamaño de perturbación.
Auditar también las 1600 ecuaciones dinámicas de línea base.

Guardar bases completas, raíces propias, sus corrientes y ambos endpoints.
No se cambia objetivo ni tamaño según los errores. Fallos y replay se
conservan antes de reparar, sin relajar gates.

## Recursos y alcance

Sólo compilar caller, stack 32 MiB. Estimación 16 MiB y reserva 1 GiB;
vigilancia 250 ms. Compilación≤120 s, nativo≤600 s, éxito total≤760 s,
administrativo≤1600 s con replay; auditor≤300 s. Evidencia anterior intacta.

Admisión prevista: base condicionada en las semillas corregidas y su
liberación de dos pasos. No conecta esta fase inicial con el intervalo
entre resets previamente medido. Faltan esa propagación completa y sus
eventos propios antes de corregir memoria periódica. Sin audio nuevo,
fidelidad física, calendario adaptativo, mapa de Poincaré ni RT.
