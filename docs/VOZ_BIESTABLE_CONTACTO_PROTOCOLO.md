# Predictor algebraico del contacto S en229

Declarado tras el rechazo02, antes del intento03, 2026-10-12.
El cierre S reproduce `phase=2,k=0:IterationBudget` sin cambios en replay.
Se conserva el código fallido y los dos tramos ya aceptados.

Se reutiliza el predictor de [Q12/Q20](VOZ_GATILLO_SEMILLA_PROTOCOLO.md),
con RESET_BASE leído del estado entrante227. Sólo se proponen los nodos
algebraicos217/218/219/214/210/211/216/224. No se proponen C2=205,
C7=221, C4_LEFT=223 ni Q25/Q15=225..228. Su carga siempre procede de la
historia original, incluso durante trials. Al abrir S se propone la rama
de driver desactivado, pero la selección de Q25/Q15 depende de sus KCL
dinámicas. Leyes, gates, 64/24 y pasos31.25/15.625 ns permanecen idénticos.

Los predictores son hipótesis numéricas. Se exigen los prefijos01 y02
idénticos por bytes, restauraciones, oráculo y refinamiento establecidos.
Este banco no acredita las cargas omitidas de Q12/Q20 y otros BJT.
