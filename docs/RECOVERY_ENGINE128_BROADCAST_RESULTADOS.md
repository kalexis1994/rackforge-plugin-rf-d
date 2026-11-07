# RF-D con entrada compartida entre pares SIMD

2026-11-07. Se midió RackForge `37e5f803` con un slot Wasm de
laboratorio a 48 kHz. ASIO4ALL confirmó incrementos de 128 muestras
y alternancia de búfer. El mismo banco comparó el SIMD anterior,
la entrada compartida entre pares y esa variante con FIR contiguo.
Todas las variantes mantuvieron los 2048 frames bit a bit, incluida
la latencia de 48 frames. Hubo cero asignaciones en el hilo de
render, avisos de ASIO y fallos de slot.
[Protocolo](RECOVERY_ENGINE128_BROADCAST_PROTOCOLO.md)

## Reservas eléctricas

Los dos SIMD y el escalar produjeron los mismos bits en WASI para
las 18 cargas, memorias de predicción, 12 corrientes de defecto,
68 nodos, puertos y residuos. Se usaron tres puntos nominales y
su estrés de ±0.13 V con las entradas congeladas. Los 48 endpoints
pasaron el balance de transición y la KCL algebraica. El mayor
residuo observado en las trazas fue 1.999 × 10⁻¹³ y la mayor KCL
recalculada en los endpoints fue 6.104 × 10⁻¹⁶ A. La malla de las
12 leyes también pasó en los tres puntos.

Frente a las reservas de 250 ns, el mayor error nodal fue 0.9684 µV
y el mayor error RMS relativo de J7 fue 0.006584 %. En WASI, el FIR
contiguo conservó los voltajes, índices y latencia de 9288 frames
en cuatro escenarios con fragmentación, sin asignar durante el
procesamiento. El FIR mantuvo los 769 taps y el orden de sus sumas.
[Reservas](../evidence/recovery_engine128_reserve01.json),
[equivalencia FIR](../evidence/recovery_engine128_broadcast_fir01.json)

## Cola de latencia a 128 frames

Cada fila corresponde a 4800 callbacks. Tiempos en ms.

| Variante | Pase | Mediana | P99 | Máximo | Sobre 1.333 ms | Sobre 2.667 ms |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| SIMD por pares | Inicial | 1.1252 | 1.4567 | 1.9942 | 79 | 0 |
| SIMD por pares | Replay | 1.1380 | 1.3985 | 2.1224 | 64 | 0 |
| Entrada compartida | Inicial | 1.0940 | 1.3801 | 1.9265 | 56 | 0 |
| Entrada compartida | Replay | 1.0947 | 1.3397 | 1.9085 | 50 | 0 |
| Entrada compartida y FIR contiguo | Inicial | 1.0693 | 1.3915 | 1.8878 | 60 | 0 |
| Entrada compartida y FIR contiguo | Replay | 1.0672 | 1.2546 | 1.8981 | 26 | 0 |

La entrada compartida redujo el P99 y el máximo observado en
ambos pases respecto al SIMD anterior. El FIR contiguo redujo la
mediana en ambos y bajó de nuevo el máximo, con P99 variable
entre sesiones. Los seis pases cumplieron el plazo del controlador.
**El margen de 1.333 ms sigue rechazado** y el VCO y los contornos
quedan fuera del banco.
[Pares](../evidence/recovery_engine128_native07.json),
[entrada compartida](../evidence/recovery_engine128_native08.json),
[FIR contiguo](../evidence/recovery_engine128_native09.json)

El P99 fuera del tramo de render quedó entre 2.7 y 2.9 µs. En los
335 bloques por encima del margen, el hilo acumuló más ciclos que
el P99 de sus pares dentro de margen en el mismo pase. Sólo 18 de
esos bloques cambiaron de CPU entre las dos muestras de CPU. Las
lecturas no separan el coste del solver de la frecuencia o la
contención del procesador.

La comprobación restauró el perfil original de ASIO y retiró el
target temporal, paquetes y cachés. Se conservaron los recibos de
cada pase y el inventario anterior.
[Auditoría](../evidence/recovery_engine128_broadcast_tests01.json)
