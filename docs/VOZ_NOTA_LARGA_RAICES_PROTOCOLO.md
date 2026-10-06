# Raíces de las matrices capturadas durante el rechazo

2026-10-06. Antes de calcular raíces, exigir el control exacto y el replay
de trayectoria del [observador](VOZ_NOTA_LARGA_MATRIZ_PROTOCOLO.md).
No se cambia el build o el número de correcciones. Este ensayo usa sólo
los sistemas lineales guardados; no evalúa dispositivos ni publica estados.

Selección previa: la **última pareja completa 100/101** en orden del log
con iguales time, delta, order y mode. Si no existe, registrar que el
análisis no pudo prepararse. El límite de dieciséis capturas sigue vigente;
una pareja seleccionada no se presenta como último intento de Newton sin
prueba de cobertura. Mantener todas las demás capturas en el log privado.

Reutilizar el análisis LU Decimal existente: interpretar cada float por
`Decimal.from_float`, resolver a 80 y 120 dígitos con su corrección interna,
comprobar acuerdo y residual con los límites anteriores. Conservar su helper
y SHA; un fallo de precisión del analizador no se corrige en silencio.

Para ambas matrices, separar el SMPsolve original, las tres actualizaciones
compensadas y la publicación final binary64. Reutilizar las comprobaciones
de residual y actualización compilados y el gate lineal ya declarado:
voltajes `1e-8 V + 1e-7·|x|`, corrientes `1e-13 A + 1e-7·|x|`.
Guardar cada fila, unidades de desconocida/ecuación, diferencias y máximos.

Cuatro factorizaciones diagnósticas: dos precisiones por matriz. Cero nuevos
solves SPICE, sistemas no lineales, cambios de aritmética nativa o audio.
Una raíz precisa de A/b no certifica KCL independiente, estabilidad o causa
del rechazo. Si el solve refinado pasa este gate y el TRAN sigue abortando,
conservar ambos hechos: ese contraste local no resuelve el aborto global.
