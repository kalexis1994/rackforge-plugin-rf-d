# Coordenadas de carga y terminales de riel fijo

2026-10-09. Errata de notación del
[condicionador](VOZ_CARGAS_SEMILLA_PROTOCOLO.md), con
[bytes anteriores](../evidence/voice_joint_seed_cycles_rail_before01.json) y
[contraste](../evidence/voice_joint_seed_cycles_rail_reference01.json).

Para un capacitor lineal, `v_c=Eᵀx−v_fijo`, `Q=C·v_c`.
Si ambos terminales están en x, `v_fijo=0`. Si el terminal b es un riel
impuesto, E no tiene su columna y la coordenada `Eᵀx` incluye solamente
el terminal a. La corriente es `C·Eᵀ·dx/dt` mientras ese riel sea fijo.
Así, conservar Eᵀx conserva Q bajo el mismo riel, pero Q absoluto no
se obtiene multiplicando la coordenada por C sin restar su referencia.
Si cambia el riel, hay que incluir explícitamente su diferencia y corriente.

En esta escena, el capacitor de índice 11 conecta nodo 40 al riel PLUS,
según SVC-9 pp.13/10 y `circuit66::capacitors`. PLUS=+10 V es la frontera
de laboratorio de `mixer_chain_lab::controlled_boundary`, no una nueva
afirmación sobre todos los rieles del Model D. El capacitor vale 220 µF;
su tensión física es `x40−10 V`. El stamp de incrementos de `chain_charge`
elimina la derivada del terminal fijo y conserva la misma incidencia.
Las otras referencias fijas de la lista son 0 V; BUS y C10 son dinámicos.

Los objetivos anteriores contienen coordenadas Eᵀx. El contraste suplementario
publica también sus tensiones físicas/cargas absolutas con referencias,
verifica las 18 cargas de cuatro raíces y preserva los recibos anteriores.
Memoria 0 conserva las 18 cargas físicas, y memoria 1 cambia solo C27.
Los cambios por ciclo y los balances de corriente ya usaban diferencias:
la referencia fija se cancela exactamente. No cambian roots, checkpoints,
componentes, Jacobianos, motor temporal ni trayectorias.
