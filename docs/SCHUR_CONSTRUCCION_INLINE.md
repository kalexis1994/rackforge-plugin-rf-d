# Integrar constructores grandes, antes de medir

2026-10-13. El perfil privado pasa84 pares por bits: preparación82.47%,
corrección8.75% y residuo0.70% del solve observado. Factor330 anidado:
143.895 ms de309.612 ms de preparación; soporte51.255 ms. Los tiempos
no son una partición aditiva ni un benchmark de deadline.

Ensayar únicamente #[inline(always)] en los constructores Lu::factor,
Prepared::new y Sparse::new, y en las funciones solve/solve_observed.
Esos constructores retornan matrices y estructuras grandes por valor.
La hipótesis es facilitar al compilador la integración de esos retornos
con el llamador; el perfil no demuestra cuántas copias hace el binario.
La causalidad exacta de una ganancia no se atribuirá sin inspección adicional.

Conservar cuerpo, orden, tipos, mapas, pivotes y todas las operaciones.
Sin unsafe, nuevo heap, caché entre Jacobianos o cambios físicos. Las
directivas son específicas de esta compilación, no rendimiento universal.
Mantener tres refinamientos, gate1e-11 y capacidad4096 con rechazo.

Exigir84 raíces y396 trazas J/b/correcciones por bytes frente al kernel
anterior. Cinco rondas pareadas del banco sin instrumentación. Si la
mediana está entre1 y1.10, confirmar una sola vez el mismo ejecutable y
packet con otras cinco rondas; ambas medianas deben superar1. Si no pasa,
conservar el intento sin admitir utilidad. No cambiar flags tras medir.
Doce regresiones de estructura/rechazo deben pasar en el nuevo código.
La trayectoria requiere contrato separado si pasa el banco.
