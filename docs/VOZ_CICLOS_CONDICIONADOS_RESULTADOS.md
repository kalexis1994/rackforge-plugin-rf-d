# Ciclos con carga desde la inicialización conjunta

2026-10-09. [Contrato previo](VOZ_CICLOS_CONDICIONADOS_PROTOCOLO.md),
[ejecución](../evidence/voice_joint_conditioned_cycles_native 01.json),
[contraste](../evidence/voice_joint_conditioned_cycles_reference 01.json) y
[QA](../evidence/voice_joint_conditioned_cycles_tests 01.json).
CA 3046 nominal con las fronteras de laboratorio anteriores. Se continúan
los checkpoints de 500 µs por bytes, reloj, propuesta y cargas, sin volver
a condicionar la memoria. Scene conserva el builder histórico, que calcula
una semilla VCO no utilizada: esa llamada no reancla la trayectoria conjunta.
No se declara encendido físico ni semilla analítica conjunta propia.

## Cobertura admitida

| Máxima media etapa | Intervalos totales con prefijo | Medios endpoints | Frecuencia del periodo observado | Balance C 1 de todo el recorrido |
|---|---:|---:|---:|---:|
| 125 ns | 23853 | 47706 | 410.801106 Hz | 1.71681439e-15 |
| 62.5 ns | 44705 | 89410 | 410.801105 Hz | 1.83671259e-15 |

Ambos perfiles llegan exactamente a 5,25 ms/2.752.512.000 ticks. Dos
seams prefix→continuación conservan el checkpoint completo; 22 anclas
cada 250 µs,21 relojes no iniciales comparados en 200 coordenadas a
2 µV/2 nA. Cuatro replays exactos de restore, a 250 µs y 2,25 ms por perfil,
excluidos de integrales/contadores. 68558 intervalos y 137116 medios
endpoints publicados. Sin rechazo eléctrico ni stop administrativo.
La peor fracción del gate de estado al mismo reloj es 0.0223384805;
diferencia de frecuencia 7.20395584e-06 cent y
mayor diferencia de extremos 3.54385077e-07 V.
Las mediciones de extremos son observaciones de endpoints, no cotas
continuas entre muestras.

Se contrastaron 9600 ecuaciones en 48 puntos de etapa nuevos: first/reset 1/
reset 2/final, full/mid/end de ambas continuaciones. Ocho LTE seleccionados
y 48 corrientes de terminales en 16 endpoints; peor ratio independiente de
residuos 0.000717284647, corrección 1.14567639e-06 y corriente
5.87262175e-16 A frente al gate 2e-11 A. El prefijo conserva su recibo
anterior de 4800 ecuaciones. Los puntos candidatos son nativos, no raíces
buscadas de forma independiente ni una segunda integración completa.
248 tests Rust heredados por identidad; cero nuevos/re-ejecutados aquí.

## Carga y estado por ciclo observado

Cada perfil contiene dos cruces ascendentes de rampa por −2 V: un periodo
completo entre ellos, no una secuencia de periodos asentados. El ledger
publica los estados compensados de ambos lados de cada cruce y las
integrales C 1 acumuladas. Brackets y estados coinciden con trace y con
las medias etapas contrastadas. Se reportan las 18 cargas de cadena y
las 200 coordenadas antes/después.

| Perfil | ΔV C 27 a fase interpolada | ΔV C 10 a fase interpolada | ΔJ 7 a fase interpolada |
|---|---:|---:|---:|
| 125 ns | +5.804078 mV | -286.807498 µV | -818.378401 µV |
| 62.5 ns | +5.804078 mV | -286.807500 µV | -818.378402 µV |

La interpolación Decimal 100 hasta rampa=−2 V es un diagnóstico, no otra
solución del circuito ni un gate de periodicidad. Anchos de bracket:
0.48828125 ns, 0.48828125 ns, 0.48828125 ns, 0.48828125 ns.
El balance C 1 usa la diferencia de integrales nativas entre endpoints
reales y la carga de esos endpoints decodificada independientemente;
ratios 1.4829007e-15, 1.42237774e-15,
dentro de 0,002. La diferencia de fase de endpoints también queda registrada.

La deriva observada de las cargas y J 7 permanece a la resolución fina.
Un DC conjunto condicionado correcto y un balance KCL cerrado no prueban
que la trayectoria libre se haya asentado. Tampoco la ganancia/modalidad
local de una cadena con BUS impuesto certifica su régimen no lineal.
Los ciclos del lift histórico siguen válidos para aquella otra memoria;
no se reemplazan por estos resultados ni se convierten en arranque físico.

## Comparación retrospectiva y condición media

El [análisis histórico](../evidence/voice_joint_history_cycles_reference 01.json)
reconstruye eventos de los dos perfiles anteriores desde sus estados
seleccionados, con dos seams adicionales en fine. No reintegra aquellas
escenas ni resuelve raíces nuevas; conserva traces y recibos previos.

| Perfil | ΔC 27 histórico | ΔC 27 nuevo | ΔJ 7 histórico | ΔJ 7 nuevo |
|---|---:|---:|---:|---:|
| 125 ns | +0.225064 mV | +5.804078 mV | -223.000775 µV | -818.378401 µV |
| 62.5 ns | +0.225064 mV | +5.804078 mV | -223.000778 µV | -818.378402 µV |

Son diferencias a fase interpolada, bajo la misma escena nominal y con
historias distintas. La menor deriva histórica no admite aquella memoria
como régimen asentado: también cambia entre cruces. Allí no se guardó
cuadratura C 1 acumulada en cada evento; no reconstruirla con trapecios de
corrientes de endpoints ni trasladar el nuevo ledger a esa historia.

La [derivación previa](VOZ_CICLOS_HISTORIA_PROTOCOLO.md) usa las ramas
del [protocolo BUS](VOZ_BUS_CONJUNTO_PROTOCOLO.md): SVC-9 pp.5/19, R 6 de
25 kΩ a 0,5 y serie 33 kΩ; pp.19/13/10 para C 27 y cadena. Eliminar el
cursor da `I_cursor→BUS=(0,5·saw −BUS)/(39250 Ω)`. KCL del cursor, dirección
C 27 y fórmula Thévenin se comprueban en todos los endpoints de ambas
historias y resoluciones, dentro de 1e-12 A. Ninguna ruta ON adicional.

Para que C 27 repita su carga, el promedio ponderado de Radau de
`0,5·saw −BUS` debe ser cero. La nueva deriva implica un desbalance medio
de ≈-0.935846 V; el histórico,
≈-0.036289 V,
calculados desde los cambios de carga de endpoints reales y sus tiempos.
Son condiciones necesarias de esa red; no se guardaron todos los voltajes
de etapa para una segunda integral independiente. La condición media
orienta una inicialización distinta sin imponer otra transferencia.

R_th·C 27=392,5 ms sería la escala de la subred con saw y entrada 6 rígidos;
**no es un polo calculado de la voz ni un warmup adoptado**. La matriz con
BUS impuesto del diagnóstico anterior excluye esta frontera dinámica.
Este resultado explica por qué sus polos locales no bastan para decidir
el arranque de la red acoplada; no se atribuye causalidad exclusiva a C 27.

## Recursos y decisión siguiente

Continuaciones seriales de 785.005672 s, 1246.10445 s;
campaña 2032.28835 s, outputs nuevos 22878324 bytes. Compilación solo
del caller contra biblioteca congelada. Disco mínimo muestreado 1125371904
bytes, reserva 1 GiB, muestreo cada 250 ms. Stack 32 MiB de laboratorio;
no se mide heap ni deadline del audio. No se ejecutó SPICE ni nuevo audio.

Admitimos el periodo observado desde esta inicialización y su refinamiento,
con periodicidad/asentamiento aún abiertos. Siguiente bloque: preparar y
contrastar una inicialización para régimen oscilatorio con cargas, usando
esta deriva medida y los balances. Toda semilla alternativa necesita
su propia procedencia, restauración de estados algebraicos y trayectoria
refinada; no adoptar un tiempo fijo de warmup del polo más lento ni relajar
gates para ocultar deriva. La voz completa, controles/contornos, fuentes
restantes, fidelidad física y tiempo real conservan sus brechas.
