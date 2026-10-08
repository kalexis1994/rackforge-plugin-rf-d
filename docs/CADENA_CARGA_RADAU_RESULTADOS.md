# Mixer/filtro/VCAs: carga explícita y Radau

## Cierre local disponible

Dos módulos nuevos del crate, `chain_charge` y `chain_radau`, representan
la cadena con 68 tensiones y memoria hi/lo: 66 nodos anteriores, BUS y
nodo izquierdo de C10. Conservan F de `circuit66::linearize_dc`, red ON,
17 capacitores y C10. C27 queda explícito entre BUS/BASE_Q29. Se conserva
el circuito condicional de SVC-9 pp.19/13/10 y ambas alternativas R61.
Los antiguos adaptadores mantienen su contrato de125 ns..1 ms.

La cadena ahora tiene un solver Radau contrastado localmente con medios
pasos de7,629 ps, compatible en ese punto con el piso del VCO. Las fuentes
siguen impuestas; todavía no se confirmó VCO/cadena conjuntamente. El
paso pequeño no identifica el instrumento ni acredita estabilidad de una
nota larga, régimen de voz completa o tiempo real.

## Banco ejecutado

[Oráculo06](../evidence/voice_chain_charge_reference06.json): doce escenas,
dos R61, una/cinco entradas ON y full de125 ns/31,25 ns/15,259 ps.
Cada escena resuelve full/mid/end con historia fija; 72 etapas en el banco
final. Historia de nodos heredada del oráculo independiente anterior,
sin raíces Rust como semillas. C10/BUS se levantan desde esa historia;
otros capacitores se representan por diferencias de nodos, no se declara
identidad por bits con todas las memorias redondeadas del adaptador Euler.

| Observación nativa | Máximo | Gate |
|---|---:|---:|
| 72 etapas frente al oráculo | 1,377e-14 V | 1e-6 V |
| 180 corrientes de fuente | 2,118e-22 A | 1e-9 A |
| Error full−end normalizado | 8,036e-4 | 1 (2 µV) |
| 264 filas físicas Euler a125 ns frente al módulo anterior | 8,743e-13 A | 2e-10 A |
| 221.952 entradas de Jacobiano / tolerancia FD | 2,233e-4 | 1 |

Todos los pares admiten residual<=1e-13 A y corrección<=2e-9 V; filas
de igualdad usan residual<=1e-11 V. Se contrastan 1632 columnas de etapa.
Ocho combinaciones estructurales R21 extremo/C10 abierto, serie cero,
positiva o positiva de1e-20 ohm conservan las filas de igualdad sin memoria
dinámica. No son ocho eventos ni ocho trayectorias independientes de contacto.

[Cuatro tests nativos](../evidence/voice_chain_charge_native04.json) pasan.
Heap cero medido en un solve al intervalo pequeño y rechazo por dt fuera
de dominio, fixtures y asserts fuera. No se atribuye ese conteo a todos
los caminos posibles. 239 tests heredados por identidad, cuatro nuevos:
243 cubiertos; los replays e intentos anteriores no suman nueva cobertura.

## Precisión y procedencia

Q/h se evalúa por ramas, desde incrementos hi/lo. También se acumulan
las correcciones de etapa hi/lo: compensar sólo la memoria absoluta no
garantiza conservar una diferencia pequeña dentro de un incremento común.
El oráculo usa Decimal80 para acumular estados/cargas, interfaces físicas
binary64 y Jacobiano DC por FD con direcciones NumPy. No es una evaluación
física Decimal100 ni una referencia continua. F(hi)+Jdc(hi)·lo mantiene
el contrato de primer orden y Jacobiano quasi-Newton del VCO.

Se conserva el [protocolo inicial](CADENA_CARGA_RADAU_PROTOCOLO.md) y la
[enmienda de incrementos](../evidence/voice_chain_charge_increment01.json)
antes de ejecutar el nativo. No se relajaron tolerancias. El cuerpo de
`circuit66`, sus tarjetas, controles y módulos anteriores permanece intacto.

Los intentos del oráculo quedan conservados: conversión Decimal→NumPy,
rechazo al evaluar cargas con matriz densa, clase longdouble de Windows
y otro rechazo de representación. El intento05 pasó sus gates internos,
pero falló contra el nativo: primeras48 filas del oráculo DC expresaban
corriente entrante y las cargas añadidas usaban corriente saliente.
El [recibo de reparación](../evidence/voice_chain_charge_sign01.json)
conserva raíces, test fallido y replay; sólo orienta esas filas del adaptador.
El06 pasa la comparación. Un error sintáctico `.5` del test nativo y su
replay también quedan conservados. No hay que confundir esa compilación
fallida con un rechazo eléctrico.

GNU fijado, O2 y pila de laboratorio8 MiB. Ninguna medición de deadline,
pila mínima, otra plataforma, callback host o audio nuevo. C10 cero usa
contacto exacto; R21 conserva su igualdad y KCL sumada, sin epsilon.
La constante serie C10 se deriva de R14+1330−R30, con unidades ohm.
Fuentes, alimentaciones y ajustes deben mantenerse durante cada intervalo.
Estados finitos y normalizados hi/lo, tensiones dentro de±40 V; dominios
de dispositivo y controles se heredan del DC anterior. La serie se evalúa
como R14+(1330−R30) para conservar una R14 positiva muy pequeña; sólo
cero exacto es contacto. El banco nominal anterior se conserva y se repiten
los cuatro tests con esta corrección numérica y dos casos estructurales nuevos.

## Siguiente cierre

Construir el stamp conjunto del VCO y esta cadena: quitar su frontera de
BUS impuesto, transferir R6/R45 una sola vez, conservar la selección y
reconstruir el cursor. Las etapas Radau deben compartir tensiones,
corrientes y derivadas, y confirmar ambos estados sólo tras resolver el
conjunto. Este banco admite el dominio local de la cadena con fuentes
impuestas; no valida todavía esa realimentación o una nota completa.

[QA del bloque](../evidence/voice_chain_charge_tests01.json).
