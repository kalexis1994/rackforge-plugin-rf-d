# Retorno de regeneración del filtro

## Ruta comprobada

La **Fig. 9-11, SVC-9 PDF p. 13** (SVC-204D completo p. 69) muestra el nodo de recuperación entre **R7, 180 Ω**, y **R3, 1 kΩ**. Ese nodo llega al **polo positivo de C10, 10 µF**; el otro polo va al **pin 7** de la placa 4. No es una conexión directa desde el colector de Q8: R3 separa ambos nodos. La **Fig. 9-17, SVC-9 PDF p. 19** (SVC-204D p. 75) lleva pin 7 al cursor de **R14 de panel, 50 kΩ REV AUD**, y pin 6 al extremo superior del mismo potenciómetro. La resistencia eléctrica de esa ruta puede variar entre 0 y 50 kΩ; la ley de giro no está calibrada. El extremo inferior no forma parte de la ruta pin 7–pin 6 dibujada.

De regreso en la placa 4, pin 6 alcanza el extremo derecho de **R73, 1 kΩ REGEN CAL**. Su cursor es la base de **Q30**. El extremo izquierdo llega por **R76, 330 Ω**, al nodo `BOTTOM`, que también pertenece al pie del ladder. La [transcripción](../evidence/filter_regeneration_path.json) coteja las Fig. 9-11 y 9-17 con la tabla 7-8 de piezas, SVC-9 PDF pp. 30–31. R73 es un **ajuste de servicio**, distinto de la perilla R14. El par Q29/Q30 inyecta la diferencia entre la entrada de audio y esta señal de retorno al ladder, pero aún falta su ley activa.

## Dos puertos pasivos condicionados

La [referencia ejecutable](../tools/filter_regeneration_reference.py) impone el voltaje del nodo R7/R3 como fuente ideal, fija `BOTTOM` como masa de pequeña señal y deja abierta la base de Q30. Para R14 expresado como resistencia real `R14ₑ` de pin 7 a pin 6 y R73 como dos segmentos `R73_L + R73_R = 1000 Ω`:

```text
R_abajo = R76 + R73_L
R_arriba = R14ₑ + R73_R
H(s) = V_Q30base / V_R7R3 = s·C10·R_abajo / [1 + s·C10·(R_abajo + R_arriba)]
```

Las entradas son Hz y Ω; C10 está en F; `s` está en rad/s y `H` es adimensional. El capacitor bloquea la componente DC de la **ruta de retorno**. El polo de esta red aislada es `1/[2π·C10·(R14ₑ + R73 + R76)]` y el límite de ganancia a frecuencia alta es `(R76 + R73_L)/(R14ₑ + R73 + R76)`. Por ejemplo, con R73 a mitad eléctrica, R14ₑ=0 da un límite de **0,624** y un polo de **11,97 Hz**; R14ₑ=50 kΩ da **0,0162** y **0,310 Hz**. Estos números son controles de aritmética de la **ruta aislada**: no son frecuencia de corte del ladder ni nivel de autooscilación. Tampoco equivalen a las posiciones físicas 0/10 de EMPHASIS.

La tabla 7-8 asigna a C10 tolerancia **+50/−10 %**; los valores anteriores usan 10 µF nominal. La impedancia del tap R7/R3, el sesgo de Q30, `BOTTOM` dinámico, la carga del panel, R61 [aún conflictivo](ENTRADA_FILTRO.md), la no linealidad del par y la ganancia de la etapa recuperadora alterarán la transferencia real. Por ello el cálculo comprueba conectividad y escala pasiva sin fijar un coeficiente de resonancia para DSP.

## Contrastes siguientes

1. Transcribir R7/R3/C9/R6 y Q8 para calcular la impedancia real del tap, además de su voltaje.
2. Acoplar R73/R76 al nodo `BOTTOM` de C24/R61 y modelar la corriente de base de Q30.
3. Resolver el par Q29/Q30 con la fuente de cola Q28 antes de cerrar el lazo del ladder. Sólo entonces simular autooscilación y pérdida de graves a distintos niveles.

```powershell
python tools/filter_regeneration_reference.py
python -m unittest discover -s tests -q
```

Las pruebas verifican aislamiento DC, límites de alta frecuencia, partición del trimmer y sentido de variación de la perilla en el modelo condicionado.
