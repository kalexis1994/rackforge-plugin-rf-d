# Derivada del reset observado y proyección de fase

2026-10-10. Model D clásico CA3046. [Protocolo previo](VOZ_EVENTO_HISTORIA_PROTOCOLO.md),
[inputs](../evidence/voice_history_event_inputs01.json),
[campaña nativa](../evidence/voice_history_event_native01.json),
[contraste independiente](../evidence/voice_history_event_reference01.json)
y [QA](../evidence/voice_history_event_tests01.json).

## Observador implementado

Ocho brackets de rampa 43 cruzando -2 V en sentido creciente, primer y
segundo reset de cuatro historias. Se usan los dos primeros pasos de las
ventanas anteriores. Los 16 pasos reproducen por bits cinco estados HIGH/LOW
e incrementos; 57600 coordenadas de sensibilidad también coinciden con
el output admitido. Biblioteca, leyes y Newton no cambian ni se recompilan.

Se deriva el interpolante lineal que ya define la observación histórica:
`alpha=(-2-a)/(b-a)`, `dalpha=-[(1-alpha)Sa[43]+alpha Sb[43]]/(b-a)`.
El cambio del tiempo relativo al inicio del bracket es `dt=h*dalpha`.
La respuesta del estado en fase incluye
`dZ=(1-alpha)Sa+alpha Sb+(B-A)*dalpha`.
Los tiempos absolutos de milisegundos se conservan como ticks; sus pequeños
cambios se calculan relativos al bracket para evitar cancelación.

El detector conserva HIGH+LOW redondeado a binary64. El interpolador del
estado conserva diferencias compensadas. Se evalúan derivadas a primer orden;
no se afirma una derivada de cada redondeo del codec ni del evento continuo.

## Contraste y resultados

72 direcciones de evento/14400 coordenadas de estado proyectado. 576 pasos
perturbados nuevos, 288 observaciones de evento propias: nueve direcciones,
dos tamaños y dos signos, con dos pasos encadenados por historia. Los
endpoints de cada historia y su estado interpolado completo se guardan;
el auditor reconstruye la diferencia central. Todos mantienen el mismo
bracket transversal y la rampa interpolada a -2 V dentro de 1e-13 V.

El oráculo propaga su propia sensibilidad en los 16 pasos con masa antigua
y Jacobianos independientes (VCO Decimal100, gradiente de cadena heredado),
y deriva observador/proyección en Decimal100. Evalúa candidatos nativos;
no busca raíces no lineales independientes.

| Contraste | Peor ratio frente a gate 1 |
|---|---:|
| Estado en fase, oráculo | 8.59426157e-06 |
| Tiempo de cruce, oráculo | 1.11698326e-11 |
| Estado en fase, historias propias | 6.47372499e-06 |
| Tiempo de cruce, historias propias | 5.42005404e-07 |

Gate de cambio del estado: 1e-8 V / 1e-11 A + 1e-4 relativo.
Gate de cambio de tiempo: 1e-17 s + 1e-4 relativo. Epsilon por dirección
se reutiliza de su ventana anterior, con dos tamaños centrales; no se
elige a partir de estos resultados. El denominador/alpha y las unidades
de entrada y salida quedan explícitos en protocolo y codec RFJHEVT1.

Ocho controles algebraicos 98 dan tiempo y respuesta exactamente cero.
La respuesta escalada de la rampa proyectada es≤1e-18 V. El control
positivo 43 detecta que omitir el cambio de tiempo deja una respuesta
de rampa mayor que el gate de estado en cada bracket:

| Perfil | Reset | Alpha | Cambio de rampa sin término temporal V |
|---|---|---:|---:|
| 0 | reset1 | 0.254677275 | 4.51952348e-06 |
| 0 | reset2 | 0.17185063 | 4.5155845e-06 |
| 1 | reset1 | 0.267473751 | 4.52013504e-06 |
| 1 | reset2 | 0.208344515 | 4.51731587e-06 |
| 2 | reset1 | 0.251704284 | 4.51937802e-06 |
| 2 | reset2 | 0.165945726 | 4.51530153e-06 |
| 3 | reset1 | 0.264500765 | 4.51998939e-06 |
| 3 | reset2 | 0.202439568 | 4.51703183e-06 |

## Alcance y siguiente bloque

Admitido: este observador interpolado y su proyección de fase local, respecto
de la historia inmediatamente anterior al bracket, con calendario fijo.
No es un mapa de retorno de periodo completo, una saltación de un sistema
híbrido ni una derivada del calendario adaptativo. La corrección de memoria
periódica necesita todavía propagación entre retornos y su dominio de
cargas iniciales. Sin nueva memoria asentada, audio, SPICE, cambio de
componentes, fidelidad física o tiempo real. 248 tests Rust heredados
por identidad, sin reejecutarlos.

## Recursos y limpieza

Nativo 15.865325 s, oráculo 11.171185 s; compilación≤120 s,
ejecución/verificador≤300 s, total nativo≤480 s; pila 32 MiB. Este banco
compacto fijó 16 MiB estimados y reserva 512 MiB antes de medir. Los
recibos anteriores de 1 GiB y sus artefactos permanecen intactos.

A petición del usuario se limpiaron 5346 archivos regenerables
en `rackforge/target/release/deps`: 6942289384 bytes
lógicos de rlib/rmeta/pdb/o/d. [Recibo de limpieza](../evidence/storage_cleanup01.json).
166 ejecutables/DLL de esa carpeta conservan su hash;
Git del host conserva su estado. No se borra evidencia ni paquetes.
El disco informó 15984484352 bytes libres al terminar la limpieza.
La próxima compilación del host regenerará esos intermedios. El espacio
libre global es una observación; el recibo distingue bytes eliminados.
