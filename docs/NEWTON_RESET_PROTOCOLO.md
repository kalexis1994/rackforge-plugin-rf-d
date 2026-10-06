# Observación del rechazo Newton en reset

2026-10-06. Diagnóstico offline; ninguna admisión de tarjeta, audio o runtime.

## Reproducción congelada

Usar el tercer VCO de `voice_port_behavioral01`, con su BUS PWL original,
R45, JFET, 741, Gear2, KLU, bypass=0 e itl4=100. Comprobar el SHA de la
entrada antes de ejecutar. El primer VCO, BUS cero, es el control positivo.
No modificar ecuaciones, tolerancias, cargas, inicialización o tiempos.

La ventana de observación es 2.2773–2.2775 ms, alrededor del primer reset.
Registrar tras cada solve lineal la mayor corrección normalizada entre
iteraciones, su nodo y valores, y el contador de no convergencia del load.
Registrar para cada JFET las diferencias entre corriente predicha y nueva,
sus tolerancias y el indicador de limitación. Son criterios del solver:
no equivalen al residual KCL completo de la solución no lineal.
Registrar por separado el retorno NIiter y la decisión de truncamiento.

## Identidad de la herramienta

Conservar el ejecutable oficial y sus recibos. Compilar ngspice 46 localmente
en un directorio ignorado; identificar archivo de distribución, compilador,
flags, logs y ejecutables. Comparar las cuatro fuentes intervenidas con la
revisión `ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6` antes del parche.
El archivo de distribución incluye configure, evitando instalar herramientas
de generación. No instalar el resultado en el sistema.

Primero medir el control y la reproducción con la compilación sin parche.
Después compilar únicamente observación activada por `RF_D_TRACE=1`.
Comparar ejecución con la variable ausente y presente y con el baseline.
La admisión de observación exige **igualdad exacta** de reloj y seis vectores
para estas dos últimas comparaciones, incluidas las trayectorias parciales.
Si el baseline no reproduce exactamente el ejecutable oficial, registrar
esa frontera: sus iteraciones no explican automáticamente el fallo oficial.
No reinterpretar semejanza de forma de onda como identidad de la trayectoria.

## Parada y siguientes decisiones

No barrer parámetros físicos ni regularizadores. Si la compilación falla,
conservar logs, corregir sólo dependencias o configuración y registrar ambos
intentos. Si la sonda altera el resultado, rechazarla y conservar el intento.
Una medición finita debe distinguir carga/limitación, corrección de nodo,
iteraciones agotadas y truncamiento antes de proponer un cambio al integrador.
El último dispositivo señalado por el log no identifica por sí solo la causa.

Fuentes primarias: [NIiter](https://raw.githubusercontent.com/imr/ngspice/ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6/src/maths/ni/niiter.c),
[NIconvTest](https://raw.githubusercontent.com/imr/ngspice/ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6/src/maths/ni/niconv.c),
[JFETload](https://raw.githubusercontent.com/imr/ngspice/ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6/src/spicelib/devices/jfet/jfetload.c),
[compilación Windows](https://raw.githubusercontent.com/imr/ngspice/ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6/compile_min.sh).
