# Construcción y factorización en sitio, antes de medir

2026-10-13. Basecf79a8d, QA3251 fuentes/7726 privados. Conservar los
experimentos negativos y sus trazas. Una única intervención principal:
cambiar la vida de los buffers grandes, partiendo del Schur estable
con residuo de soporte exacto, sin las tres variantes no elegidas.

Inicializar un workspace local seguro de tamaño fijo en solve_observed.
Llenar los dos interiores64 y exterior330 directamente en sus buffers;
factorizarlos mediante &mut, devolviendo sólo Result<()>.
Prepared::initialize y Sparse::initialize escriben en sus destinos sin
devolver sus agregados grandes. Conservar permutaciones, orden, pivotes,
umbrales y finitud. Reponer todos los coeficientes de cada matriz antes
de factorizar; no conservar un factor ni un coeficiente de otro J.
Reiniciar escalas, índices y respuesta de puertos en cada preparación.

Sin unsafe, MaybeUninit, heap nuevo, caché entre trials o cambios físicos.
El workspace es local a una resolución; un rechazo no publica estado.
Conservar458 correcciones y229 estados, HIGH/LOW, masa, puertos y cargas.
Tres refinamientos, gate mixto1e-11, capacidad4096 y rechazos originales.
La API evita retornos grandes por construcción; no atribuir ahorro de
copias del binario sin evidencia adicional de compilación.

Exigir identidad de84 raíces y396 J/b/correcciones con los datos previos,
heredando por esa identidad sus gates Decimal100. Reejecutar12 regresiones
de estructura y9 de LU/RHS, adaptando explícitamente la API. Probar también
reutilización del workspace después de otra matriz y de una preparación
fallida: ningún dato residual puede sobrevivir a initialize exitoso.

Cinco rondas alternadas, warmup separado, mediana>1 para utilidad. Si
1<mediana≤1.10, confirmar una sola vez el mismo ejecutable/packet; exigir
ambas medianas>1. Si falla, consolidar sin otro intento de optimización.
Una utilidad aprobada aún requiere contrato temporal propio antes del
recorrido completo. Sin admisión RT, fidelidad física o audio nuevo.

Compilación120 s, banco/diagnóstico/auditor600 s;64 MiB nuevos privados,
reserva1 GiB, stack32 MiB. Biblioteca congelada;248 tests Rust heredados.
