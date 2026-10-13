# Localizar el costo después de la reducción estructural

2026-10-13, antes de perfilar. Exterior272→140 ofrece una utilidad marginal
confirmada. Para decidir el siguiente bloque, observar el conjunto reducido
con una copia privada instrumentada; no añadir otra variante de optimización.

84 parejas congeladas. Una ejecución de kernel público intacto y otra de
la copia instrumentada por pareja. Exigir identidad de1834 campos por bits,
iteraciones y trials antes de aceptar tiempos. Timers/counters fuera del
kernel público, del benchmark y de la campaña temporal. No admitir RT.

Fases anidadas: step, linearize, parts, solve, prepare, soporte disperso,
factores64/58/132/140, RHS por tamaño, reconstrucción y residuo. RAII local
recoge el intervalo incluso si se retorna antes; no cambia cálculos, gates
o firmas. Separar calls de tiempos; no sumar fases contenidas unas en otras.
Verificar parts=2×linearize,396 solves/preparaciones/soportes/factores
58/132/140 y792 factores64,416 correcciones/residuos y RHS exteriores.
El perfil incluye overhead del observador y no acredita utilidad de costo.

Ligar fuentes, compiler/flags, output y packet por hash. Compilación120 s,
experimento600 s; mismo stack32 MiB, presupuesto agregado64 MiB y reserva1 GiB.
Preservar fallo/replay antes de reparar. Registrar el costo dominante como
orientación para la siguiente intervención, sin atribuirlo a copias o heap
del binario si esas causas todavía no se midieron.
