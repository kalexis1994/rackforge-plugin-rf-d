# Crecimiento BDF2 desde DC: E4G8

## Protocolo declarado antes de medir

Las [ventanas con memoria E4](BIESTABLE_VENTANAS_DE_CRECIMIENTO.md) motivan
un contraste completo desde DC. Se integra una ruta nueva **E4G8** hasta
3 ms. Sólo cambia el umbral de error para duplicar la propuesta: **0,125**
frente al 0,25 de E4. Es una sensibilidad al controlador con tolerancias
fijas, no una tercera política de refinamiento.

Se conservan circuito sintético `finite_transit`, 94 nodos, R61=200 Ω,
BUS=0 V y KEY 0→10 V en t=0. Se usa exactamente la política E4: error
absoluto nodal/juntura 10 nV, relativo 10⁻⁸, incremento de juntura 12,5 mV,
producto modal 0,025, paso máximo 100 µs, mínimo de intervalo real 1 ps y
presupuesto de 12000 intentos. El macro con dos medios requiere ≥2 ps;
la razón de BDF2 y cada crecimiento siguen limitados a 2.

El arranque conserva BE completo frente a BE medio+BDF2 medio solamente
mientras falta el historial previo; publica los dos estados finos. Después
se publica BDF2 completo y se guardan dos medios BDF2 provisionales al mismo
destino binario. No se divide Richardson ni se reinicia memoria tras rechazo.
Los otros dos criterios para crecer siguen en la mitad de sus gates.

Cada publicación y medio guardado debe satisfacer carga sobre historial real,
KCL <10 pA, error de rama <10 fV y restauración exacta. Las fuentes y los
informes anteriores se fijan por SHA antes/después y permanecen intactos.
Se preservan todos los rechazos y cualquier cobertura incompleta.

`python tools/loudness_latch_bdf_growth_dc.py`

## Observación declarada

Se contrasta E4G8 con **E4** y, separadamente, con **D4**. Ambos contrastes
mantienen el reloj original, excluyen puentes del salto de fuente inicial y
conservan el gate de 1 mV. La comparación interpolada es un diagnóstico.
La segunda etapa consulta cada máximo interpolado por nodo (94), la rejilla
fija heredada de 25 µs y 0,5 µs entre 2,4–2,5 ms, 32 medios estratificados
por ruta y el máximo interpolado global. Se deduplican tiempos exactamente.

Se usa el observador conservativo existente, con anclaje anterior y dos
pasos provisionales cuando el resto solicitado sería menor que 1 ps.
Se repite FD en el pico interpolado y en el pico de la selección consultada;
se distinguen registros repetidos de casos distintos. Las consultas no
modifican la trayectoria publicada ni acotan su máximo continuo.

`python tools/loudness_latch_bdf_growth_dc_sampling.py`

## Costo y alcance

Se separan intentos, rechazos, intervalos publicados y medios provisionales.
Se registra tiempo de integración Python fuera de audio, en una ejecución;
no se compara como benchmark con tiempos antiguos ni como deadline.
Incluso si estos contrastes pasan, no hay solución exacta independiente,
refinamiento a tolerancia más estricta, identificación física o audio admitido.
El gate fallido D4/E4 de 7,81 mV permanece en su informe original.

## Resultado del barrido completo

E4G8 completa exactamente 3 ms desde el mismo DC y arranque E4.

| Ruta | Ensayos aceptados | Intervalos publicados | Medios provisionales aceptados | Rechazos | Intentos totales |
| --- | --- | --- | --- | --- | --- |
| E4, crecimiento 0,25 | 5921 | 5922 | 11840 | 669 | 6590 |
| E4G8, crecimiento 0,125 | 6485 | 6486 | 12968 | 49 | 6534 |

Se evitan 620 rechazos y se añaden 564 ensayos aceptados: sólo **56 intentos
menos** (≈0,85%). Todos los rechazos nuevos son por error de voltaje o
incremento de juntura; no hay fallo de solve, mínimo o presupuesto.
La integración Python tomó 2731,848 s en una ejecución, excluyendo
almacenamiento, comparaciones y observación. No es un benchmark comparado
con E4 ni mide un deadline de audio.

En los aceptados normales, el código v4 evalúa tres tasas modales nuevas
por ensayo; la tasa entrante se reutiliza. Son **17760** evaluaciones en
E4 frente a **19452** en E4G8, derivadas del flujo y de los registros.
Se cuentan aparte del arranque común y de la tasa DC inicial. Los rechazos
por error vuelven antes de esas evaluaciones. Intentos distintos no tienen
costo uniforme: reducir su total no prueba una optimización de CPU.

El mínimo publicado es 190,734863 ps y el mínimo provisional 95,367431 ps.
Máximo KCL publicado 9,955757 pA; en medios aceptados 9,944990 pA. Ambos
conservan el límite original de 10 pA, sin cambiar tolerancias o memoria.
El gzip canónico tiene 74697768 bytes, con restauración sin pérdida.

| Contraste interpolado | Máximo | Nodo / tiempo | Diferencia final |
| --- | --- | --- | --- |
| D4/E4G8 | 8,234030 mV | ATTACK_GATE_LOWER / 2,442470360 ms | 16,016031 µV |
| E4/E4G8 | 1,001861 mV | ATTACK_OUT / 2,422424316 ms | 1,477786 µV |

Ambos diagnósticos interpolados fallan 1 mV. El máximo frente a D4 es
mayor que los 7,808516 mV originales D4/E4. Se retiene la observación
conservativa como etapa propia; no se elige un controlador sólo por
rechazos ni se modifica el gate global anterior.

## Resultado de observación

| Contraste | Tiempos válidos | Consultas válidas | Máximo consultado | Nodo / tiempo | Gate muestreado de 1 mV |
| --- | --- | --- | --- | --- | --- |
| D4/E4G8 | 432/432 | 864/864 | 8,234013 mV | ATTACK_GATE_LOWER / 2,442470360 ms | Falla |
| E4/E4G8 | 430/430 | 860/860 | 0,425517 mV | ATTACK_GATE_LOWER / 2,442476082 ms | Pasa sólo esta selección |

Se guardan **1724 consultas válidas**, de las que **160** requieren otro
anclaje y dos etapas provisionales para respetar el mínimo. No se les aplica
el estimador adaptativo como gate temporal de aceptación: verifican dominio,
ecuaciones, carga y destino exacto, y permanecen sin publicar.

El pico interpolado D4/E4G8 persiste al consultarlo. En cambio, el pico
interpolado E4/E4G8 de 1,001861 mV en ATTACK_OUT baja a **12,896926 µV**
en ese mismo tiempo. El máximo de la selección consultada se mueve a otro
nodo/instante y conserva 0,425517 mV. Una consulta aislada habría omitido
ese segundo pico; se mantiene la selección de los 94 máximos.

Los prefijos muestreados hasta 2,3 ms pasan con 5,233493 µV en 114 tiempos
D4/E4G8 y 0,633425 µV en 116 tiempos E4/E4G8. Son conjuntos finitos propios,
sin cota continua ni sustitución del contraste D4/E4 anterior.

Los ocho registros FD representan **seis casos distintos**: en D4/E4G8
ambos nombres de pico coinciden, dando dos casos repetidos; en E4/E4G8
son cuatro casos. Todos pasan el gate original de 10 nV, con máximo
2,842171×10⁻¹⁴ V respecto de la consulta analítica. FD comparte el circuito
y no crea un oráculo espacial o físico independiente.

La [gráfica de las tres comparaciones](../evidence/loudness_latch_bdf_growth_dc_comparison.png)
usa sólo datos guardados y fija hashes antes/después. Se inspeccionó el PNG;
sus metadatos distinguen el piso visual logarítmico de los valores reales.
Usa las dependencias opcionales de `requirements-plot.txt`.

El resultado **no promueve 0,125 como controlador predeterminado**. Cambia
poco el total de intentos, aumenta controles modales aceptados y conserva
8,234 mV frente a D4. El próximo gate es cuantificar propagación de memoria
y defecto temporal con referencia/contraste propio, o declarar otra política
de refinamiento; no ajustar parámetros físicos ni retimar para aprobar.

## Regresiones cerradas

**10/10 regresiones nuevas pasan** el 2026-10-01: seis del barrido y cuatro
de observación. El recibo registra un intento exitoso, exit code cero,
103,166 s y 88,696 s por suite, entradas sin cambios y salidas completas.
Verifican publicación directa de cada intervalo principal/medio guardado,
linaje ante rechazos, todas las propuestas de crecimiento/halving,
reproducciones seleccionadas, las 1724 publicaciones observadas, selección
de máximos y repeticiones FD con JSON canónico. Sumadas a las cinco pruebas
matemáticas de este corte, son **15 regresiones nuevas**; no se afirma
haber repetido toda la suite histórica.

El productor DC registra HEAD `efd74b0` al iniciar; observación y validación
registran `5e6cea8`. Los SHA enlazan los bytes exactos de fuentes y entradas
guardadas en este corte: el HEAD contextual no sustituye esa identidad.
No se editó ninguna fuente fijada durante su ejecución.

## Recibo de validación

`python tools/validate_bdf_growth_dc.py` ejecuta las suites específicas del
barrido y de la observación en procesos separados. Guarda comandos, conteo
de pruebas, salidas completas, exit codes y SHA de entradas antes/después.
Cada ejecución añade un intento a
`evidence/loudness_latch_bdf_growth_dc_validation.json`. Si una prueba falla,
conserva también su fuente UTF-8; el fallo no se sustituye por el reintento.
Los nuevos JSON de este corte fijan sus bytes con `-text` en
`.gitattributes`, para conservar los SHA al guardar/restaurar Git.
La evidencia matemática tiene sus cinco regresiones propias en el
[corte de defecto y memoria](BIESTABLE_DEFECTO_Y_MEMORIA.md).
