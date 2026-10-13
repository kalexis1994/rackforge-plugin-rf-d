# Escala residual antes del segundo diagnóstico

2026-10-13. El contrato inicial y su rechazo permanecen congelados.
El replay del primer sistema rechazado conserva J, b y las correcciones
de ambos métodos en sus filas problemáticas. Decimal100 con operandos
binary64 exactos reproduce 42 filas señaladas; 26 también rechazan la
LU completa. Es un contraejemplo del criterio inicial para el banco,
no una demostración de exactitud de la nueva condensación.

El cociente componente a componente puede valer uno cuando b y la
corrección exacta son cero: cualquier resto diminuto tiene entonces
el mismo tamaño que su denominador. Su magnitud no expresa el error
en las unidades del circuito. Se conservará como observación, incluido
su máximo, sin reinterpretar el primer fallo como aprobado.

## Nuevo gate, declarado antes de medir

Para cada fila, calcular con suma compensada r=Jd−b. Añadir al denominador
original la escala de resolución de las correcciones:

    tau[k] = 2e-9 V o 2e-12 A, según la incógnita original
    scale[i] = |b[i]| + sum_k |J[i,k] d[k]| + sum_k |J[i,k]| tau[k]
    mixed_backward[i] = |r[i]| / scale[i] <= 1e-11

Una escala cero exige residuo exactamente cero. Verificar este gate en
la LU completa y en Schur para cada J/b, sin modificar ninguno de ellos.
La escala es dimensional por fila: no suma voltios con amperios. El piso
de resolución es el gate de corrección Newton ya existente, transportado
por el Jacobiano. Para correcciones pequeñas el residuo permitido es
1e-11 veces ese presupuesto transportado; para grandes, conserva el
control relativo. No se escogió a partir del peor error medido.

Se conserva la comparación directa de correcciones a 2 nV/2 pA y los
gates originales de Newton, además del gate 2 µV/2 nA de candidatos.
No se regulariza, no se modifica un dispositivo ni se elimina una fila.
Registrar cuántas filas incumplen el cociente inicial en ambos métodos,
cuántas pasan gracias a la escala, y sus máximos absolutos y mixtos.
Puertos y memorias originales se verifican antes de admitir trayectoria.
Este documento reemplaza únicamente el gate relativo puro del protocolo
inicial para intentos posteriores; no cambia sus demás presupuestos.
