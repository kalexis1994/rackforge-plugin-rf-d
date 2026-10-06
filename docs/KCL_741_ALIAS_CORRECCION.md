# Corrección de observación: pin formal e instancia expandida

2026-10-06. El primer banco conserva exactamente las cuatro trayectorias,
pero rechaza el gate de observación completa. El pin formal 1 de LM741
es `QB_COLLECTOR` en XIC3; no existe el nodo interno `xic3.1` buscado.
Los [recibos](../evidence/voice_kcl_runs01.json) y la
[fuente fallida](../evidence/voice_kcl_observation_rejection01.json) se preservan.
No son cuatro rechazos nuevos de circuito ni evidencia de la KCL buscada.

Copiar build/fuente en `newton-build04` y resolver el pin a través de los
dos decks congelados antes de compilar. Cambiar únicamente el nombre de
búsqueda del observador en NIiter. Mantener coeficientes, registros, circuito,
runtime y el [protocolo](KCL_741_RESET_PROTOCOLO.md). Ejecutar otras cuatro
trayectorias con sonda apagada/encendida y los mismos gates exactos.
Tres regresiones cubren alias externo, case, instancia ausente/duplicada,
modelo incorrecto y nodo interno que no es un pin formal.
