# Recuperación de dos presupuestos enormes sin cambiar el cálculo

Las ramas de radio 10 µV, índices 5 y 6, del [prefijo dirigido](BIESTABLE_PREFIJO_DIRIGIDO_RESULTADOS.md)
conservan un fallo de registro de enteros de 4300 dígitos. Este ensayo
repite exclusivamente esos dos cierres usando sus ocho celdas archivadas,
matrices, forcing, ganancias, anclajes y pico entrante conocidos.

[Protocolo](BIESTABLE_CIERRES_ENTEROS_PROTOCOLO.md) y
[productor](../tools/loudness_latch_bdf_static_precision_large_closure.py)
se congelan en `2d961a5`. Datos, cuatro pruebas y validator, en `59a0630`.
La política explícita sys.set_int_max_str_digits(0) permite texto decimal
exacto sin límite de longitud. No cambia la aritmética racional, el dominio
de kernel <=4096, las normas, el circuito o ningún gate numérico.

## Resultado

Ambos cierres ahora completan sus ocho celdas y **exceden el tubo de 10 µV**.
Los presupuestos permanecen fuera del rango binary64 de visualización;
sus fracciones exactas y kernels completos quedan archivados. Sus
numeradores tienen 4663 y 8951 dígitos respectivamente. La excepción
anterior no era evidencia de ese exceso: el nuevo presupuesto sí lo prueba.

Hay dos propagaciones nuevas y cero solves, precondicionadores, recintos,
consultas de tasa o acciones nuevos. No se transportan sus salidas. El
prefijo certificado conserva seis intervalos hasta ≈6,25 µs, error nodal
≤0,754 µV y primer soporte sin certificar índice 6. Ninguna selección se
reescribe y los intentos de registro originales permanecen en su informe.

## Validación y archivo

Las cuatro pruebas pasan al primer intento en **42,0994302 s**, con
fuentes intactas antes/después. Reproducen ambos cierres, fuentes,
almacenamiento y alcance;
un control y'=3000*y transporta cuatro tramos dentro del dominio de cada
kernel, con cota de más de 5000 dígitos. Una exponencial racional independiente
de 64 términos contrasta el kernel positivo de 32 términos. También se
rechazan soportes o fuentes que no coinciden con los dos fallos identificados.
[Recibo](../evidence/loudness_latch_bdf_static_precision_large_closure_validation.json).

[Datos](../evidence/loudness_latch_bdf_static_precision_large_closure.json.gz):
15109425 bytes, SHA comprimido
`16865c653a5e755e6ff5e7b7af8a15ac0c649c8a0e77a56ea684194342b849ad`,
canónico `b1f0064a3939d7a8997350df34d4af827d584811d1471f374e532013fa892a1b`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_large_closure_summary.json)
y [corpus conjunto](BIESTABLE_PREFIJO_DIRIGIDO_ENTRADAS.md).

Recuperar el registro permite distinguir fallos de archivo y presupuestos
numéricos. No estrecha estas cotas, identifica componentes vintage o
admite una voz, hardware, audio, 1 mV global o deadline.
