# Nota larga: cobertura y diagnóstico

2026-10-06. Ejecución del [protocolo previo](VOZ_REFINAMIENTO_SIGUIENTE_PROTOCOLO.md).
Build08, tres correcciones, modelos y fronteras del banco corto. Cada escena
parte de DC propio: 350 ms, ON 10 ms/OFF 200 ms y transiciones de 10 µs.
Los únicos anclajes del deck son tiempos del teclado, duración y export.
Los bytes eléctricos restantes se verifican por reversión y SHA.

## Cobertura y admisión

| Escena | Filas | Último tiempo aceptado (ms) | Cobertura | Tiempo de proceso (s) |
| --- | ---: | ---: | --- | ---: |
| nominal500 | 649113 | 136.630269425 | parcial, rechazada | 683.31 |
| nominal250 | 1000821 | 150.293268353 | parcial, rechazada | 1021.39 |
| nominal125 | 3703552 | 350.000000000 | completa | 3535.58 |
| nominal-trap125 | 155680 | 15.940420729 | parcial, rechazada | 161.67 |

**Resultado del conjunto: rechazado.** Gear125 completa 350 ms y pasa
los balances: C2 de contorno **0,170264 pC** y C2 del seguidor
**0,003553 pC**, ambos frente a 100 pC. Las otras tres escenas abortan
con mensaje Q7; sus comparaciones dependientes sobre 350 ms no se miden.

La salida Gear125 llega a −0,326880/+0,323302 V; la frecuencia medida
es 439,142277 Hz bajo las fronteras condicionadas. El contorno final
queda en 4,499931 V: la ventana release no demuestra regreso al reposo.

El [banco](../evidence/voice_full_note_runs01.json) conserva errores y
comparaciones no medidas. El exit code cero de ngspice no sustituye el
control del log y de cobertura. Una escena parcial no puede llenar
ventanas de held/release ni un contraste sobre 350 ms. Tampoco se repite
un prefijo para escuchar una nota. No se genera audio nuevo.

La [auditoría](../evidence/voice_full_note_validation01.json) reconstruye
decks históricos, controles, fuentes, runtime, clocks y decisiones sin
nuevos solves. La estimación previa era 4,965 GiB para exports más 2 GiB
de margen, con 10,964 GiB disponibles. Los presupuestos de 7200 s se
fijaron antes de lanzar cuatro procesos independientes; no cambian el
límite Newton. Los tamaños estimados no son cotas.

## Estados aceptados y observación Newton separados

El [diagnóstico](../evidence/voice_full_note_diagnostic01.json) informa
últimos estados aceptados, cruces de reset y extremos en los últimos
100 ns. Sus tres contrastes de prefijo sólo consultan la intersección
real de los exports en rejilla de 5 µs; no retiman ni extrapolan y no
admiten una nota larga aunque el prefijo concuerde.

Trap125 termina a 15,94042072898988 ms, aproximadamente 59,874 ns después
del séptimo cruce ascendente de rampa a −2 V. Teclado está en 10 V y C2
alcanza ~1,136 V. El tiempo redondeado del mensaje Q7 y su paso diminuto
son datos del solver; ese estado exportado no es la iteración rechazada.
Duración y tiempos de teclado cambiaron juntos, por lo que el banco
no atribuye el fallo exclusivamente a extender el horizonte.

La [observación de matrices](VOZ_NOTA_LARGA_MATRIZ_RESULTADOS.md) reproduce
exactamente el rechazo y captura cuatro sistemas. Dos raíces independientes
muestran que tres correcciones dejan ~9,851 µV y fallan el gate lineal.
El [ensayo adicional](VOZ_NOTA_LARGA_SEIS_CORRECCIONES_RESULTADOS.md) contrasta
seis sin cambiar la publicación original: pasa en esas dos matrices con
0,537 nV máximos. Siguiente: [candidato activo separado](VOZ_NOTA_LARGA_SEIS_ACTIVO_PROTOCOLO.md),
sus controles y las cuatro trayectorias; los gates se mantienen.

## Alcance de QA y del sonido

La [QA de publicación](../evidence/voice_full_note_tests01.json) distingue
22 pruebas nuevas de 111 heredadas del recibo anterior mediante SHA
exactos, con sólo README/PLAN/matriz como resúmenes actualizados. La
herencia no cuenta como 111 ejecuciones nuevas. Se conservan los rechazos
de preparación, runner y fixture; ningún gate se flexibiliza al reintentar.

El banco corto de 40 ms conserva su admisión local. La escucha anterior
con senoide impuesta conserva sus bytes y alcance. Alimentación del contorno,
base Q21 y tarjetas siguen condicionadas; falta contorno de filtro y otras
fuentes. Identificación vintage, motor portable y tiempo real permanecen
abiertos. El bloque mide ocho procesos SPICE (cuatro notas y dos parejas
de controles observados), dos builds y cuatro factorizaciones Decimal;
el ensayo adicional reutiliza raíces y no añade factorizaciones.
