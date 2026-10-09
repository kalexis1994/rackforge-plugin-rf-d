# Primer ciclo VCO1 con carga activa hasta J7

2026-10-08. [Protocolo previo](VOZ_PRIMER_CICLO_PROTOCOLO.md),
[extensión de recursos](VOZ_PRIMER_CICLO_EXTENSION.md),
[QA del bloque](../evidence/voice_joint_cycles_tests01.json).

## Circuito y alcance

Perfil clásico CA3046 nominal a25 °C, C4=10 pF, seis CV de−2,1 V,
R61=200 Ω y solo OSC1 ON. VCO1, R6/R45, BUS/C27, entrada, ladder,
recuperación, dos VCAs y J7 se resuelven conjuntamente. Las leyes físicas,
Newton y control LTE del motor anterior conservan sus bytes. El nuevo
observador `joint_currents` aplica las leyes anteriores a ambas etapas:
Qa/Q10 colector y Q7 gate, incluidas sus cargas no lineales y memoria low.
No introduce fuentes de corriente ni modifica la evolución del circuito.

Inicialización condicionada: arranque propio del VCO y memoria anterior
de cadena con BUS levantado al VCO. Toda la evolución posterior pertenece
al solve conjunto. Los contornos, cutoff, volumen/Q21 y demás controles
de la cadena siguen impuestos; otros cuatro generadores están omitidos.
Este alcance no contiene DC propio de toda la voz, contornos eléctricos
completos, otros osciladores o una nota de producción.

## Cobertura y refinamiento

Se comparan máximos de medio paso125/62,5 ns hasta5,25 ms exactos,
2752512000 ticks. Cada intervalo acepta dos medios pasos después de
compararlos con un paso completo. No se extrapola el estado. Las200
coordenadas high/low se comparan en21 relojes comunes separados0,25 ms,
con puertas2 µV/2 nA y sin alinear fase.

| Medición | Máximo125 ns | Máximo62,5 ns |
|---|---:|---:|
| Intervalos admitidos | 23869 | 44745 |
| Medios endpoints | 47738 | 89490 |
| Segmentos conservados | 1 | 3 |
| Primer reset, ms | 2.434474768421 | 2.434474774665 |
| Segundo reset, ms | 4.868738930039 | 4.868738938882 |
| Frecuencia del ciclo transitorio, Hz | 410.801759220511 | 410.801758781921 |
| Máxima razón LTE | 0.9992876221 | 0.9986772238 |
| Peor KCL BUS, A | 9.8256e-20 | 1.1520e-19 |
| Peor KCL C1, A | 9.9226e-14 | 9.9948e-14 |
| Balance integrado relativo C1 | 1.4494e-15 | 1.4123e-15 |

Refinamiento al mismo reloj: máxima fracción 0.01466385892 del gate2 µV/2 nA.
Frecuencia: diferencia 1.84834e-06 cents. Peor diferencia de extremos: 3.26908e-07 V.

| Señal, extremos del ciclo | 125 ns, V | 62,5 ns, V |
|---|---:|---:|
| saw | -1.86040400982 / 1.87257313596 | -1.8604040169 / 1.8725732312 |
| tri | -1.9532559359 / 1.65169606215 | -1.95325626281 / 1.65169580326 |
| pulse | -4.29734477815 / 0.00656013192132 | -4.29734477815 / 0.00656013118773 |
| bus | -0.011938012463 / 0.0103737947608 | -0.011938012505 / 0.0103737952937 |
| j7 | -2.26430572568e-05 / 0.000200357717784 | -2.26430605506e-05 / 0.000200357717608 |

El cruce ascendente de RAMP_C1 por−2 V se interpola entre endpoints
adyacentes. Es un marcador de observación: no interviene en el solve ni
fuerza el reloj. Dos cruces delimitan un ciclo transitorio; no certifican
periodicidad asentada ni calibración física del fabricante. Las puertas
de frecuencia1 cent y extremos5 mV comparan discretizaciones de la misma
escena, sin hardware de referencia.

## Balances y contraste independiente

C1 usa la derivada Radau de sus incrementos compensados. La integral
de las tres corrientes usa ambas etapas con pesos3/4 y1/4 y acumulación
Kahan; no se integra por trapecios una traza de endpoints. Cada segmento
conserva su integral nativa. Decimal100 compara su suma con−10 nF ΔRAMP
del estado inicial/final completo y normaliza por la integral nativa de
la suma de valores absolutos. Esta comparación no reconstruye por otro
programa todas las corrientes de todas las etapas de la trayectoria.

El [oráculo](../evidence/voice_joint_cycles_reference01.json) evalúa
full/mid/end seleccionados del comienzo, ambos resets y final; también
los primeros intervalos tras ambas restauraciones del perfil fino. Mantiene Decimal100
para el VCO y el oráculo anterior de cadena con cargas lineales Decimal
y Jacobiano Python/FD. Verifica residuos y correcciones en candidatos
nativos declarados; no obtiene raíces independientes desde otra semilla.
Comprueba la historia compartida, LTE y las corrientes terminales de
Qa/Q10/Q7 en los medios endpoints seleccionados, puerta2e-11 A heredada
de las filas de corriente del oráculo nodal.

60 etapas / 12000 ecuaciones, 10 diferencias full−end y 60 corrientes terminales. Máxima fracción residual0.000732082; peor diferencia de corriente5.57895e-16 A. El perfil grueso reutiliza su recibo verificado; no duplica cobertura.

Cada medio endpoint registrado conserva reloj, tamaño, intentos, métricas,
señales y corrientes. El codec binario pasa restauración por bytes; no
almacena todas las400 componentes de estado en cada medio paso. Los
checkpoints comunes sí conservan esas componentes. Los parámetros se
reconstruyen con el builder nominal fijado por fuentes; no es un formato
general de presets. Cuatro continuaciones de restore a0,25/2,25 ms
comprueban estado, incrementos y observaciones sin duplicar el conteo.

## Pausa administrativa y continuación exacta

El [intento original](../evidence/voice_joint_cycles_native01.json) queda
con `passed=false`: el perfil125 terminó en842,17 s y el coste medido
motivó una parada cooperativa anticipada del perfil62,5 antes del límite
original900 s. No hubo rechazo del solver. Se conservan fallo de proceso,
fuente, stderr, trazas y checkpoint del prefijo:7875 intervalos hasta
515440640 ticks =0,983125 ms. `administrative_stop=false` en el monitor
original indica que ese monitor no creó la señal; la pausa externa queda
explicada en el [recibo de recursos](../evidence/voice_joint_cycles_resource01.json).

El [llamador de continuación](../evidence/voice_joint_cycles_resume01.json)
restaura ese checkpoint por bits y usa la misma biblioteca física compilada
y ligada por SHA256. No vuelve a integrar el prefijo. La
[enmienda](../evidence/voice_joint_cycles_extension01.json) conserva el
llamador original y declara cinco cambios de IO/recursos: argumento de
restore, inicialización desde checkpoint, límite1800 s, comprobación
agregada de cruces/restores y argumento de CLI. Las puertas eléctricas,
LTE y refinamiento siguen iguales. La primera memoria del segmento nuevo
debe coincidir por SHA256 del bloque binario con la última del prefijo;
el primer endpoint nuevo queda después de ese reloj.

Se reserva1 GiB en ambos procesos; estimaciones48/28 MiB, stack32 MiB.
El segundo caller usa `strip=symbols` para reducir metadata del ejecutable
y enlaza la biblioteca física anterior sin recompilarla. El coste total
de laboratorio no acredita un deadline de audio. No se midió heap en
esta campaña: se conserva la medición limitada anterior por identidad.
Los248 tests Rust anteriores son heredados, no reejecutados ni aumentados
por cada etapa/intervalo del banco. No hay SPICE o audio nuevo.

La [primera QA de release](../evidence/voice_joint_cycles_qa_failure01.json)
y su replay idéntico rechazaron la falta del recibo de salida staged:
su creación falló por quoting de PowerShell/Python. Se conserva el fallo;
la [reparación de staging](../evidence/voice_joint_cycles_staging01.json)
añade el placeholder y repite el mismo auditor, sin cambiar sus fuentes,
leyes, gates ni volver a ejecutar trayectorias.

La continuación01 tuvo después una caída externa de disco: detectó1040076800
bytes libres, por debajo de1 GiB, y conservó una segunda pausa a3,35762451171875 ms.
El [protocolo de recursos](VOZ_PRIMER_CICLO_RECURSOS.md) y la
[continuación02](../evidence/voice_joint_cycles_resume02.json) retoman desde
esa memoria con el mismo caller, sin recompilar. El
[banco agregado](../evidence/voice_joint_cycles_continuations02.json) conserva
ambos fallos administrativos, dos uniones exactas y toda la trayectoria.
El mínimo bajo reserva queda declarado; no se cambia a una ejecución aprobada.
La [fe de erratas](../evidence/voice_joint_cycles_time_label01.json) conserva
el rótulo3,3576225 ms del protocolo y su conversión correcta desde ticks;
el estado binario y la campaña no se modifican.

## Siguiente trabajo

Cerrar una inicialización coherente de cadena/controles y seguir su
asentamiento: comprobar niveles de BUS/J7, offset y periodicidad antes
de preparar el adaptador de escucha. El primer ciclo transitorio no
autoriza repetir J7 como si fuera una nota asentada. Después integrar
contornos y controles, y medir error y coste de las optimizaciones.
Fidelidad vintage, tiempo real y producto conservan sus propias puertas.

## Revisión local del banco conservado

Con los archivos privados disponibles, usar un número de intento nuevo;
los recibos existentes no se sobrescriben. El checker final combina los
segmentos conservados y reutiliza el contraste grueso ligado por hashes.

```powershell
python -B tools/analyze_joint_cycles.py --attempt 2 --extension evidence/voice_joint_cycles_continuations02.json
python -B tools/check_joint_cycles_completed.py --attempt 2 --continuations evidence/voice_joint_cycles_continuations02.json
```

La QA de release audita el conjunto staged y sus identidades; no lanza
otra trayectoria. Un checkout sin los archivos privados conserva las
fuentes y recibos públicos, pero no permite repetir estos análisis locales.
