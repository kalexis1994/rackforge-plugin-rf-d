# Localizar el costo de Schur, antes de medir

2026-10-13. Base1e02f98, banco numérico admitido y utilidad pendiente.
Conservar3200 fuentes/7706 privados y ambos bancos de costo anteriores.

Primero instrumentar una copia privada del kernel estable. Medir soporte,
preparación, factores64/330, RHS64/330, reconstrucción/corrección, residuo
y solve completo. Tiempos anidados, sin sumarlos como fases disjuntas.
Timers/contadores sólo en el diagnóstico, fuera de los benchmarks y del
algoritmo candidato.84 pares y contraste por bits de los1834 campos,
iteraciones y trials contra el kernel sin instrumentar. Registrar calls.
El costo de retorno/movimiento fuera de un timer no debe atribuirse a
otra fase sin evidencia adicional. No inferir causalidad sólo de wall.

Elegir una intervención después de ese diagnóstico y declarar su alcance
antes de medirla. Conservar aritmética, orden, índices, tres refinamientos,
gate mixto1e-11, puertos, masa e historia. Exigir identidad por bytes de
84 raíces y de396 J/b/correcciones completas; heredar por esa identidad
los gates Decimal100 y memorias, declarando lo que no se reejecuta.
Cinco rondas pareadas, warmup separado, mediana>1 para utilidad. Si la
ganancia es marginal, confirmar el mismo código/packet una vez antes
de decidir. No ajustar tolerancias ni repetir hasta obtener una mediana.

Compilación120 s, perfil/banco600 s, auditor600 s,64 MiB privados nuevos,
reserva1 GiB, stack32 MiB. Biblioteca congelada,248 tests Rust heredados.
Una utilidad aprobada requiere después contrato temporal propio y
trayectorias completas con balances/restores; no admisión RT o fidelidad
física por este banco. Sin biblioteca/SPICE/audio nuevos.
