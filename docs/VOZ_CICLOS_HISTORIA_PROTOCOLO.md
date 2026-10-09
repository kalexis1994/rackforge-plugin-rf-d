# Comparación de historias y condición media de C27

2026-10-09. Complemento previo al análisis retrospectivo. No modificar el
banco temporal activo, sus fuentes, gates, historia ni presupuesto.
Reconstruir los brackets de los dos resets del banco histórico ya admitido
usando sus traces, checkpoints y medias etapas seleccionadas. Coarse tiene
un segmento; fine tiene el prefijo y sus dos continuaciones congeladas.
Las uniones deben conservar checkpoint/clock por bytes. Estados de eventos
deben pertenecer a las medias etapas publicadas, sin resolver raíces nuevas.

Comparar las200 coordenadas interpoladas a rampa=−2 V y las18 cargas.
Es observación, no solución de DAE ni gate de periodicidad. No reconstruir
la integral C1 entre resets mediante trapecios de corrientes de endpoints:
el ledger histórico no guardó las cuadraturas acumuladas en esos eventos.
Conservar explícitamente esa limitación. Los tests/contrastes anteriores se
heredan por identidad; este análisis no vuelve a integrar aquellas escenas.

## Restricción media de la red nominal

En esta escena OSC1 usa la ruta saw46→cursor39 con12,5 kΩ, cursor→masa
con12,5 kΩ y cursor→BUS12 con33 kΩ. Las otras cuatro rutas están OFF.
Son las ramas documentadas en el banco VCO/panel conjunto; no generalizar
esta derivación a otras formas, posiciones de potenciómetro o fuentes ON.
Auditar en todos los endpoints publicados la KCL del cursor y
`I_C27(BUS→entrada)=(cursor−BUS)/33000` dentro de1e-12 A, gate heredado.

La eliminación exacta del cursor da
`I_cursor→BUS=(0,5·saw−BUS)/39250`, con R_th=33 kΩ+(12,5 kΩ||12,5 kΩ).
Para V_C27=entrada6−BUS y C27=10 µF, una carga que se repite después
de un periodo requiere promedio ponderado de Radau de
`0,5·saw−BUS` igual a cero. Es condición necesaria, no prueba de órbita
periódica ni de fidelidad. En endpoints reales consecutivos, la variación
de carga implica `I_medio=−C27·ΔV_C27/Δt`; registrar ese valor y
R_th·I_medio como desbalance medio requerido. No afirmar haber guardado
o integrado independientemente todas las etapas de voltaje.

R_th·C27=392,5 ms corresponde únicamente a la subred RC con saw y
entrada6 impuestos como tensiones rígidas. No es polo calculado de la
voz acoplada ni bound de asentamiento. La matriz previa con BUS impuesto
excluye la dinámica libre de esta frontera; sus265 ms locales no fijan
el tiempo global. Usar las identidades y la deriva medida para formular
una semilla de régimen oscilatorio; contrastarla después, sin escoger
una historia solo porque su salida parezca favorable.

Recibos exclusivos, identidades antes/después, fallo y replay sin cambiar
fuentes si un contraste falla. Sin audio, SPICE, compilación o nueva
integración; los datos históricos privados siguen en sus rutas originales.
