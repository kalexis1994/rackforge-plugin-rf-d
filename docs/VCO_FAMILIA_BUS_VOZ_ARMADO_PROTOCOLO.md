# Armado de etapas y LU en la voz cargada

2026-11-07. Usar como control la variante con reutilización
de Newton y FMA. Fijar la tabla H128, las historias HIGH/LOW,
los pasos de Radau, los eventos KEY, los cuatro puertos
Schur y los límites de aceptación. Usar los mismos flags
GNU O3 y FMA en todos los contrastes.
[Control validado](VCO_FAMILIA_BUS_VOZ_COSTO_RESULTADOS.md)

En el armado, emitir directamente las filas de propietario
único en orden de columna física. Derivar el orden de
`chain_index`. Inspeccionar cada coeficiente generado,
conservar ceros con signo según el operador previo y usar
la suma previa de ambos aportes en las filas compartidas.

En el LU de los interiores, intercambiar la permutación
en lugar de mover las filas y sus bordes. Mantener el mismo
orden lógico para elegir el pivote y aplicar el mismo
producto y resta, en el mismo orden para cada acumulador.
Usar tramos contiguos de la fila pivote para actualizar
interiores y bordes externos. Conservar el cálculo de
residual lineal, la reconstrucción de estados y los
criterios de refinamiento.

Separar control, armado, LU y combinación en las ventanas
preexistentes de cinco muestras alrededor de KEY y de la
liberación. Comprobar el punto final antes de usar cada
medición. Hacer tres recorridos alternando el orden de
variantes. Reportar la mediana por sección y ventana.

Probar la combinación a 128 muestras a 48 kHz en ambas
reservas, con el mismo reloj y subpasos por muestra.
Exigir los 129 relojes bit a bit, las corrientes R59/R60
y la fase, el mismo intervalo de inversión de colectores,
y los gates densos originales. En las etapas reservadas,
incluida la inversión, contrastar bit a bit el Jacobiano
cargado y las correcciones del residual y de dos retornos
excitados por separado frente al control. Sólo después
comparar los tiempos sin instrumentación interna. La
medida física requiere reservas y coste con margen.

## Segunda variante tras el contraste de coste

Si el primer contraste no reduce coste, separar la
búsqueda lineal sin Jacobiano de la representación de
etapa completa. Compartir armado de corrientes, cargas
y fase BUS con la etapa completa. Medir el residual
de prueba con los mismos estados compensados y orden
de operaciones. Eliminar del resultado intermedio las
dos tangentes vacías, conservando el armado y todos
los límites de las raíces completas.

Como alternativa de LU, mantener el almacenamiento
contiguo y el intercambio físico original cuando el
pivote cambia. Omitir intercambios de una fila consigo
misma. Recorrer los mismos tramos de actualización por
pares contiguos, conservando productos y restas.

Repetir los cuatro contrastes con los mismos gates.
Mantener ambos ensayos y su separación por sección.
