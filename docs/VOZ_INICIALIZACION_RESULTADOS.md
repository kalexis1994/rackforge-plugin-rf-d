# Inicialización conjunta y diagnóstico de asentamiento

2026-10-09. [Protocolo](VOZ_INICIALIZACION_PROTOCOLO.md),
[convenciones de matrices](VOZ_INICIALIZACION_MATRICES.md),
[QA](../evidence/voice_joint_startup_tests01.json).

## Condición inicial que ahora se resuelve

`joint_startup::condition` resuelve las200 coordenadas del circuito
VCO1→BUS→cadena hasta J7 en DC, con una restricción explícita RAMP_C1=0.
Los capacitores quedan abiertos en el cálculo DC; sus tensiones iniciales
se obtienen del estado conjunto admitido. El solve conserva incrementos
y estado high/low, límites Newton64/24 y las puertas anteriores.
Recibe la semilla del llamador; no genera una semilla analítica propia
de toda la voz ni simula el encendido físico del instrumento.

Dos semillas —lift histórico y perturbación+1 mV de las coordenadas de
cadena— convergen en cuatro iteraciones/tres trials. Máxima razón residual
nativa1,958e-4 del gate; las raíces coinciden a3,549e-9 de1 µV/1 nA.
La corriente de restricción es−16,399949372 µA con la convención del
stamp. Se devuelve como observación de inicialización: no permanece
en el motor dinámico. El clamp impide considerar esta raíz DC libre
del oscilador. Tampoco demuestra unicidad global.

El [oráculo](../evidence/voice_joint_startup_reference01.json) usa VCO
Decimal100 y cadena Python/FD. Comprueba400 ecuaciones DC y correcciones
en esas dos raíces nativas declaradas: máxima fracción residual9,816e-7
de sus puertas2e-11 A/2e-10 V. No busca raíces independientes.

## Memoria histórica y memoria condicionada

La inicialización del [ciclo anterior](VOZ_PRIMER_CICLO_RESULTADOS.md)
levantaba una memoria de cadena tomada de otro banco transitorio y
asignaba su BUS al del arranque aislado del VCO. Esa historia era
explícita y válida para aquel banco; no era DC conjunto.

El nuevo DC cambia la tensión inicial de C27 (BASE_Q29−BUS) en
−0,930504872443 V, equivalente a−9,30504872443 µC para10 µF. Es la
mayor diferencia entre las18 tensiones capacitivas auditadas. No se
atribuye a un error de componente ni se ajusta un capacitor para ocultarla.
La raíz cambia muy poco las demás tensiones capacitivas: la mayor diferencia
restante es≈1,714e-7 V en una celda de ladder. Por eso observar únicamente
J7 o nodos aislados no describe la coherencia de la memoria acoplada.

Esta raíz condicionada constituye otra inicialización. El banco de5,25 ms
conserva su estado inicial y admisión propios. No se reemplazan sus
checkpoints, ni se atribuyen sus resets a la nueva condición inicial.
Durante una trayectoria viva, sustituirla por DC alteraría todas las
cargas: este API se aplica antes de comenzar la evolución.

## Liberación corta contrastada

Desde la primera raíz se ejecutan dos continuaciones libres hasta2 µs
exactos, con máximos de medio paso125/62,5 ns.14/20 intervalos admitidos,
68 medios endpoints, sin la corriente de clamp. LTE máximo0,475618 del
gate2 µV/2 nA; BUS<=1,803e-21 A y C1<=2,202e-14 A.

Los full/mid/end seleccionados del primer y último intervalo pasan
24 etapas/4800 ecuaciones independientes, cuatro diferencias temporales
y sus historias compartidas. Refinamiento de las200 coordenadas al mismo
reloj: máxima fracción7,164e-4 del gate. No se ejecutó un reset/ciclo de
esta nueva inicialización, ni se acredita una nota asentada con2 µs.

Dos presupuestos inválidos y una semilla no finita se rechazan. Las
funciones reciben estado por valor; los candidatos se devuelven solo
al admitir la raíz. No se midió heap ni deadline de este nuevo API.

## Ganancia local de la cadena

Se exportan las matrices G y C de68 coordenadas de cadena evaluadas en
el DC conjunto. Todas las4624 entradas de G se comparan con FD del
oráculo y C con las18 incidencias independientes. BUS se impone solo
para este diagnóstico de pequeña señal; no se impone en la trayectoria
conjunta. El estímulo1 V es normalización de V/V, no una simulación de
entrada finita de1 V en el circuito no lineal.

| Frecuencia | Ganancia BUS→J7, V/V | Ganancia, dB |
|---:|---:|---:|
| 10 Hz | 0,01648556 | −35,6579 |
| 100 Hz | 0,12840161 | −17,8286 |
| 410,801759 Hz | 0,004478657 | −46,9770 |
| 1000 Hz | 0,000163501 | −75,7296 |
| 10000 Hz | 1,345262e-7 | −137,4239 |

Las cinco soluciones complejas pasan residuo y comparación de las68
coordenadas contra el oráculo; máxima fracción de diferencia2,028e-5
del gate1 µV+1e-4|referencia|. Con estos controles nominales, una componente
de BUS de10 mV a410,8 Hz daría≈44,8 µV en esta linealización. Esto es
una inferencia local, no una predicción de toda la onda de J7, sus
armónicos o el transitorio no lineal. La ganancia pequeña es compatible
con el nivel observado y no justifica normalizar J7 como una nota final.
Abrir el filtro u otro control será una escena física distinta que requiere
su propio banco, no una corrección arbitraria de nivel.

## Polos locales y alcance de su escala

El diagnóstico usa las18 coordenadas de carga y reconstruye sus
autovectores en las68 coordenadas exteriores. Ambas ecuaciones pasan
residuo relativo<=1e-8. Se conservan18 modos finitos, incluidos tres pares
complejos, y50 coordenadas algebraicas; estas últimas no se cuentan como
polos físicos. Todos los polos calculados tienen parte real negativa en
este punto de operación. No se obtuvo una cota de error espectral ni una
certificación de estabilidad no lineal de la voz.

Los tiempos reales más lentos son≈264,582/77,373/60,170 ms; los rápidos
≈180,338/95,738 ns. El punto local combina escalas muy diferentes.
La ventana5,25 ms equivale apenas al≈2 % del tiempo más lento observado.
Su excitación y observabilidad dependen de la historia y los controles:
no convertir264,582 ms en una cota global de asentamiento o en un plazo
obligatorio de simulación. La frontera BUS fijada también distingue
estos polos de los modos del sistema VCO/cadena completo.

## Identidad, coste y próximo bloque

El [nativo](../evidence/voice_joint_startup_native01.json) tardó≈5,14 s
en compilación y banco; sin fallos en este intento. Compilador fijado,
O2, caller con strip=symbols y stack32 MiB. Espacio libre muestreado
antes/después de cada proceso acotado, no vigilancia continua. Reserva
1 GiB y estimación12 MiB; no se borró evidencia anterior.
248 tests Rust heredados por identidad, sin tests Rust nuevos. Las
ecuaciones y escenas del laboratorio no aumentan ese conteo.

Las tarjetas físicas, motor temporal, gráficos y módulo conjunto anterior
conservan sus bytes. No hay nuevo SPICE, audio, fidelidad o RT.
Siguiente: usar esta condición inicial en un banco de ciclos propio y
definir un criterio de periodicidad/carga por ciclo. Las escalas locales
orientan el diseño de ese banco; antes de una extensión larga, medir
coste y considerar una inicialización periódica contrastada por carga,
sin sustituir la evolución no lineal por esta linealización.
