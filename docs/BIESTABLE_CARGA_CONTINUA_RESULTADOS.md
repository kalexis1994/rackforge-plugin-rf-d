# Tasas de carga frente a la DAE continua: resultados

Protocolo/productor fijados en `e3edf8c`, el 2 de octubre de 2026.
Se diagnostican 496 extremos de referencias finas existentes. No se
ejecuta integración nueva, no se cambia raíz, historial ni controlador.
El modelo sigue siendo el circuito condicional de 94 nodos con parámetros
sintéticos; este contraste no identifica el sonido de una unidad vintage.

## Identidades y preparación

Los 496 puntos pasan Decimal80/100 y las tres identidades de
[KCL, ecuación RC y potenciales redondeados](BIESTABLE_CARGA_CONTINUA_PROTOCOLO.md).
Máximo error de precisión normalizado: 6,35385e-40, con gate
1e-30 absoluto +1e-8 relativo. La incidencia continua usa Q' directamente,
sin beta. Conservación dinámica incluye los terminales fijos.

Todos los 496 residuales BDF finos levantados quedan bajo 10 pA;
máximo 9,71957139166e-12 A, en ataque de cuatro subpasos, índice 30,
nodo 67. Los 496 recibos de publicación anteriores también conservan
su aceptación. Son evaluaciones relacionadas, con leyes compartidas;
la evaluación Decimal no constituye un oráculo de otra física.

El residual cúbico continuo cumple 10 pA en **106/496** puntos y conserva
**390 incumplimientos** de esa observación. No se publican estados nuevos.

| Ventana | Máx. KCL cúbica, 2 subpasos (A) | Máx. KCL cúbica, 4 subpasos (A) | Puntos bajo 10 pA, 2/4 |
| --- | ---: | ---: | ---: |
| Prefijo | 6,07191921665e-11 | 1,54762109808e-11 | 0/44 |
| Ataque | 4,40456474180e-8 | 9,21149068849e-9 | 0/0 |
| Reset | 2,56244753569e-11 | 6,41451728403e-12 | 0/62 |
| Cola | 2,24658373523e-10 | 5,62758634736e-11 | 0/0 |

Cada nivel contiene 62 puntos. El máximo es nodo 92 (C2), ataque de
dos subpasos, índice 21, t=0,002422375488281306 s. La identidad separa
el residual BDF fino de la diferencia de diferenciación cúbica; no
atribuye automáticamente a C2 todo el error global de voltaje.

## Regla de la cadena y restricciones de memoria

QBE/QBC se contrastan con Cj(v)*D4v. En reset, el máximo desajuste de
tasa es 1,95717071960e-12 A con dos subpasos y 1,15661957826e-14 A
con cuatro. Hay un soporte de dos subpasos, índice 45,
t=0,0024420673370362457 s, con extremos a ambos lados del knee de Q25 BC.
Los cuatro subpasos no muestran cruce en sus soportes muestreados.
Esto no garantiza regularidad dentro de cada intervalo ni valida una
cota basada en Q''' a través del cambio de pieza.

Máximo Q almacenada menos Q(high+low): 5,25908321209e-26 C.
Máximo cambio de KCL estática al preparar high+low frente a high:
4,83120488140e-16 A. Ambos se guardan completos, sin reemplazar los
estados ni modificar la evaluación histórica binary64.

Las 496 ecuaciones de las 21 ramas capacitivas quedan bajo 10 fV.
Máximo cúbico 1,30815438275e-15 V en C10 serie. La identidad
E4=Eb-R(D4-Db)Q conserva el efecto de diferenciación y el voltaje
interno autoritativo; para las ramas sin R el término es cero.

## Una comprobación que no es independiente

El interpolante cuadrático de los últimos tres tiempos finos es casi
el mismo operador que el BDF2 que produjo el destino. La máxima
diferencia de tasas en todo el corpus es 8,16636579840e-21 A.
Por ello, su pequeño residual continuo no valida una derivada exacta:
reproduce esencialmente una ecuación discreta ya satisfecha. La consulta
cúbica agrega historial y detecta un residual diferente, pero tampoco
es una solución independiente ni una cota de error absoluto.

La reducción observada al refinar es diagnóstico local desde anclajes
compartidos. No acota el error de esos anclajes, la acumulación desde DC,
el residual entre muestras ni el error de voltaje usando solamente A.

## Regresiones y archivo

Cuatro pruebas pasan al primer intento (24,52065 s), con hashes
antes/después idénticos. Cubren los 496 replays Decimal80/100,
24 replays racionales independientes de tasas/incidencias/ecuaciones,
24 evaluaciones estáticas por corrientes de dispositivos, 96 FD de
capacitancia de juntura y 248 diferencias de refinamiento.
La FD permanece en la pieza local y no certifica el soporte completo.

Archivo: `evidence/loudness_latch_bdf_static_precision_continuous_charge.json.gz`,
13.373.820 bytes. SHA comprimido
`01a3ee0127a213d8f5ac247f0a7d7074d6ac8236f87d9e5875908cd20936743c`;
SHA JSON canónico
`8aa8e070977808b882d2fc330818ad2551304fad9d9e5ad5fcddacf3e1615c75`.
El resumen y recibo conservan todas las observaciones, fuentes y alcance.

Siguiente corte: reconstrucción dentro de intervalos, restricciones de
carga y tratamiento declarado de soportes que cambian de pieza antes
de una cota/estimador temporal. El criterio global de 1 mV, física,
audio y deadline continúan abiertos.
