# Iteraciones rechazadas del reset: observación local admitida

2026-10-06. Sigue abierto el VCO con BUS variable y la unión con contorno.
No hay nueva tarjeta física, cambio de circuito, audio o admisión de runtime.

## Herramienta y controles

Se compiló ngspice 46 con GCC 16.1.0 UCRT64, `-O2 -g -m64`, Gear2 y KLU.
La distribución queda identificada por SHA y las cuatro fuentes intervenidas
coinciden antes del parche con `ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6`.
XSPICE y su módulo `spice2poly` son necesarios para la fuente POLY del 741.
La compilación y módulos permanecen privados, sin instalación en el sistema.

El [protocolo](NEWTON_RESET_PROTOCOLO.md) conserva el deck del tercer VCO
de `voice_port_behavioral01`: BUS PWL, R45, tarjetas, tolerancias e inicio.
Sólo cambia la ruta de exportación. El ejecutable oficial se mantiene intacto.
Se midieron seis trayectorias: dos sin parche, dos con parche apagado y dos
con observación encendida.

| Caso | Oficial | Baseline local | Sonda apagada/encendida |
|---|---|---|---|
| BUS cero | 223220 filas, 40 ms completos | 219538 filas, 40 ms completos | Exactamente las 219538 filas y seis vectores del baseline |
| BUS variable | 7729 filas; último aceptado 2.277414318997602 ms | 7724 filas; último aceptado 2.277414365034117 ms | Exactamente las 7724 filas y seis vectores del baseline |

La sonda conserva íntegramente la trayectoria local y los resultados de ambos
casos. **El baseline no reproduce exactamente la trayectoria oficial.**
Los últimos estados aceptados del caso fallido difieren unos 46 ps, pero sus
relojes completos y filas son distintos. Esto admite observación del build
local; no transfiere sus iteraciones como explicación del rechazo oficial.

## Qué rechaza en la ventana local

Se observaron 2.2773–2.2775 ms. El BUS variable deja 811 intentos de paso,
2897 iteraciones y 2300 registros de rechazo JFET. Hay 79 reducciones por
truncamiento y ocho retornos no nulos de Newton, todos `E_ITERLIM=103`.
En esa ventana no se activó ningún limitador de los JFET observados.

El último intento tiene h=5e-18 s, orden 1, y agota **101 iteraciones**.
Ambos JFET rechazan en las 101 cargas de ese intento. En su última carga:

| Dispositivo | Error de puerta / tolerancia | Error de drenador / tolerancia | Limitador |
|---|---:|---:|---:|
| JQ7 derecho | 29.1594 | 1.11e-9 | 0 |
| JQ7 izquierdo | 72.4358 | 9.92528 | 0 |

Son diferencias entre corriente predicha y recalculada, incluyendo la carga
integrada. **No son el residual KCL no lineal completo.** El contador del load
es 2 en las últimas iteraciones: una atribución exclusiva al JFET izquierdo
no describe todas las comprobaciones fallidas observadas.

La mayor corrección normalizada en las últimas doce iteraciones es siempre
`xic3.17`. En la última pasa de -1.3798024717 a -1.1722169293 mV:
corrección de 0.2075855424 mV frente a tolerancia de unos 10.138 nV,
aproximadamente 20476 veces el umbral. También hay correcciones de nodo
grandes; no se trata de un rechazo aislado del test de corriente JFET.

El nodo 17 pertenece al polo interno L2/R13 del macromodelo TI LM741:
L2=530.5 mH, R13=1 kohm, con referencia en nodo 98. Su identidad de archivo
está congelada; estos son elementos del macromodelo, no componentes físicos
identificados dentro de un 741 vintage. La observación local permite dirigir
el siguiente diagnóstico hacia ese estado y sus ecuaciones de integración.
Todavía no demuestra una causa física ni que cambiar ese polo resuelva el VCO.

## Fallos de preparación conservados

La primera compilación desactivó XSPICE y rechazó la fuente POLY antes de
simular. La segunda produjo un módulo correcto, pero las comillas del
comando `codemodel` se interpretaron literalmente y volvió a rechazar la
carga. Se conservan [dos rechazos por POLY](../evidence/voice_newton_build_rejections01.json)
y [dos por inicialización](../evidence/voice_newton_build_rejections02.json),
separados de los seis solves del banco final.
Un [rechazo de preparación](../evidence/voice_newton_preflight_rejection01.json)
conserva además el deck y la fuente del runner cuando faltaba la inicialización.
El `make` invocado antes de terminar configure queda registrado con su log.
Ningún error de carga se cuenta como fallo del circuito.

## Auditoría y siguiente paso

La [auditoría](../evidence/voice_newton_observation01.json) verifica todo el
árbol fuente contra la distribución, permitiendo únicamente las cuatro
inserciones observacionales. Comprueba ejecutables, módulos, runtime,
recibos, logs, exports completos/parciales y las dos comparaciones exactas
por caso; vuelve a calcular el resumen sin nuevos solves.
Las [regresiones](../evidence/voice_newton_tests01.json) comprueban el lector,
los gates anteriores, identidad de entradas eléctricas y el WAV previo.

Próximo: observar corriente/flujo e historia del L2 interno, evaluar sus
ecuaciones y escalas junto con carga JFET y residual eléctrico completo.
Cualquier reformulación debe conservar historia, punto de operación y
transferencia terminal, y volver a pasar BUS cero antes de BUS variable.
La sonda local proporciona una hipótesis comprobable; hay que contrastarla
en el ejecutable oficial o mantener explícita la frontera entre builds.
No se cambian tolerancias ni se añade una fuga para ocultar el rechazo.
