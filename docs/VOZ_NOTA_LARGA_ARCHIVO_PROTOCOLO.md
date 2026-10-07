# Notas largas con archivo reversible y presupuesto serial

2026-10-07. Prospectivo; los preflights anteriores se conservan.
Requiere [control binario](VOZ_NOTA_LARGA_EXPORT_BINARIO_PROTOCOLO.md) admitido
y auditable. No cambia build11, circuito, 350 ms, ON 10 ms/OFF 200 ms,
vectores, ventanas o gates. Las cuatro escenas parten de DC propio.

## Preparación y control de archivo

Preparar, sin SPICE, dos contenedores del mismo archivo binario completo
del control: gzip nivel 9 y XZ preset 6/CRC64. Conservar su raw y ASCII.
Leer cada contenedor hasta EOF y exigir SHA256 y tamaño **exactos** del
original descomprimido. Registrar versiones, tamaños, tiempos y hashes de
helpers antes/después. Conservar todo fallo; no redondear o diezmar valores.

Estimar cada nota por sus filas cortas medidas ×8,75, 19 columnas binary64
y la cabecera observada. Estimar archivo por la densidad comprimida del
control. Es una estimación, no una cota ni una prueba de compresibilidad
de otra escena. Presupuestar el total de archivos retenidos, el mayor raw
intermedio, y 2 GiB. Este pico incluye ambos formatos al verificar el
último archivo; no sumar como si cuatro raws coexistieran.

Elegir el primer contenedor admitido por ese presupuesto, en el orden
gzip→XZ. Si ninguno pasa, no lanzar el banco. La elección sólo cambia
almacenamiento. Exigir disponibilidad actual antes de cada escena.

## Producción serial y conservación

Ejecutar las cuatro escenas en orden 500→250→125→Trap125, con presupuesto
SPICE de 7200 s **por proceso**, independientemente de un rechazo previo.
Archivar también exports parciales. Después de cada proceso, guardar su
recibo original y producir el contenedor en una ruta nueva de esta campaña.

Antes de retirar **ese raw intermedio recién generado**, verificar por
streaming todos sus bytes restaurados, SHA y tamaño, y conservar el SHA
del contenedor. Registrar el vínculo raw→archivo y el retiro del intermedio.
Un error deja el raw intacto y bloquea el retiro. No borrar o mover archivos
de campañas históricas, fuentes, modelos, logs, decks o recibos.

La restauración para medir/auditar usa una ruta temporal de esta campaña,
comprueba bytes y pasa el array al lector binario admitido. Su buffer propio
debe cerrar los handles antes de liberar ese temporal en Windows. El
contenido original sigue disponible exactamente en el contenedor.

Registrar recursos y recibos al terminar cada escena, con manifiesto final.
Una falta posterior de recursos deja escenas pendientes y el banco sin
admisión; no equivale a un rechazo eléctrico. Conservar aborto y timeout
separados de archivos corruptos y errores de lanzamiento.

Reproducir las cuatro coberturas y tres contrastes con los helpers largos
congelados. Ningún prefijo completa una ventana faltante. No convertir
mejor compresión o una escena completa en admisión del conjunto, audio,
identificación física o deadline de tiempo real.
