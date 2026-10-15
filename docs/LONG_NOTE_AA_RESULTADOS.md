# Nota de 300 ms, antialias y escucha nominal

## Escena y continuidad

[Protocolo](LONG_NOTE_AA_PROTOCOLO.md) y [auditoría](LONG_NOTE_AA_AUDITORIA.md).
Mismo motor CA3046/SVC-204D, un VCO periódico de fase en sierra y DC propio.
KEY ON 1 ms, OFF 200 ms. Se integran 301 ms: cuerpo de escucha [0,300 ms)
y 1 ms de futuro real para el filtro. No se repite un ciclo grabado ni
se reinicia C2/C5, trigger, filtro, VCA o acoplos para prolongar la nota.

Lector [384 kHz](../crates/rf-d-circuit/src/j7_oversampled_readout.rs)
derivado del de 48 kHz cambiando únicamente la tasa y su comentario.
El polinomio y contrato de publicación siguen idénticos. Muestreo racional,
115585 puntos inclusivos, 14401 puntos de salida con un ancla final.
El cuerpo exportable tiene 14400 frames. La salida permanece en voltios.

## Conversión digital y fronteras

[FIR](../crates/rf-d-circuit/src/j7_antialias.rs) posterior a la lectura;
no carga ni realimenta J7. Coeficientes congelados Kaiser/sinc de corte
22 kHz, paso hasta 20 kHz y rechazo exigido de 90 dB desde 24 kHz.
385 coeficientes a 192 kHz y 769 a 384 kHz; mismo semisoporte de 1 ms.
Salida 48 kHz con factores 4/8. Ganancia DC unitaria, sin normalización
de picos o ajuste de la receta. Parámetros del conversor documentados
como decisiones DSP, sin atribuirlos al circuito histórico.

Conversión centrada offline: compensación explícita de 1 ms de retardo
causal. Usa el futuro integrado a la derecha y J7 inicial constante para
tiempo negativo, cero en este DC. No rellena el final con ceros ni duplica
fronteras al concatenar. El filtro puede producir anticipación alrededor
de eventos al compensar el retardo; no modifica el tiempo de KEY eléctrico.

## Diseño contrastado

[Recibo](../evidence/long_note_aa_design01.json): coeficientes comparados
con sinc/I0 en Decimal de 100 dígitos, error máximo 2,297e-16/1,568e-16.
Simetría exacta y error DC <=8,882e-16. Grilla de 524289 frecuencias por
tasa, extremos de bandas explícitos y cota analítica de interpolación
por segunda derivada, con margen declarado de redondeo f64. No se anuncia
como demostración formal mediante intervalos.

Límites conservadores obtenidos: ripple 0,000078696/0,000079143 dB y
rechazo 102,058/102,018 dB, ambos dentro de <=0,001 dB y >=90 dB fijados.
La ventana tiene semisoporte de 1 ms en ambos casos. Fuentes primarias
y ecuaciones se conservan en el protocolo; el runtime no requiere SciPy.


Beta corresponde al diseño Kaiser de 100 dB: 0,1102·(100−8,7)=10,06126,
según [kaiser_beta, implementación SciPy v1.18.0](https://github.com/scipy/scipy/blob/v1.18.0/scipy/signal/_fir_filter_design.py).
El número de coeficientes se fija por un semisoporte entero de 1 ms,
con margen sobre la estimación de longitud; el rechazo se mide y no se
deduce únicamente de la fórmula empírica. La derivación Decimal independiente
comprueba los coeficientes efectivamente publicados.


## Nota y precisión temporal

[Campaña](../evidence/long_note_aa_native01.json): ambos máximos 2/1 us
completan 301 ms. Dos raíces propias DC, prefijo GRID/estado a 75 ms y
cada octava muestra de lectura iguales por bits a las notas admitidas
anteriores, antes de su antiguo KEY OFF. Dieciséis replays exactos del
solver y diez rechazos atómicos en total; once rechazos/retries exactos del
lector entre ambos perfiles. Heap cero en solver, lectura y conversión.

Comparación de salida filtrada de 384 kHz a 48 kHz, ventanas con sus
extremos incluidos para el análisis, sin duplicarlos en el cuerpo de audio:

| Ventana | Diferencia RMS relativa | Máximo/pico |
| --- | ---: | ---: |
| 0–300 ms | 0.0643910 % | 0.1451297 % |
| 1–75 ms | 0.0639364 % | 0.1451297 % |
| 75–200 ms | 0.0653613 % | 0.1576480 % |
| 200–300 ms | 0.0609015 % | 0.1073684 % |

Todas pasan los mismos límites de 0,1 % RMS, 0,3 % máximo/pico y media
1 uV. Error RMS global 1.82312886 uV,
máximo 18.6446957 uV. Antes de KEY se compara
error absoluto: 7.05293815e-14 V. Estos contrastes entre
perfiles no son una cota frente a la solución exacta.

151883/301151 pasos, mínimo full 3,90625 ns. Máximos nativos conjuntos
0,999915 pA/1,998879 nV, error adaptativo <=1. Procesamiento del solver
317,597030/597,544549 s por 301 ms eléctricos, sin incluir todo el costo
de lectura/exports. Es una referencia offline, sin nuevo benchmark RT.

## Tasa y conversión independiente

192/384 kHz proceden de la misma historia: todos los pares de la lectura
384 kHz forman la entrada 192 kHz. Los dos FIR tienen el mismo soporte
temporal y su retardo se compensa con el mismo futuro. RMS relativo global
8,515e-8/8,514e-8 para los dos máximos eléctricos; todas las ventanas pasan
0,01 % RMS, 0,03 % máximo/pico y media 0,1 uV. El máximo absoluto entre
tasas es 4,392 nV. Esta convergencia no demuestra ausencia universal de
alias que pudiera haberse plegado antes de la lectura más alta.

[Auditor del conversor](../evidence/long_note_aa_filter01.json):
convolución NumPy independiente de ambos perfiles y de veinte estímulos;
máximo sobre la nota 3,817e-17 V frente a <=1e-14 V. DC e impulso,
extremos de soporte, cosenos de banda útil/stopband y recuperación ante
capacidad, factor, no finitos o soporte inválidos. Dos tests Rust nuevos
pasan; heap cero en el camino nativo de conversión.

El bypass de 30 kHz expone alias a 18 kHz y falla el rechazo. El estímulo
180 kHz leído a 192 kHz se pliega a 12 kHz antes del FIR y pasa con pico
>0,99; leído a 384 kHz permanece fuera de banda y se rechaza bajo -90 dB.
Estos controles negativos muestran por qué un FIR aprobado no sustituye
la comprobación de tasa ni acredita otros registros/CV.


## Auditoría eléctrica original

[Recibo](../evidence/long_note_aa_audit01.json): **11662 filas**, 238 de
DC y 11424 dinámicas de 48 pares/96 etapas. Incluye el nuevo KEY OFF de
200 ms antes/después, sostenido, final de salida y soporte hasta 301 ms.
Máximos dinámicos 0,450281 pA/0,417714 nV frente a <=20 pA/2 nV. Dos
raíces DC pasan y ambos eventos conservan los estados HIGH/LOW por bits.
Se auditan etapas publicadas con Amount, estrella VCO y cargas originales;
no se presenta una segunda integración original inexistente.

## Escucha única y almacenamiento

[Recibo de escucha](../evidence/long_note_aa_listening01.json) y
[exportador](../tools/export_long_note_aa.py): una vista local regenerable
`artifacts/rf-d-nominal-current.wav`, fuera de Git. WAV IEEE float32 mono,
48 kHz, 14400 frames/300 ms, 57656 bytes. Usa el perfil de referencia de
1 us y la conversión desde 384 kHz. Convención fija **1 V=1 FS**, sin
normalización de pico, fade, clipping o dither. Pico 0.0128469155921 V
(-37.824023 dBFS con esta convención): el nivel de
escucha es bajo porque se conserva la tensión modelada.

Roundtrip float32 máximo 4.63966756e-10 V,
por debajo de 1 nV. Si se retira el WAV, el exportador lo regenera desde
los recibos sin simular otra vez ni sobrescribir el recibo admitido.
No se incorpora el archivo regenerable a los 8769 inputs privados
obligatorios ni se crean carpetas por muestra/variante.

## Admisión y límites

[QA global](../evidence/long_note_aa_tests01.json): 4278 fuentes previas y
8769 entradas privadas protegidas. Se heredan 257 tests anteriores por
identidad y se ejecutan dos nuevos. Dos trayectorias largas, pruebas de
tasa, veinte estímulos del conversor y auditoría original ejecutadas;
las suites históricas completas no se vuelven a correr. Entradas privadas
usadas por el auditor: 0, verificadas por hash
si fueron abiertas. Compiler y rlib congelados verificados de nuevo.

Modelo, solver e inicializador previos conservan bytes. Se admite esta
nota nominal con lectura a 384 kHz, conversión de salida y el máximo full
2 us contrastado con 1 us. Temporales vacíos, recibos <=8 MiB sin QA,
sin Cargo, rlib/cache o carpetas de muestras nuevas. Sigue siendo offline,
un solo VCO de fase nominal y ningún parecido con hardware demostrado.
La respuesta del FIR y el contraste entre dos tasas no acreditan alias
universalmente nulo, otros registros/CV, tres osciladores o deadlines RT.
