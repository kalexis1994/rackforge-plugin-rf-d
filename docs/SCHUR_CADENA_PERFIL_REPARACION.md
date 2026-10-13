# Contar el retorno temprano de la primera etapa

2026-10-13. El primer perfil y su replay conservan1834 campos por bits,
iteraciones y trials de84 raíces. El auditor rechaza su igualdad supuesta
parts=2×linearize: observa460 entradas a linearize y856 a parts.
[Rechazo preservado](../evidence/voice_schur_refined_chainprofile01.json),
[replay con los mismos conteos](../evidence/voice_schur_chain_profile_replay01.json).

El kernel evalúa parts0? antes de parts1?. Un error de dominio en la
primera etapa retorna antes de llamar a la segunda. El siguiente observador
privado registra ambos rechazos por separado, conservando orden y operaciones
del kernel. Exigir parts=2×linearize−rechazos0 y
linearize=solves+rechazos0+rechazos1; ningún stamp de una etapa rechazada
llega al solve. Contrastar nuevamente todos los bits con la fuente intacta.

Esta corrección reemplaza el supuesto de conteo del
[protocolo previo](SCHUR_CADENA_PERFIL_PROTOCOLO.md), no los gates eléctricos
ni la identidad requerida de las raíces. Los tiempos siguen siendo anidados,
incluyen overhead de observador y no constituyen un benchmark de utilidad.
No se modifica el solver, la campaña temporal ni un parámetro físico.
