# Padre sin DC del ladder y reacciones locales compartidas

## Cambio fijado antes del ensayo

La [unión anterior](LADDER_VOZ_RESULTADOS.md) pasa precisión y falla costo
1,542441. El directo sigue activo. Este candidato elimina el segundo stamp
DC del ladder, conserva sus cargas en el padre y usa el stamp final del
solve local para reconstruir las ecuaciones físicas. Misma tarjeta nominal
CA3046/SVC-204D, fuentes SVC-9 pp.9/13/19 y p.10, rama 40–100 ms y KEY OFF
75 ms, semilla HIGH/LOW y perfil VCO. Sin calibración, leyes o dominio nuevos.

Derivar el audio padre quitando sólo las ocho resistencias y diez NPN del
ladder estático (nodos 0–15, Fig.9-11). Mantener las 16 incidencias de carga
y la rama C10 del grafo original, incluido bias 220 µF, sin duplicación.
Conservar recuperación, VCA, salida, controles y cargas de puertos.

El kernel local devuelve DC/J físicos de su última evaluación, junto a las
reacciones y Jacobiano implícito. La congruencia local utiliza el soporte
inmutable de la transformación T (máximo dos entradas por columna), con
finitud comprobada por el stamp original antes de proyectar; no es una
máscara aprendida de escenas. Mantener orden de contribuciones no nulas;
se permite normalizar ceros con signo a +0 en las proyecciones.

Proyectar sólo el padre y añadir directamente el bloque de reacción 9×9.
Comprobar que el DC padre y sus filas/columnas DC de los diez interiores
eliminados/diferenciales son cero; rechazar fuentes/enlaces inesperados.
La masa mantiene M·Tz=0 y Tzᵀ·M=0, con las cargas en el padre una vez.
Para convergencia, sumar el DC/J local a las filas físicas del padre,
conservando 118 nodos, 111 coordenadas por etapa y solver temporal 222.

El stamp transferido pertenece al mismo estado actual. Avanzar HIGH/LOW
puede cambiar su redondeo DD: corregir el DC con J·offset sólo para
offset ≤128·epsilon²·max(1,abs(V)) V, calculado con pares compensados.
Es un límite numérico ligado a ±40 V y al redondeo de las pocas sumas DD,
no un error eléctrico admitido de otro estado. Rechazar offsets mayores,
NaN/overflow o un sello no finito antes de publicar el resultado. No guardar
estos datos entre estados/h/recetas. Validar también la transferencia en
las ecuaciones originales; el margen eléctrico no se amplía.

## Gates previos

- 48 etapas admitidas: contrastar DC/ΔQ/J/masa físicos con la voz completa
  original, 20 pA/2 nS; carga y masa iguales. Contrastar 111×111 reducido
  con la unión anterior, gate derivativo 2 nS+2e-5·abs(ref).
- Contrastar kernel anterior/nuevo desde semillas perturbadas; comprobar
  congruencia TᵀJT con matrices finitas que incluyan cancelación. Rechazar
  metadatos/estado de otro punto, enlaces/fuentes inesperados y recuperar
  la solución válida exacta sin publicación parcial.
- Reejecutar 222 columnas FD y 144 direcciones del bloque anterior, con
  sus mismos gates, y comprobar ambas modalidades FULL/residual.
- Dos trayectorias nuevas 64/32 µs: 481 observaciones cada una, gates
  directos de nodos/estados 20 µV+2e-6·abs(ref), cargas 2 nA+2e-5·abs(ref),
  J7 RMS 0,1 %, pico 0,3 %, media 1 µV. Conservar gates reservados y de
  refinamiento; contrastar también la unión anterior como control funcional.
- Newton físico 1 pA/2 nV, backward 1e-11, estimador físico sin cambios;
  ocho replays, diez rechazos atómicos y heap cero en integración. Auditoría
  independiente de 24 pares/5712 filas originales, 20 pA/2 nV.
- Control directo fresco 32 µs, mismo compilador/rlib/flags/equipo, sin
  timers internos; ratio de promoción ≤0,90. Informar también comparación
  con la unión anterior, sin sustituir ese gate por uno más fácil.

El benchmark pertenece al conjunto: separación del padre, transferencia
del stamp y congruencia por incidencias. No atribuir el ahorro a uno sin
medición aislada. Si falla costo, guardar fuentes/input/replay y mantener
el directo activo. Área única `tmp/lab-current`, sin WAV/Cargo/rlib/inputs
privados de sonido nuevos; retirar binarios después de recibos. Sin nueva
fidelidad física, arranque/CV general o admisión de tiempo real.


## Segundo candidato después de perfil del primer rechazo

El primero conserva precisión y falla costo (ratio 1,924343). Se guardan
fuentes/input/replay. El perfil instrumentado sitúa 8,648849 s en el
llamador del padre, incluyendo su retorno; mide el tramo local en 1,263518 s.
Incluye replays y termina antes del retorno de Stage, por lo que no es un
desglose exhaustivo ni permite atribuir el costo a una copia concreta.

El segundo hace que el padre construya directamente los tipos físicos
State/Controls/Parts originales. Retira el adaptador de resultado 118×118
y sus tipos duplicados; la conversión de contornos/cadena sigue explícita.
No se atribuye ahorro antes de medir. Repetir los mismos gates y controles
frescos, preservando receta, cargas, unidades, finitud y publicaciones.
