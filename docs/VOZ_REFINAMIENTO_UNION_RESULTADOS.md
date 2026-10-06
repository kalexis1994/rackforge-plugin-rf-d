# Voz monolítica con refinamiento del solve

2026-10-06. [Protocolo congelado](VOZ_REFINAMIENTO_UNION_PROTOCOLO.md),
[banco](../evidence/voice_union_refine_runs01.json),
[auditoría sin nuevos solves](../evidence/voice_union_refine_validation01.json)
y [regresiones](../evidence/voice_union_refine_tests01.json).

## Control nominal antes de la unión

El circuito conserva VCO1, cargas de sierra, R6/R45/C27, ladder,
recuperación, ambos VCA y salida. Su contorno de volumen sigue fijo a 2 V
en este control. Se ejecutan los mismos decks históricos con build06
original y build08 desactivado: **218786 filas idénticas**, incluido reloj
y todos los vectores exportados, durante 0–40 ms.

Build08 activo completa 187157 filas y 40 ms. Su control pasa sin
alineación temporal: máximo de voltajes en grilla absoluta de 5 µs
**63.8393 µV**, diferencia DC **2.48734 pV**, diferencia de frecuencia
**9.68562e-8 cent**. Ambas trazas tienen 17 resets; el mayor desfase es
**2.01515 ps**. Los límites previos son 5 mV, 1 µV DC, 1 cent y 10 ns.
La diferencia de cantidad de filas adaptativas no mide costo de audio.

## Identidad eléctrica y procedencia

El runner local fija los binarios y sus módulos/init/DLL por SHA antes
y después. Reutiliza los decks de los bancos históricos y sustituye
exclusivamente `wrdata`; no regenera conexiones, tarjetas, fuentes,
trims, tolerancias o historial. Presupuesto 900 s por proceso, fijado
antes de medir; flags de observación/replay/fila equivalente apagados.
Se archivan comando, log, export, códigos de salida y recibos privados.

Los fuentes Git históricos se comprueban contra sus commits originales.
La única divergencia actual admitida es `loudness_voice_circuit.py`:
su medida de frecuencia pasó de flanco de Schmitt a cruce ascendente
de la rampa a −2 V. El diff histórico sólo cambia esa línea de medición.
Ambos SHA se declaran; el deck eléctrico conserva sus bytes originales.
No se normalizan fuentes históricas ni se omiten sus identidades.

## Alcance de la voz con contorno físico

Se elimina la fuente fija de volumen y se resuelve el contorno/gatillo
con su C2, biestable y seguidor cargado por R59 y la base de Q18.
El VCO produce la sierra que carga el mixer y toda la placa 4. No se
imponen ondas de audio, corriente de cola, fases ADSR, estado del
biestable o voltaje de C2. Teclado ON a 2 ms y OFF a 25 ms, con
transiciones de 10 µs; ataque 10 kohm, decay 100 kohm, sustain inferior
2500 ohm y decay final ON.

Cuatro escenas conjuntas completan **40 ms**, pasan conservación de carga
y sus tres contrastes. La unión queda **admitida numéricamente para este
nominal corto con build08**, sin cambiar tarjetas o tolerancias.

| Escena | Filas | Duración (ms) | Máximo balance C2 contorno (pC) | Máximo balance C2 salida (pC) |
| --- | ---: | ---: | ---: | ---: |
| nominal500 | 191714 | 40 | 0.216153 | 0.000673 |
| nominal250 | 267743 | 40 | 0.199882 | 0.000321 |
| nominal125 | 424429 | 40 | 0.170242 | 0.000413 |
| nominal-trap125 | 393472 | 40 | 0.001842 | 0.001491 |

Límite de ambos balances: 100 pC durante toda la trayectoria.

| Contraste | Máximo entre cinco señales (µV) | Máximo salida (µV) | Máximo RMS por ventana (µV) | Frecuencia (cent) |
| --- | ---: | ---: | ---: | ---: |
| nominal500--nominal250 | 1.545915 | 0.353760 | 0.070061 | 1.21635386e-08 |
| nominal250--nominal125 | 0.387135 | 0.087075 | 0.017292 | 1.9391622e-09 |
| nominal125--nominal-trap125 | 138.454543 | 0.631933 | 0.001838 | 6.28396388e-05 |

Se contrastan C2, contorno, BUS, recuperación y salida en grilla de 5 µs,
con límite 5 mV. RMS pasa 1% +10 µV en cada ventana y frecuencia pasa
1 cent. Gear2→Trap2 tiene su máximo de **138.454543 µV en BUS**; la
recuperación queda en 2.966861 µV. Esto es concordancia finita, sin cota
continua ni identificación física. Los siete solves son tres controles
nominales y cuatro escenas conjuntas; la auditoría reproduce sus medidas
desde exports privados sin resolver otra trayectoria.

El nominal Gear2/500 ns entrega **439.142062 Hz**, contorno desde
−0.290032 V hasta 1.552892 V. RMS AC de salida: **0.138745 µV** en
reposo, **18.1565 mV** en ataque y **53.7825 mV** en la ventana de release.
El contorno medio de esta última ventana es 1.503177 V: el intervalo
25.01–40 ms no acredita release natural terminado. Los valores describen
esta nota corta condicionada y no se ajustan a un objetivo sonoro externo.

Las iteraciones históricas divididas en R45 siguen rechazadas. El nuevo
solve monolítico calcula directamente esa carga; no hereda un cierre de
puerto fallido ni convierte el retorno PWL del VCO mínimo en un contorno.
Se mantienen tarjetas condicionadas, alimentaciones ideales, suministro
de contorno 9.3 V y base Q21 impuesta a 2 V. Contorno de filtro, las otras
fuentes del mixer, identificación de una placa real y tiempo real siguen
abiertos. Ninguna admisión numérica identifica el sonido vintage.

El [siguiente protocolo](VOZ_REFINAMIENTO_SIGUIENTE_PROTOCOLO.md) establece
el próximo corte según estos resultados. Este banco no produce audio
nuevo ni alarga un prefijo por repetición de ciclos. La escucha anterior
con senoide impuesta y sus bytes permanecen conservados.
