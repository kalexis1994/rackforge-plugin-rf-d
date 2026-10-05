# VCO 1: salida de sierra 9B corregida

Fuente: SVC-9 Fig. 9-3 PDF p. 5, contrastada visualmente con SVC-204D
Fig. 9-3 PDF p. 61 el 2026-10-05. Valores: tabla 7-5 pp. 24–25.
No hay medidas de una unidad física.

## Conectividad

9B conecta **R34=4.3 kohm al colector Q3** y **R33=4.7 kohm a masa**.
R34 cruza la barra -10 V sin punto; R33 cruza esa barra sin unión y
continúa hasta el punto en la línea inferior de 9B. Los extremos de
R14/R29/R23/R44/R35 y el emisor de Q12 sí terminan en -10 V.
La interpretación anterior de siete cargas y Q12 en 9B era incorrecta.
[Auditoría y corridas rechazadas](VCO1_AUDITORIA_RETORNOS.md).

## Límite pasivo

Con V_Q3 impuesta y el panel abierto:

`V_9B = [R33/(R34+R33)] V_Q3 = 0.522222… V_Q3`.

`Rth = R34 || R33 = 2245.556 ohm`.

La [referencia](../tools/vco1_saw_passive_reference.py) comprueba esas
ramas. El panel Fig. 9-17 añade el puente de 57 kohm hacia 21B y el
potenciómetro de nivel seleccionado; esa carga debe resolverse junto con
Q3/triángulo. R23 no está en paralelo con el puente: es un retorno de
21B a -10 V. El coeficiente anterior 0.3388 y Rth=1457 ohm se retiran.

El [oráculo acoplado](VCO1_ORACULO_CIRCUITO.md) obtiene 9B de la red,
sin interpolar los extremos de Q3 como una forma de onda ideal.
