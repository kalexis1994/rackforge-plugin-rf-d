# VCO y contorno cargado: resultados de unión

2026-10-06. El contorno cargado y la voz de contorno fijo conservan sus
admisiones anteriores. **La unión VCO/contorno físico sigue rechazada.**
Se preservan todos los ensayos, sin cambiar grafos, tarjetas o gates.

## Unión monolítica

El [protocolo congelado](CONTORNO_VCO_UNION_PROTOCOLO.md) une VCO1,
R6/R45, filtro, ambos VCA, salida y circuito de volumen/gatillo. Las
cuatro escenas debían completar 40 ms. El log identifica timestep demasiado
pequeño en JQ7_left, tarjeta LAB_E402. Últimos clocks exportados:

| Escena | Último tiempo, ms | Resultado |
| --- | ---: | --- |
| Gear2 / 500 ns | 2.277224604 | Rechazo en reset |
| Gear2 / 250 ns | 4.554610124 | Rechazo en reset |
| Gear2 / 125 ns | 6.831777634 | Rechazo en reset |
| Trap2 / 125 ns | 6.831777813 | Rechazo en reset |

[Archivo de cuatro escenas](../evidence/loudness_voice_screen01.json.gz).
Alcanzar un reset posterior con menor paso no completa la trayectoria ni
admite los contrastes de frecuencia, salida o carga. No se fabrica audio
extendiendo estas trazas parciales.

## Cálculo dividido en el puerto físico

El [protocolo de R45](PUERTO_VCO_CONTORNO_PROTOCOLO.md) mantiene la reacción
de carga mediante iteraciones de ambas historias completas. Empieza con
contorno fijo 2 V: debe cerrar el puerto y reproducir el monolítico nominal
antes de abordar la envolvente real. Tolerancias: 10 microvolt, 1 nA,
polilínea de entrada 1 microvolt y máximo diez iteraciones.

| Ensayo | Resultado del control previo |
| --- | --- |
| [01](../evidence/voice_port_relaxation01.json.gz) | Dos solves completos; adaptador rechaza redondeo final de un ULP |
| [02](../evidence/voice_port_relaxation02.json.gz) | Primera pareja no cierra; segundo VCO rechaza a 2.277234922 ms, con aviso PWL |
| [03](../evidence/voice_port_relaxation03.json.gz) | Aviso PWL eliminado; mismo rechazo del segundo VCO a 2.277234922 ms |
| [Expresión 01](../evidence/voice_port_behavioral01.json.gz) | Dos parejas completas; tercer VCO rechaza a 2.277414319 ms |

La primera pareja presenta defecto BUS **0.772148407 V** y corriente
**23.398447 microampere**, aunque cada solve completa 40 ms. La representación
por [expresión temporal](PUERTO_VCO_EXPRESION_PROTOCOLO.md) permite otra
pareja: defectos **0.132847370 V** y **4.025678 microampere**. Ambos siguen
fuera de los gates. Dos valores decrecientes no prueban contracción ni
garantizan que otra iteración complete.

El resistor VCO satisface I=(R6-BUS)/R45 con error máximo observado
1.36e-20 A. Ese contraste local tampoco cierra los puertos: las corrientes
de ambas soluciones aún difieren por microamperes. Las fuentes temporales
permanecen fronteras iterativas; no se declara una voz acoplada por el hecho
de haber propagado una onda hacia el filtro.

## Identidad y regresiones

La [auditoría final](../evidence/loudness_voice_validation02.json) verifica
**17 recibos**, diez trayectorias completas y siete parciales, sus decks,
logs, exports, ejecutable y fuentes congeladas por Git. Reproduce cuatro
defectos de parejas completas sin nuevos solves. Conserva el par CRLF/LF
identificado del grafo histórico; no normaliza otras fuentes. La
[auditoría anterior de doce recibos](../evidence/loudness_voice_validation.json)
también se conserva.

Las regresiones cubren la unión física sin fuente de onda/ADSR, dominio de
eventos, balances acumulados de ambos C2, clocks no uniformes, signos de
corriente, puntos rápidos de reset, errores de polilínea y rechazo de
historial parcial/no finito. Las tarjetas y los grafos eléctricos de la
revisión anterior permanecen idénticos. El cierre del puerto, refinamiento
del banco conjunto, audio nuevo y tiempo real no están admitidos.

## Próximo bloque

El ensayo ahora reproduce el fallo en **VCO aislado con BUS variable bajo
R45**, sin colocar la placa 4 en su matriz. Esto ofrece un caso más pequeño
para estudiar reset y transferencia de carga. Prioridad: resolver ese caso
con la misma tarjeta y contrastar contra el VCO constante y la unión nominal
que completan. No ampliar bancos o duración mientras falle el control previo.

Después: cerrar el puerto en las cuatro políticas, recuperar el contorno
físico, contrastar Note On/Off y extender la nota completa. Contorno de
filtro, alimentación compartida, base Q21 real, otros VCO/ruido y motor
portable siguen pendientes. No hay identificación de una unidad vintage.
