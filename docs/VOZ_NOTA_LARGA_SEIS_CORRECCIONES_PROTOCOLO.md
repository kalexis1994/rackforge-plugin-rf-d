# Próximo ensayo: seis correcciones con el factor real

## Estado y motivación

Protocolo prospectivo; todavía no ejecutado. Se conservan el candidato de
tres correcciones, sus bancos cortos admitidos y los rechazos de nota larga.
Las dos matrices finales de 226 incógnitas observadas en Trap125 muestran
errores máximos de voltaje aproximados de 180,539 mV antes del refinamiento,
6,848 mV después de una corrección, 259,717 µV después de dos y 9,851 µV
después de tres. El último valor falla los gates lineales existentes.
La reducción observada motiva otro ensayo; no proporciona una cota global
ni demuestra la causa completa del aborto Newton.

## Primera fase: cálculo adicional sin publicar

Build10, GCC UCRT64 idéntico a build09, `-O2 -g -m64`/`-m64`, make
con dos workers. Presupuesto fijo de 900 s para cada control SPICE;
espacio para copiar el árbol y exportar ambos controles más 2 GiB antes
de preparar. Flag explícito `RF_D_REFINE_SHADOW=1`, sólo efectivo con
refinamiento activo y captura de matriz. Etiqueta separada `RFSHADOW`.
Reutilizar las dos raíces ya auditadas; no contar nuevas factorizaciones
Decimal, evaluaciones no lineales ni una variante activa de seis.

1. Derivar otro build con identidad propia de build09. Mantener dispositivos,
   stamps, tolerancias, integración, historia y tres correcciones activas.
2. En las capturas declaradas en el [protocolo de observación](VOZ_NOTA_LARGA_MATRIZ_PROTOCOLO.md),
   conservar la solución compensada tras tres correcciones y calcular otras
   tres sobre una copia, usando el mismo factor SMP/KLU real. Registrar cada
   residual, corrección y actualización; publicar exclusivamente el resultado
   original de tres correcciones. No refactorizar ni evaluar dispositivos.
3. Con el cálculo adicional desactivado, exigir identidad exacta de reloj y
   dieciocho vectores frente al control Gear500 de 40 ms (191714 filas).
4. Activado, exigir la misma identidad frente a Trap125 largo rechazado
   (155680 filas), mismo error y contextos de las capturas. Preservar cualquier
   rechazo de compilación, identidad o tiempo antes de reintentar.
5. Contrastar las seis correcciones compiladas con las raíces independientes
   Decimal 80/120 del [protocolo de raíces](VOZ_NOTA_LARGA_RAICES_PROTOCOLO.md).
   Mantener los gates originales por unidad: voltaje
   `1e-8 V + 1e-7 |x|` y corriente `1e-13 A + 1e-7 |x|`.
   Un residual pequeño por sí solo no admite el error de solución.

## Segunda fase: candidato activo separado

Sólo si la primera fase pasa, preparar otro candidato que publique seis
correcciones, con archivo fuente, ejecutable, protocolo y recibos propios.
Antes de correrlo, congelar controles desactivados, banco activo de 40 ms y
las cuatro escenas de 350 ms del protocolo original. Mantener los gates,
ON 10 ms/OFF 200 ms, ventanas y modelos; no retimar ni extrapolar prefijos.
Registrar costos y errores de dominio. El éxito en dos matrices no permite
omitir el contraste de trayectorias, carga ni integración temporal.

Los presupuestos por proceso deberán fijarse después de verificar espacio
y estimación de recursos, antes de cada lanzamiento. No aumentar `itl4`,
cambiar tarjetas ni relajar tolerancias para aprobar este candidato.
Escucha nueva sólo después de admisión de las cuatro notas completas; la
identificación física y el gate de tiempo real siguen separados.
