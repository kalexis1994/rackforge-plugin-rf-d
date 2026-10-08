# Recuperación del banco125 desde el rechazo Newton

Fijado después del diagnóstico local01, antes de extender otra vez.
Conservar bancos01/02/03 y todas sus fuentes/exports. Banco03 contiene
un perfil250 completo/admitido por sus gates individuales y un125 parcial
rechazado en Newton a12,171591857910155 ms. No admitir su refinamiento.
Original/replay local idénticos en el diagnóstico; una copia instrumentada
muestra corrección descendente con residual fuera de gate. La copia con
Armijo1e−4 sobre residual resuelve las mismas ecuaciones, 64/24 y mismos
gates; tres tríos independientes Decimal100 pasan error local sin dividir.

Banco04 hereda íntegro el perfil250 completo, por hashes y contenido;
no ejecutarlo otra vez. Continuar125 desde su último par completo con
tick absoluto, hi/lo y propuesta reconstruida como en la extensión03.
La única diferencia en el kernel es el criterio de descenso; comparar
bytes con el reemplazo exacto del kernel Radau original. Física, tableau,
Jacobiano, budgets Newton, floor y control LTE permanecen idénticos.
El prefijo125 conserva la búsqueda original; el resto usa residual.
El integrador y gates de todas sus raíces siguen siendo los mismos.

Presupuesto2400 s, reserva1 GiB monitoreada y pila8 MiB. Guardar todas
las filas y tails futuros. Verificar echo y clocks, hash lógico del recorrido
completo, fuentes antes/después y nuevas etapas/corrientes seleccionadas.
Admitir sólo si ambos perfiles alcanzan30 ms y pasan gates previos de
periodicidad, balance y refinamiento250/125. Conformidad y escucha usan
sólo ese banco04 completo. No convertir la recuperación local en admisión
de producción, física, RT, CV/trims reservados o mixer activo.
