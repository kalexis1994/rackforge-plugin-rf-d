# Descriptor: variante de solve exacto

El primer ensayo de ocho matrices conserva ocho fallos del solver equilibrado
con backward error cercano a 1. Se declara antes de medir una ruta racional
exacta, sin cambiar H, las consultas, los presupuestos ni las tolerancias.
Se reutilizan las matrices binary64 archivadas y el eliminador racional ya
existente. Verifica H*X=I exactamente antes de redondear una sola vez.
La inversa redondeada sigue obligada a ambos gates backward de 1e-10.
Se conservan ceros estructurales; no se recorta contaminación numérica por umbral.

Las escalas para el certificado se calculan con el mismo equilibrado de filas
máximo absoluto y luego columnas. Toda multiplicación del certificado es
racional exacta. Si q>=1 o el gate redondeado falla, se conserva el fallo.
Un solve exacto de coeficientes levantados no identifica la matriz ideal.
El [protocolo continuo](BIESTABLE_DESCRIPTOR_CONTINUO_PROTOCOLO.md) conserva
signos, unidades, Gronwall congelado, anclaje desconocido y límites de alcance.
Regresiones nuevas identifican ambas rutas por bytes y preservan sus fallos.
