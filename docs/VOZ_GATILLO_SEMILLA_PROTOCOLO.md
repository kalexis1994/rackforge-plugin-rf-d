# Recuperación del guess algebraico ante S-trigger

Addendum previo al intento02. El intento01 y su replay desde la misma
semilla agotan64 iteraciones en tramo2/paso0. El diagnóstico instrumenta
únicamente logging: reproduce el rechazo con las mismas ecuaciones/gates.
La base Q12 permanece alrededor0,665 V, por encima del colector de
gatillo≈0,578 V, mientras RESET_DRIVER recorre lentamente≈2,307 V.
Son iteraciones de Newton, no una trayectoria física.

Añadir un predictor de voltajes sólo cuando el contacto y el guess entrante
quedan separados: S cerrado con TRIGGER_COLLECTOR>1 V; S abierto con
TRIGGER_COLLECTOR<1 V. Inicializar un guess compatible con Q12 conduciendo
o bloqueado, sin forzar el candidato aceptado a esas tensiones.
Valores0,03/7/0,45/0,5/0,6/0,7/3,1/6 V son decisiones numéricas de
semilla. No son tiempos, umbrales del contorno ni una elección del latch.

Sólo se interviene en217/218/219/210/211/214/216/224 y en el guess222
de CR10 ya previsto. Ninguna de estas coordenadas tiene almacenamiento
en este modelo. No mover205/C2,221/C7 o223/C4; no editar el estado
entrante. Los dos candidatos de etapa arrancan desde esa misma semilla
de incrementos y todos los trials conservan la memoria completa.

Mantener64 iteraciones,24 halvings y gates originales. Repetir las cuatro
escenas con los mismos inputs y oráculo; exigir que los primeros dos
tramos del perfil ya ejecutado sigan idénticos por bytes. Conservar
fuente/bytes/diagnóstico del fallo antes de reparar. Una semilla aceptada
por Newton no demuestra unicidad, dinámica de dispositivo o conmutación
causal de Q25/Q15, que siguen fuera de esta conexión.
