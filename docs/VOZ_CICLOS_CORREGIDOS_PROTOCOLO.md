# Ciclos propios de las memorias corregidas

2026-10-09. Model D clásico CA3046, misma escena nominal SVC-9 p.5
y p.19/13/10 del [banco anterior](VOZ_CICLOS_SEMILLAS_PROTOCOLO.md).
Las dos memorias proceden del [cierre conjunto](VOZ_CARGAS_CORREGIDAS_PROTOCOLO.md).
Física, biblioteca, controles, solver y gates permanecen congelados.

## Experimento

Restaurar las dos raíces id/guess=0 por sus 400 floats exactos, reloj
cero, propuesta 2·máxima media etapa, 20 intentos, reservado=0.
Caller Rust idéntico por bytes al banco de semillas. Solo cambia la
procedencia de los checkpoints del llamador y el destino de los outputs.
Cuatro perfiles seriales: dos memorias ×125/62,5 ns hasta 5,25 ms,
2.752.512.000 ticks. Frontera de 2 µs para reproducir por bytes las
liberaciones corregidas admitidas; 21 anclas de 250 µs y restores
exactos a 250 µs/2,25 ms. Scene construye parámetros, no la memoria.

## Gates y comparación

Heredar sin cambios los gates y codecs del protocolo anterior:
Newton 1e-13 A/1e-11 V y 2e-9 V/2e-12 A; LTE 2 µV/2 nA;
BUS/C1 KCL≤1e-12 A, balance C1 relativo≤0,002.
200 coordenadas a 22 relojes no iniciales; refinamiento ≤1 cent de
frecuencia y ≤5 mV de extremos. 19200 ecuaciones seleccionadas,
96 puntos de etapa, 96 corrientes de terminales y 16 LTE nuevos.
Dos resets por perfil delimitan un periodo observado.

Ledger Radau saw/BUS/entrada 6/corriente de panel/desbalance; cerrar
C27 con endpoints reales, error≤1e-12 A por duración, identidades
medias≤1e-9 V. Reportar 18 cargas y 200 diferencias por fase con
interpolación Decimal100. El ledger no es otra integración independiente.

Comparar cada memoria corregida con su historia anterior a igual
resolución y misma definición de fase. Reportar mejoras y empeoramientos
de las 18 cargas y J7, con valores y unidades; no dividir entre cero.
Contrastar la deriva observada con la predicción estática, conservando
su alcance. Comparar medias de cada historia con sus propias integrales.
Ni la mejora ni el gate temporal acreditan asentamiento; quedan pendientes
periodos consecutivos y fuentes/controles fuera de esta escena.

## Recursos y admisión

Preservar toda la evidencia anterior y documentos mutables por bytes.
Compilar solo caller, stack 32 MiB; compilación≤120 s,
32000/48000 intervalos, 1800 s por perfil y 7200 s globales.
Reserva 1 GiB más 64 MiB estimados, disco cada 250 ms, stop cooperativo
y gracia de 20 s. Conservar fallos/checkpoints/replay antes de reparar.
Sin nuevos tests Rust, audio, SPICE, cambio de circuitos, encendido físico,
periodicidad, fidelidad vintage o RT admitidos por este banco.
