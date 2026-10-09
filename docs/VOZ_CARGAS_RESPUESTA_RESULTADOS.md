# Respuesta de las 18 cargas y nuevas memorias conjuntas

2026-10-09. [Protocolo de respuesta](VOZ_CARGAS_RESPUESTA_PROTOCOLO.md),
[refinamiento](VOZ_CARGAS_RESPUESTA_FINA_PROTOCOLO.md) y
[cierre/liberación](VOZ_CARGAS_CORREGIDAS_PROTOCOLO.md).
[Respuesta independiente](../evidence/voice_joint_charge_response_fine_reference01.json),
[raíces/liberación](../evidence/voice_joint_charge_corrected_reference01.json),
[objetivos](../evidence/voice_joint_charge_response_targets01.json) y
[QA](../evidence/voice_joint_charge_response_tests01.json).

## Qué se midió

Las dos memorias anteriores tienen respuesta estática de rango 18.
Se resolvieron 36 columnas/7848 entradas de la matriz aumentada de 218
filas, con todas las restricciones de carga y C1=0 V. Condición de S en
A/V: 310372.473 y 310372.473. No se regulariza ni usa
pseudoinversa. Las dos raíces y corrientes anteriores se reproducen por bytes.

146 raíces del banco fino contrastadas: 31828 ecuaciones nuevas.
Tangentes contra Jacobiano/evaluador independiente; peor ratio
3.98272235e-05.
No hay búsqueda de raíces independiente. La tangente describe fase retenida,
no el mapa de retorno periódico. Su rango completo permite intentar una
corrección local; no identifica los polos temporales de toda la voz.

## Perturbación y rechazo conservado

| Memoria | Media perturbación | Peor ratio del gate | Decisión |
|---|---:|---:|---|
| 0 | 1000 µV | 7.17071322 | rechazado |
| 0 | 500 µV | 1.79387684 | rechazado |
| 0 | 125 µV | 0.112140044 | pasa |
| 0 | 62.5 µV | 0.0280354228 | pasa |
| 1 | 1000 µV | 7.17071323 | rechazado |
| 1 | 500 µV | 1.79387685 | rechazado |
| 1 | 125 µV | 0.112140044 | pasa |
| 1 | 62.5 µV | 0.028035436 | pasa |

La [comparación completa](../evidence/voice_joint_charge_response_refinement02.json)
usa idénticas tangentes nativas en ambas compilaciones. El error en fila
215/columna 6 cae aproximadamente como h², consistente con truncación de
la diferencia central. El primer [rechazo y replay](../evidence/voice_joint_charge_response_reference01.json)
queda intacto; no se amplían los gates ni se admiten sus perturbaciones.
El nuevo checker separa el refinamiento de filas de tensión (V/V) y
corriente (A/V), sin un máximo que mezcle sus unidades.

## Corrección conjunta

Para cada historia anterior se observa `m=C·Δv/Δt` entre fases interpoladas
a rampa=-2 V. Las dos resoluciones difieren, a lo sumo,
4.54559561e-13 A por carga,
frente al gate de 1e-10 A. Esta inferencia de deriva no es una cuadratura
Radau de las 18 corrientes. Se resuelve `S·δt=-m`; peor residuo
3.70589839e-21 A.

Máximo cambio de objetivo: 37.157391603 mV y 3.282860796 mV.
Ambos pasos tienen α=1 bajo el límite previo de 0,1 V. Son correcciones
de memoria inicial; se conservan componentes, controles, fase y biblioteca.
El signo de corriente es de a hacia b, y las referencias fijas se cancelan
solo en estos cambios de carga bajo igual riel.

| Capacitor | Terminales de cadena a→b | m memoria 0 (µA) | m memoria 1 (µA) | δt memoria 0 (mV) | δt memoria 1 (mV) |
|---|---|---:|---:|---:|---:|
| índice 0 | 8→12 | +0.009371134 | +0.009464345 | -0.391780431 | -0.027792422 |
| índice 1 | 9→13 | +0.026060470 | +0.023766474 | +0.008529644 | +0.337279996 |
| índice 2 | 10→14 | +0.027768906 | +0.023247477 | +0.439348214 | +0.697951205 |
| índice 3 | 11→15 | +0.013186872 | +0.008694623 | +0.556389049 | +0.710132228 |
| índice 4 | 4→GROUND | -0.937699419 | -0.073996913 | -0.026232620 | -0.040801450 |
| C27 | 6→66 | +0.924565087 | +0.023936840 | +37.157391603 | +0.921827762 |
| índice 6 | 16→11 | +0.005607645 | +0.007729916 | -0.100175132 | -0.109281966 |
| índice 7 | 17→15 | -0.005827430 | -0.008104506 | +0.102586388 | +0.111175010 |
| índice 8 | 23→GROUND | +8.444904166 | +14.101683629 | -0.517850197 | -0.603737647 |
| índice 9 | 24→25 | +0.250920240 | +0.354049550 | -2.852335134 | -3.282860796 |
| índice 10 | 26→GROUND | +0.232134256 | +0.332321913 | -0.004189001 | -0.004843177 |
| índice 11 | 40→PLUS | +0.009990696 | +0.011586181 | -0.000067341 | -0.000074691 |
| índice 12 | 46→47 | +1.650616981 | +2.383691589 | -0.673510227 | -0.778913713 |
| índice 13 | 49→50 | +0.186022757 | +0.284508128 | -0.361965053 | -0.420372839 |
| índice 14 | 57→58 | -0.000254236 | -0.000226045 | -0.893940855 | -1.367505496 |
| índice 15 | 60→61 | +4.293184151 | +6.669753838 | -0.054406661 | -0.063127908 |
| índice 16 | 62→GROUND | +0.000000000 | +0.000000000 | +0.000000000 | -0.000000000 |
| C10 | 67→7 | +0.150020352 | +0.203706038 | -0.045212116 | -0.049939716 |

No tomar `m+S·δt≈0` como medición de mejora de la nueva trayectoria.
Es una predicción estática con fase retenida. Los objetivos nuevos tienen
identidad high/low propia y deben generar su propia historia temporal.

## Cierre no lineal y liberación corta

Los dos objetivos pasan el cierre completo desde dos semillas cada uno:
cuatro raíces/872 ecuaciones aumentadas y comparación de las corrientes
de retención. Se rechazan NaN de estado y objetivo. El caller es idéntico
al anterior salvo el archivo de objetivos; toda la física permanece igual.

Cuatro liberaciones hasta 2 µs, dos resoluciones por memoria: 68
intervalos/136 medios endpoints. Cuatro restores exactos.
24 pares/9600 ecuaciones dinámicas nuevas en 48 puntos de etapa, ocho LTE.
Peor ratio entre resoluciones
0.000716382167.
BUS/C1 KCL, gates de raíz y LTE pasan. No se comparan memorias distintas
con el gate de refinamiento temporal.

Se admite respuesta estática, cierre de estos objetivos y su liberación
corta. La deriva periódica de las nuevas memorias aún no se midió.
Siguiente: ciclos propios con estados completos y cargas a igual fase,
a dos resoluciones; exigir periodos consecutivos para asentamiento.
Sin nuevos tests Rust/audio/SPICE, encendido físico, fidelidad vintage o RT.
248 tests Rust heredados por identidad, sin reejecutarlos.

## Fallos de herramientas y recursos

Se conservan el [fallo de decoder y su replay](../evidence/voice_joint_charge_response_refinement01.json):
el parser de ±1 mV rechazaba correctamente el banco fino. La reparación
selecciona el parser de cada banco y conserva todos los gates.
El [import fallido del exportador](../evidence/voice_joint_charge_corrected_build_failure01.json)
y su replay preservan la fuente anterior; la reparación añade el TwoSum
local que verifica pares normalizados, sin cambiar objetivos.

El [fallo inicial de QA y replay](../evidence/voice_joint_charge_response_qa_failure01.json)
conserva un defecto del adaptador: comparaba tracebacks completos, cuyos
frames del llamador difieren entre intento y replay. La reparación compara
la excepción terminal y mantiene fuentes, fallos completos y gates eléctricos.
El archivo de objetivos declara LF en Git para conservar su identidad
en futuros checkouts de Windows.

Los intentos [1](../evidence/voice_joint_charge_response_fine_native01.json)
y [2](../evidence/voice_joint_charge_response_fine_native02.json) rechazaron
el preflight de disco antes de compilar o medir. El
[intento 3](../evidence/voice_joint_charge_response_fine_native03.json) pasa
después de compresión NTFS transparente, preservando hashes/tamaños.
La [captura binaria protegida](../evidence/voice_joint_charge_response_compression01.json)
y el [export anterior retenido](../evidence/voice_joint_charge_response_compression02.json)
recuperan 788148804 bytes asignados.
El export grande no figuraba en la QA privada anterior: se registra su
identidad antes/después, sin admitir sus resultados eléctricos. Sin borrar
o mover archivos. Stack de laboratorio 32 MiB; solo caller contra biblioteca
congelada, procesos ≤180 s y campañas ≤600 s; reserva 1 GiB.
