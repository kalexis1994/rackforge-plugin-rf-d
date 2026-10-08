# VCO1: incrementos, precisión recuperada y reset temporal pendiente

2026-10-08. CA3046 nominal a 25 °C, controles y mixer impuestos. Sin hardware físico. Base cad6841. El [protocolo](VCO1_INCREMENTOS_PROTOCOLO.md) fija ecuaciones, aproximación de primer orden en lo y gates. Los módulos anteriores y parámetros físicos permanecen intactos.

## Memoria e incidencias

134 pares hi/lo transportan nodos y ramas; Newton resuelve incrementos respecto del estado aceptado. Capacitores e inductores usan incrementos, y las cargas no lineales conservan su ΔQ estable más la corrección de las partes bajas. La aproximación DC R(hi)+J(hi)lo y las cargas de primer orden son cuasi-Newton: no se presentan como precisión arbitraria o identidad bit a bit con leyes exactas.

La [referencia independiente](../evidence/voice_vco1_increment_reference01.json) usa Decimal100 en terminales, junturas, cargas, incidencias y pivotes. Resuelve las 48 historias condicionales anteriores y los dos intervalos preservados del rechazo: **50 raíces**. Las partes bajas alternadas de las historias condicionales son entradas artificiales declaradas; no describen una trayectoria física independiente.

La [producción](../evidence/voice_vco1_increment_native02.json) contrasta 50 stamps, las 897.800 entradas del Jacobiano incluidas cero, 50 raíces y 110 vectores TwoSum. Error máximo de stamp 5,68435e-14; Jacobiano 5,11591e-13; raíces 7,01014e-12 V / 2,21931e-15 A. 100.000 incrementos menores que un ULP se acumulan; NEG4_REF conserva una parte baja de 1,66080e-16 V y los dos intervalos que antes se atascaban pasan. Heap cero en 16 recuperaciones y 128 pasos.

El [controlador](../evidence/voice_vco1_increment_adaptive_native01.json) conserva 2 µV/2 nA, reloj entero, presupuestos, memoria completa y publicación atómica de ambos medios pasos. Dos tests eléctricos más uno de heap pasan: 128 pares, retries idénticos y recuperación del antiguo piso. Se suman seis tests nuevos a 229 heredados por identidad: **235 controles cubiertos**, sin reejecutar los 229 históricos.

## Recursos de laboratorio

El [primer ensayo nativo](../evidence/voice_vco1_increment_native01.json) desbordó la pila del hilo de test y repitió el fallo sin cambios. El segundo declara 8 MiB de pila de laboratorio en hilo y ejecutable. El ensamblador O2 registra frames directos de 741.160 bytes en solve y 588.040 en linearize; no son una cota de la cadena de llamadas. El recibo/asm privados se protegen por hash. Heap cero **no admite RT**: reducir stack, memoria y medir deadlines sigue pendiente.

El [preflight de ciclos 01](../evidence/voice_vco1_increment_cycles01.json) rechazó recursos antes de lanzar comandos. El [protocolo de almacenamiento serial](VCO1_INCREMENTOS_ALMACENAMIENTO.md) mantiene 2 GiB de reserva y compresión con roundtrip de bytes. No se llegó a archivar una escena exitosa: el primer proceso del intento 02 falló por precisión temporal, no por disco.

## Reset contrastado

La [campaña 02](../evidence/voice_vco1_increment_cycles02.json) parte del arranque propio. Rechaza a **2,434338134765625 ms / 79768392 ticks**, con 15.898 pasos aceptados y 15.899 filas completas de 412 columnas. Original y replay tienen SHA-256 idéntico; conservan tiempo, hi/lo, incremento, corrientes, gates y dt real. La campaña se detiene en su primera escena C4=10 pF/máximo 500 ns; las otras cinco no se ejecutan. No hay frecuencia ni refinamiento estacionario admitidos.

El [diagnóstico](../evidence/voice_vco1_increment_floor01.json), bajo [protocolo propio](VCO1_INCREMENTOS_RESET_PROTOCOLO.md), resuelve desde la memoria preservada el paso de 2 ticks y dos pasos de 1 tick. Las tres raíces nativas cumplen residual/corrección y coinciden con Decimal100 hasta **2,05832e-13 V / 9,76994e-17 A**. El solver independiente parte de la historia, no del candidato nativo.

La incógnita limitante es **SCHMITT_Q6_COLLECTOR, índice 50**. Full menos endpoint independiente = −2,013102314101013 µV; ratio 1,006551157 frente al gate 1. El endpoint cambia −1,468627771239932 mV respecto de la historia. La precisión del estado está recuperada en este intervalo, pero el piso temporal de 30,517578125 ps no satisface LTE. El rechazo conserva su significado; no se amplía el gate por 0,65 %.

## Trabajo siguiente y límites

Derivar una grilla temporal más fina con memoria compensada, contrastar el intervalo limitante y sólo después retomar el banco completo con gates originales. Mantener C4 separados y R6/R45 con propietario único antes del mixer. Calibración transitoria, ciclos estacionarios, carga activa, voz, audio nuevo, física y RT no están admitidos. Cero procesos SPICE nuevos. Los rechazos previos quedan protegidos junto con las versiones exactas de fuentes medidas.

La [QA de publicación](../evidence/voice_vco1_increment_tests01.json) valida este alcance y la conservación de evidencia.
