# Intervalo completo entre resets: respuesta observada de C27

2026-10-11. Model D clásico CA3046. [Protocolo previo](VOZ_INTERVALO_RETORNO_PROTOCOLO.md),
[inputs](../evidence/voice_return_interval_inputs01.json),
[campaña nativa](../evidence/voice_return_interval_native01.json),
[contraste independiente](../evidence/voice_return_interval_reference01.json)
y [QA](../evidence/voice_return_interval_tests01.json).

## Recorrido y dominio

Perfil memoria 0 / límite 125 ns, desde el estado real inmediatamente anterior
al primer bracket hasta el final del segundo. 22356 medios pasos reproducen
por bits las siete observaciones del calendario anterior; los cuatro pasos
de ambos brackets reproducen los cinco estados HIGH/LOW e incrementos.
Se reutiliza la biblioteca congelada sin recompilarla ni modificar leyes.

Las nueve direcciones 43,5,12,139,199,194,157,117,98 se propagan durante
todo el intervalo. Sólo 139 tiene contraste no lineal de recorrido completo:
cuatro historias propias de 22356 pasos, ±epsilon y ±epsilon/2, total 89424
solves perturbados. La perturbación cambia inicialmente V139, entrada 6 de
cadena, y V(C27)=V139−V12, con BUS y rampa fijos. No se deriva una raíz de
18 cargas condicionadas. El origen es el estado real previo al bracket;
no se convierte el primer interpolante en condición inicial.

Se observan Z1/Z2 con el interpolante de reset ya admitido y se comparan
T=t2−t1 y D=Z2−Z1. La respuesta de T es dt2−dt1; la de D, dZ2−dZ1,
incluyendo la proyección de fase en cada evento. El tramo común de ticks
se cancela antes de medir cambios de periodo, sin restar relojes grandes.
Todos los brackets propios conservan cruce transversal creciente de −2 V.

## Resultados y contraste

Periodo observado **0.00243426399764 s**. Epsilon inicial de 139:
**5.39926548977e-06 V**; elegido con la ganancia máxima nativa de todas
las etapas antes de las historias perturbadas, no a partir de sus errores.
Respuesta del periodo **-4.20221880967e-09 s/V**.
Deriva observada de J7 **-0.000224263234611 V**;
su respuesta a V139 inicial **0.000572320298198 V/V**.

| Contraste | Peor ratio frente a gate 1 |
|---|---:|
| Operadores seleccionados | 0.0036906916 |
| Primer evento, historias completas | 1.40374909e-06 |
| Segundo evento, historias completas | 1.68003509e-06 |
| Periodo observado, historias completas | 0.00348514479 |
| Deriva del estado, historias completas | 2.19800385e-06 |
| Deriva de tensiones de capacitores, historias completas | 3.24597491e-09 |

Los gates de cambios son 1e−8 V / 1e−11 A + 1e−4 relativo para
estado/deriva; 1e−17 s + 1e−4 relativo para periodo, y 2e−8 V + 1e−4
relativo para tensiones de ramas. El observador Decimal100 reconstruye
alpha dentro de 2e−15 y los estados dentro de 1e−13 V / 1e−16 A;
la rampa en sección queda a −2 V dentro de 1e−13 V. La respuesta escalada
de la rampa proyectada es≤1e−18 V. El control algebraico 98 permanece
cero exacto en las etapas de los 22356 pasos y ambas proyecciones.

El oráculo reconstruye masa/Jacobiano en **15 puntos preseleccionados** y
aplica el operador independiente a la **sensibilidad entrante nativa**.
135 direcciones/54000 coordenadas de etapa; 6000 ecuaciones no lineales
de candidatos cumplen gates heredados de residual/corrección. También
reconstruye ambas proyecciones y sus diferencias. Esto contrasta operadores
seleccionados, no propaga una sensibilidad independiente en los 22356 pasos.
El contraste completo de 139 proviene de sus cuatro historias no lineales.
La ganancia máxima de todas las etapas es una reducción nativa: el auditor
comprueba epsilon y las cotas de los 15 puntos, no recalcula todo ese máximo.

## Las 18 tensiones de memoria de cadena

Deriva de tensión entre Z2/Z1 y su respuesta a la perturbación de V139.
Se incluyen todas las ramas: C27 es índice 5, C10 es índice 17. BUS es
nodo 66; PLUS y tierra son referencias fijas y cancelan en las diferencias.
El contraste de diferencias centrales incluye las 18 ramas con ambos tamaños.
Estos valores describen este intervalo; no acreditan memoria periódica asentada.

| Índice | Nodos de cadena | Capacidad F | Deriva V | Respuesta V/V |
|---|---|---:|---:|---:|
| 0 | 8 / 12 | 6.8e-08 | 0.000422605576 | -0.0100966303 |
| 1 | 9 / 13 | 6.8e-08 | 0.000975599923 | -0.00770717752 |
| 2 | 10 / 14 | 6.8e-08 | 0.000886711085 | -0.00470786408 |
| 3 | 11 / 15 | 6.8e-08 | 0.000237921356 | -0.00212727287 |
| 4 | 4 / None | 0.00022 | 1.67740576e-06 | 0.000267289465 |
| 5 | 6 / BUS | 1e-05 | 2.13791727e-06 | -0.00603368094 |
| 6 | 16 / 11 | 2.2e-07 | 0.000118709451 | 9.11514549e-05 |
| 7 | 17 / 15 | 2.2e-07 | -0.00012136508 | -0.000106314368 |
| 8 | 23 / None | 0.0001 | 0.000673634167 | 0.000665991088 |
| 9 | 24 / 25 | 3.3e-07 | 0.00385971569 | 0.00316843794 |
| 10 | 26 / None | 0.00022 | 5.69874071e-06 | 4.70281926e-06 |
| 11 | 40 / PLUS | 0.00022 | 6.6795025e-08 | 2.77323303e-08 |
| 12 | 46 / 47 | 1e-05 | 0.00092236614 | 0.000764921804 |
| 13 | 49 / 50 | 2.5e-06 | 0.000503801876 | 0.00043481837 |
| 14 | 57 / 58 | 2.2e-10 | -0.00277608971 | 0.00735452262 |
| 15 | 60 / 61 | 0.0004 | 7.62194163e-05 | 6.64155207e-05 |
| 16 | 62 / None | 1e-10 | 0 | 1.65060406e-30 |
| 17 | 67 / 7 | 1e-05 | 6.52825781e-05 | 5.0541586e-05 |

## Alcance, recursos y siguiente bloque

Admitido: respuesta observada de periodo y deriva a V139 inicial para este
intervalo y calendario. Las otras ocho columnas conservan alcance de
recurrencia nativa y operadores seleccionados. No es mapa de Poincaré,
respuesta de la raíz condicionada de cargas, evento continuo ni derivada
adaptativa. Faltan el dominio de cargas iniciales y contraste entre perfiles
para una corrección de memoria periódica. Sin nuevo audio, SPICE, fidelidad
física o tiempo real; 248 tests Rust heredados por identidad, no reejecutados.

Nativo **1620.689990 s**, auditor **12.047236 s**. Salidas
nativas **4025086 bytes**: siete observaciones por paso, 15 puntos
y brackets/eventos propios completos. Sin matrices guardadas en cada paso.
Reserva 1 GiB, estimación 64 MiB, pila 32 MiB, vigilancia 250 ms;
compilación≤120 s, ejecución≤2300 s y total exitoso≤2400 s; auditor≤300 s.
La evidencia anterior se conserva íntegra.
