# Combustible y coste de RF-D a 128 frames efectivos

2026-11-07. La corrección del runtime de RackForge está en
`37e5f803`, sobre el host del banco original `7a14c68a`.
`PortableInstance` evita llamar a `get_fuel` si el store usa
interrupción por época. Las cuatro rutas siguen registrando consumo
cuando el medidor está activo, incluso al devolver un trap.
Se recompilaron las dos revisiones en Release con Rust 1.98.0 MSVC.
[Protocolo](RECOVERY_ENGINE128_FUEL_PROTOCOLO.md)

El control silencioso del host corregido y todas las series con
DSP registraron cero asignaciones Rust en el hilo de render,
desde la primera llamada. La captura de 2048 frames de cada variante
coincidió bit a bit con la referencia, incluidos los 48 frames de
latencia del FIR. ASIO4ALL reportó incrementos de 128 muestras a
48 kHz con alternancia de búfer. Se usó el motor RackForge con un
slot desde el adaptador de laboratorio.
[Campaña con el host corregido](../evidence/recovery_engine128_native03.json)

## Confirmación larga

Cada fila corresponde a 4800 callbacks. Los tiempos están en ms.
El plazo es 2.667 ms y el objetivo es 1.333 ms por callback.

| Variante | Pase | Mediana | P99 | Máximo | Fuera de plazo | Sobre margen | Asignaciones |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Host de control, invitado O2 | Inicial | 1.5002 | 1.7616 | 2.6856 | 1 | 4800 | 4800 |
| Host de control, invitado O2 | Replay | 1.5300 | 1.7181 | 2.6276 | 0 | 4800 | 4800 |
| Host corregido, invitado O2 | Inicial | 1.5533 | 2.6764 | 4.5901 | 53 | 4800 | 0 |
| Host corregido, invitado O2 | Replay | 1.5230 | 2.5800 | 4.6581 | 18 | 4800 | 0 |
| Host corregido, invitado O3 | Inicial | 1.6912 | 2.1704 | 2.6205 | 0 | 4800 | 0 |
| Host corregido, invitado O3 | Replay | 1.5949 | 2.5533 | 3.9745 | 17 | 4800 | 0 |
| Host corregido, O3 con SIMD | Inicial | 1.1236 | 1.3245 | 2.1470 | 0 | 47 | 0 |
| Host corregido, O3 con SIMD | Replay | 1.1546 | 1.6734 | 3.2889 | 1 | 125 | 0 |

El host de control recompilado volvió a asignar una vez por bloque
Wasm, incluso con el invitado silencioso. Los invitados O2 fueron
idénticos por hash entre los dos hosts. La corrección eliminó la
asignación de forma reproducible. Los máximos y las pérdidas de
plazo variaron entre sesiones y la corrección por sí sola dejó
todos los bloques largos por encima del objetivo.
[Control recompilado](../evidence/recovery_engine128_native06.json)

SIMD por pares de filas dio medianas entre 24 % y 28 % menores que
las del host corregido con el invitado O2 en los pases equivalentes.
Cada fila conserva el orden de sus productos y sumas. La variante
mantiene las cargas, las leyes de los dispositivos, el solver de
Newton y el FIR. El banco acredita la igualdad de salida del caso
nominal. Los estados y puertos de las reservas eléctricas siguen
siendo parte del criterio de promoción.
[O3](../evidence/recovery_engine128_native04.json),
[SIMD](../evidence/recovery_engine128_native05.json)

La variante SIMD todavía falla el margen de 1.333 ms y su repetición
perdió un plazo. El VCO y los contornos quedan fuera de esta versión.

## Validación y limpieza

La compilación inicial tomó el toolchain GNU por defecto y falló
por falta de `dlltool.exe`, también en el replay sin cambios.
La campaña usó explícitamente MSVC. Los recibos identifican la
recompilación y las pruebas del runtime. Se restauró el perfil
original de ASIO y se retiró el target temporal de Cargo junto con
los paquetes y cachés de las mediciones.
[Compilación y pruebas](../evidence/recovery_engine128_fuel_build01.json),
[auditoría](../evidence/recovery_engine128_fuel_tests01.json)
