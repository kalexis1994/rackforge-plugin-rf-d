# Refinamiento acotado de Schur, antes de medir

2026-10-13. Base869f4ec y su QA. Preservar todos los archivos de ese bloque,
incluidos ambos gates rechazados y el sistema RFSCHJ01 completo. Objetivo:
reducir el error lineal sin alterar circuito, puertos, masa o estado.

## Algoritmo y rechazo

Factorizar una vez los dos interiores64 y el exterior330 del mismo J.
Conservar L/U y permutaciones; reutilizarlos para nuevos RHS. Formar los
diez vectores de respuesta a puertos sin inversa explícita. Cada solve
reconstruye458 correcciones; no reduce memoria ni elimina cargas.

Calcular r=b−Jd con suma compensada y error de producto mediante mul_add;
incluir −b en la suma. Mantener exactamente el gate mixto1e-11 y tau
2 nV/2 pA del contrato previo. Si falla, resolver J·e=r con los mismos
factores Schur y sumar e a d. Máximo tres refinamientos. Rechazar
no finitos, singularidad, falta de disminución mientras no pasa, o
agotamiento de presupuesto. Sin GMIN nuevo, descartes, proyección de
filas ni fallback a la LU completa. Registrar conteos fuera del timing.

Primero ejecutar el sistema fallido guardado, repetir sin cambios y
contrastar todos sus operandos con Decimal100. Después el banco84.
Una LU completa refinada mediante la LU original sobre el mismo J/b
sirve como contraste adicional; también debe pasar1e-11. Mantener aparte
la comparación de Schur con la LU original sin refinar a2 nV/2 pA.
El refinamiento de la referencia es una nueva variante explícita; no
convierte sus rechazos anteriores en aprobados. Comparar candidatos a
2 µV/2 nA y observar memorias/puertos con los gates anteriores.

## Alcance y recursos

Pruebas de pivotes, singularidades, cargas entre etapas y acoplamientos
prohibidos heredadas o reejecutadas según identidad. Añadir precisión
del residuo frente a Decimal100 y verificación de rechazo por presupuesto.
Las nuevas raíces requieren el grafo/FD/Q Decimal100 completo, sin herencia
por cercanía. Cinco rondas pareadas, warmup separado, mediana>1 para utilidad.
Si la variante pasa banco y utilidad, abrir la campaña temporal en un
contrato separado antes de medir; no heredar balances o restores.

Compilación120 s, sistema guardado120 s, banco/diagnóstico600 s,
auditor600 s,64 MiB privados nuevos, reserva1 GiB y stack32 MiB.
Sin biblioteca/SPICE/audio nuevos o admisión RT. Son algoritmos numéricos
del laboratorio condicionado, no parámetros físicos del Moog vintage.
