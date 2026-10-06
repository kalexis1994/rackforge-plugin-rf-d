# Candidato activo de seis correcciones: controles antes de otra nota

2026-10-06. Prospectivo, aún no compilado ni medido. Requiere el
[ensayo sobre copia](VOZ_NOTA_LARGA_SEIS_CORRECCIONES_RESULTADOS.md), identidad
de sus dos controles y gate lineal de las dos matrices contrastadas.
El candidato anterior y sus rechazos se conservan.

## Cambio admitido y preparación

Derivar build11 de build09, con compiler y configuración idénticos.
Cambiar sólo el límite del bucle de tres a seis en `RFLinearSolve` y el
texto de anuncio de activación. Verificar ese diff, todo el árbol fuente,
los archivos generados y el ejecutable. No utilizar el cálculo sobre copia
de build10 como si hubiese publicado seis.

Mantener pares compensados, FMA, dominio de operandos, matriz/RHS efectivos,
factor SMP/KLU existente y una publicación binary64 al terminar. Las seis
correcciones no evalúan dispositivos, refactorizan o avanzan historia.
La activación sigue explícita; desactivada debe ejecutar el solve original.
Todos los observadores y replay quedan desactivados en los bancos de voz.
Registrar flags, anuncio de seis y ausencia de etiquetas de instrumentación.

No cambiar dispositivos, fuentes, trims, integración, pasos máximos,
tolerancias, `itl4` ni otro límite Newton. Conservar GCC UCRT64 y
`-O2 -g -m64`/`-m64`, make con dos workers. Presupuesto SPICE previo:
900 s por control/escena corta, 7200 s por escena larga.

## Gates secuenciales

1. **Identidad desactivada:** control nominal original de 40 ms, 218786
   filas, reloj y los 31 vectores exactamente iguales a build06.
   Reutilizar el deck histórico por SHA; sólo cambiar export/runtime.
2. **Control activo:** nominal de 40 ms frente al mismo original. Aplicar
   íntegramente los gates de DC, voltaje, frecuencia, conteo y tiempos
   de reset del [protocolo corto](VOZ_REFINAMIENTO_UNION_PROTOCOLO.md)
   y sus helpers congelados; mantener gates y unidades por separado.
3. **Cuatro escenas conjuntas cortas:** Gear2 500/250/125 ns y Trap2 125 ns,
   40 ms desde DC propio y teclado original ON 2 ms/OFF 25 ms. Aplicar
   todos los gates de cobertura, carga y las tres parejas del banco corto.
   El éxito del control simple no permite omitir estos cuatro casos.
4. **Cuatro notas largas:** sólo si pasan los anteriores, ejecutar las
   cuatro escenas y tres contrastes del [protocolo de 350 ms](VOZ_REFINAMIENTO_SIGUIENTE_PROTOCOLO.md),
   ON 10 ms/OFF 200 ms, DC propio y las ventanas originales. Los cambios
   temporales del deck se comprueban por anclajes únicos y reversión.

Antes de preparar, verificar espacio para copia de fuente, exports y
2 GiB de margen. Antes del banco largo, usar las filas/bytes medidos del
nuevo banco corto para estimar la extensión; declarar que no es una cota.
Preservar todo timeout, aborto, export parcial y fallo de medición.
Un rechazo detiene sus fases dependientes y requiere un recibo nuevo;
no reescribir el banco ni aprobar por un prefijo o un promedio favorable.

## Auditoría, costos y alcance

Los nuevos runners y auditores deben reconocer seis explícitamente;
no adaptar la lectura de un anuncio de tres para darlo por válido.
Verificar fuentes, compiler, runtime, deck, logs y exports antes/después;
reproducir decisiones con evidencia empaquetada canónica. Registrar
tiempos como costos del laboratorio, sin extrapolarlos a tiempo real.

Sólo la admisión de las cuatro notas completas permite el adaptador de
escucha congelado. Mantener los bytes y alcance de escuchas anteriores.
Gates de matrices con seis correcciones, cobertura temporal, conservación de
carga, identificación física y RT son afirmaciones diferentes. El
candidato no resuelve otras notas, contorno de filtro, parámetros reales
o extensión de controles sin sus bancos correspondientes.
