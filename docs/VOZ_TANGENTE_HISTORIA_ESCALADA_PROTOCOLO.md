# Perturbaciones de respuesta escaladas por paso

2026-10-10. Conservar los intentos 03 y 04 y sus replays: 04 rechaza
STEP_PLUS,10,117,IterationBudget con h≈30,5 ps. Una perturbación absoluta
de corriente no mantiene un cambio de etapa comparable al variar h;
la memoria L2 contiene un coeficiente L/h, no una capacitancia física.

Para cada dirección, partir de ε0=10 µV o 0,1 nA según la coordenada.
Con la respuesta lineal ya calculada t en ambas etapas, definir
`g=max(1, max_k ε0·|t_k|/target_k)` y `ε=ε0/g`, donde target es 10 µV
para coordenadas V y 10 nA para A. Ejecutar perturbaciones ±ε/±ε/2.
Es una regla de selección de entrada, no un gate de error ni un ajuste
posterior al resultado FD. Un predictor falso sigue comparándose con
solves nuevos y con el Jacobiano independiente. Guardar ε por dirección
y verificar la regla al decodificar. No imponer un piso que haga grande
el cambio en los pasos más cortos.

Hx a etapas fijas conserva los tamaños originales en las 200 columnas.
Todos los gates del [protocolo original](VOZ_TANGENTE_HISTORIA_PROTOCOLO.md)
siguen iguales; también biblioteca, escenas, pasos y presupuesto. Esta
política no valida el mapa adaptativo ni una trayectoria periódica.
