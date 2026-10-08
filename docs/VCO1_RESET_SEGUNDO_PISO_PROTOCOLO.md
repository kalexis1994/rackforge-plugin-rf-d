# Segundo piso del reset: comprobar la causa local

2026-10-08. El recorrido privado con grilla 1,9073486328125 ps rechazó tras 99028 ticks / 188,88092041015625 ns desde la historia original, por PrecisionLimit. Original y replay de la campaña quedan conservados. No ampliar otra vez el dominio de dt ni lanzar otro recorrido.

Con la última memoria completa de ese prefijo, resolver el full de 2 ticks y los dos half de 1 tick con la misma copia privada congelada. Comparar los tres con Decimal100 desde la historia, KCL y masa bajo gates originales; registrar todas las raíces y la fila limitante de step doubling. No modificar el núcleo, constantes, tolerancias o intento anterior. Pila 8 MiB y compiler fijado. Esto es diagnóstico condicional de un intervalo, no método continuo, ciclo, audio ni deadline.
