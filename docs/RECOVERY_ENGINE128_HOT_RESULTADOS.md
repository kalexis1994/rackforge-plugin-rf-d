# Leyes y solve SIMD en el banco de 128 frames

2026-11-07. El banco mantuvo RackForge `37e5f803`, el FIR contiguo,
la ruta Wasm, la excitación, la política de audio y el driver
ASIO4ALL a 48 kHz. El controlador recibió silencio. Los
2048 frames de salida del núcleo coincidieron bit a bit con
la referencia de cada paquete antes de medirlo.
[Protocolo](RECOVERY_ENGINE128_HOT_PROTOCOLO.md)

## Trabajo del solver

El perfil offline usó la misma secuencia de entrada y recorrió
1024 pasos internos por callback. Contó entre 2057 y 2209
evaluaciones de las leyes por bloque, con hasta tres por paso.
En los dos pases largos previos, la mediana de los bloques
dentro del margen fue 2157 en ambos. En los que se pasaron
fue 2156 y 2172.5. Los dos máximos de pared correspondieron a
2206 y 2201 evaluaciones. La correlación de Pearson entre
evaluaciones y ciclos del hilo fue 0.23 y 0.34. Las cuentas
se solapan y no explican por sí solas la diferencia de tiempos.
El primer compilado de este perfil falló por un comentario interno
en el código concatenado. Se conservó ese fallo y su replay.
[Perfil](../evidence/recovery_engine128_work02.json),
[primer intento](../evidence/recovery_engine128_work01.json)

## Reservas y FIR

El polinomio y `exp_m1` conservaron las ramas y umbrales por
junción. Las variantes mantuvieron los pivotes y el orden de las
operaciones de cada fila. En WASI, el escalar y los candidatos
coincidieron bit a bit en los tres puntos nominales y en el estrés
de ±0.13 V, con 18 cargas, 12 corrientes de defecto, 68 nodos,
memorias, puertos, iteraciones y residuos. La prueba del paso
especializado también comparó sus puertos y estado contra el
inspector después de cada entrada. Los 48 endpoints y la malla de
las leyes conservaron los resultados de las reservas.

El peor error nodal frente a la reserva de 250 ns fue 0.9684 µV
y el peor RMS relativo de J7 fue 0.006584 %. El FIR de cada
variante pasó 9288 frames con los mismos voltajes e índices,
incluidas la fragmentación y la prueba de rechazo atómico.
[Reservas completas](../evidence/recovery_engine128_reserve03.json),
[FIR](../evidence/recovery_engine128_broadcast_fir03.json)

## Confirmación larga

Cada fila corresponde a 4800 callbacks. Los tiempos están en ms.
El criterio exige un máximo de 1.333 ms, el reloj de 128 frames
y dos pases largos válidos.

| Variante | Pase | Mediana | P99 | Máximo | Sobre margen | Plazos perdidos | Reloj 128 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| SIMD y FIR previos | Inicial | 1.0693 | 1.3915 | 1.8878 | 60 | 0 | Sí |
| SIMD y FIR previos | Replay | 1.0672 | 1.2546 | 1.8981 | 26 | 0 | Sí |
| Leyes, eliminación y puertos SIMD | Inicial | 0.8741 | 1.2226 | 1.6435 | 42 | 0 | Sí |
| Leyes, eliminación y puertos SIMD | Replay | 0.8710 | 1.4810 | 1.5627 | 78 | 0 | Sí |
| Paso nominal especializado | Inicial | 0.8624 | 1.3932 | 1.6235 | 53 | 0 | Sí |
| Paso nominal especializado | Replay | 0.8665 | 1.4928 | 1.7280 | 67 | 0 | Sí |
| Solve par por columnas | Inicial | 0.9406 | 1.6519 | 2.5874 | 394 | 0 | Sí |
| Solve par por columnas | Replay | 0.9455 | 1.5539 | 1.7142 | 101 | 0 | Sí |
| Paso nominal con LTO | Inicial | 0.8369 | 1.4142 | 1.7117 | 389 | 0 | Sí |
| Paso nominal con LTO | Replay | 1.2742 | 2.2368 | 23.7374 | 1767 | 35 | No |
| Acumuladores SIMD explícitos | Inicial | 0.8636 | 1.2156 | 1.4393 | 12 | 0 | Sí |
| Acumuladores SIMD explícitos | Replay | 0.8839 | 1.3975 | 1.6994 | 248 | 0 | Sí |
| Acumuladores SIMD explícitos con LTO | Inicial | 0.8662 | 1.3652 | 1.6460 | 115 | 0 | Sí |
| Acumuladores SIMD explícitos con LTO | Replay | 0.8448 | 1.3350 | 1.5061 | 52 | 0 | Sí |

Los acumuladores explícitos dieron el máximo más bajo de un
pase válido, 1.4393 ms. Con LTO, sus dos pases largos cumplieron
el plazo de 2.667 ms, con cero asignaciones y avisos, pero el
margen de 1.333 ms sigue rechazado. El VCO y los contornos
quedan pendientes de superar ese criterio.

El replay con LTO incluyó un salto de 4224 muestras en el reloj
de ASIO. Queda como rechazo y se conserva su traza. El salto
ocurrió en esa sesión y la medición no lo atribuye al compilador.
[SIMD de leyes](../evidence/recovery_engine128_native10.json),
[paso nominal](../evidence/recovery_engine128_native11.json),
[solve por columnas](../evidence/recovery_engine128_native12.json),
[LTO](../evidence/recovery_engine128_native13.json),
[acumuladores](../evidence/recovery_engine128_native14.json),
[acumuladores con LTO](../evidence/recovery_engine128_native15.json)

Se restauró el perfil original de ASIO y se retiraron el target
temporal, los binarios y las cachés. Se conservaron las capturas
y los replays de los rechazos.
[Auditoría](../evidence/recovery_engine128_hot_tests01.json)
