# Cómo nos ayuda CA-72

Inspección de arquitectura, 2026-11-06. Fuente primaria fijada en
[CA-72 d268d22](https://github.com/idlefoundry/ca-72/tree/d268d22a0af63a881868968abe5442a43d544f9f),
en particular [Board4](https://github.com/idlefoundry/ca-72/blob/d268d22a0af63a881868968abe5442a43d544f9f/docs/circuit/board4.md),
[supuestos](https://github.com/idlefoundry/ca-72/blob/d268d22a0af63a881868968abe5442a43d544f9f/docs/circuit/assumptions.md)
y [calibración](https://github.com/idlefoundry/ca-72/blob/d268d22a0af63a881868968abe5442a43d544f9f/docs/calibration/README.md).
No se descargó ni ejecutó su motor ni se añadieron dependencias.

La decisión útil es separar la constitución estática no lineal de la
memoria y de los puertos eléctricos. CA-72 trata recuperación con una
transferencia estática y conserva su carga y acoplamientos; además deriva
el ladder de las parejas diferenciales y contrasta cada bloque. Esto
orienta dónde sustituir nuestra linealización, sin rehacer el oráculo.

RF-D aplica esa idea de partición con una derivación propia desde su stamp:
defectos Ebers–Moll BE/BC y eliminación algebraica del sistema de68 nodos.
El [primer bloque](RECOVERY_PORT_RESULTADOS.md) conserva18 memorias de
capacitor, BUS, corrientes de puerto, recuperación, VCAs y auriculares
en el dominio anterior. Sólo seis BJT vuelven a ser no lineales; los demás
siguen linealizados. No es un port de su filtro ni una calibración Moog.

| Reutilizar como método | Mantener propio o contrastar antes |
| --- | --- |
| Separar leyes estáticas y memoria; condensar antes del callback | Valores, revisión SVC-9, cargas y puertos de RF-D |
| Jacobianos analíticos y regresión por bloque | Modelo de transistor e incertidumbre documental |
| Contraste independiente y errores por dominio | Oráculo RF-D completo y reservas no usadas como ajuste |
| Medir coste y rechazar aproximaciones fuera del presupuesto | Controles, autooscilación, antialias y voz completa |

CA-72 distingue variantes documentales y ajustes de su referencia moderna.
Sus tablas, trims calibrados y opciones numéricas no son datos de una
unidad vintage RF-D. Su reducción de estados tampoco acredita por sí
sola nuestros puertos o auriculares. No se incorporan código, tablas,
constantes calibradas o grabaciones suyas. Las coincidencias con nuestro
oráculo sólo prueban el modelo condicional común, no el parecido audible
con un Minimoog físico.

Próximo uso de esta referencia: condensar los pares restantes del ladder
y el convertidor de cutoff, manteniendo corrientes y cargas; separar la
reducción física del integrador. Antes de unir H128/contornos, cerrar el
coste y los dominios reservados. No extender una tabla de matrices para
ocultar el rechazo de nivel grande ni trasladar una aceptación local a
la voz completa.
