# Entrada de la placa 4: C27 y par Q29/Q30

## Fuentes y alcance

La **Fig. 9-11, SVC-9 PDF p. 13** (SVC-204D completo p. 69) dibuja la entrada del filtro. La **tabla 7-8, SVC-9 PDF pp. 30–31** identifica componentes de la placa 4; su [transcripción de nodos y valores](../evidence/filter_input_board4.json) conserva una discrepancia importante. Se trata del esquema nominal documentado, aún sin confirmar la población de una unidad o revisión concreta. No hay un Model D físico para medir.

El pin 4 recibe el [bus de cinco fuentes](MEZCLADOR_PANEL.md). **C27, 10 µF**, une ese bus al nodo `BASE` con el polo positivo hacia Q29. `BASE` llega a la base de **Q29** y, por **R54, 470 Ω**, al nodo `BOTTOM`. `BOTTOM` es simultáneamente el extremo inferior de la cadena del ladder (debajo de R52), el extremo superior de **C24, 220 µF** y el de **R61**; C24 y R61 van a masa. **Q29/Q30 son un par TIS97 emparejado**, con emisores comunes en `TAIL`, que baja por **R60, 680 Ω**, hacia Q28. La base de Q30 llega al cursor de **R73 REGEN CAL**. Su [ruta de retorno](REGENERACION_FILTRO.md) pasa por pin 6, la perilla EMPHASIS y C10 hasta el nodo de recuperación R7/R3; la ley activa del lazo aún no está calculada.

## Valor conflictivo de R61

En la Fig. 9-11, el rótulo junto a **R61** se lee `200`, sin `K`. La tabla 7-8, p. 31, lo lista como **200K Ohm** (número de parte `852-512204-001`, ±5 %). No escogemos uno como valor real del instrumento. La diferencia por factor 1000 afecta al sesgo y al tiempo de descarga de `BOTTOM`. Incluso el producto aislado `R61·C24` cambia de **44 ms** a **44 s**; ese producto **no** es un polo de audio del circuito completo porque `BOTTOM` también carga R54 y el ladder. La próxima verificación es otro esquema o revisión de placa independiente, una fe de erratas o una placa con procedencia comprobada.

## Referencia pasiva condicionada

La [referencia ejecutable](../tools/filter_input_reference.py) resuelve sólo `C27–R54–(C24 || R61)`. Exige el voltaje del bus, las corrientes que Q29 y el ladder extraen de `BASE` y `BOTTOM`, y una elección explícita de R61: **200 Ω** o **200 kΩ**. Corriente positiva sale del nodo hacia la frontera activa. Las ecuaciones, en amperios, son:

```text
C27·d(V_BASE − V_BUS)/dt + (V_BASE − V_BOTTOM)/R54 + I_Q29 = 0
C24·dV_BOTTOM/dt + V_BOTTOM/R61 + (V_BOTTOM − V_BASE)/R54 + I_LADDER = 0
I_PIN4 = C27·d(V_BUS − V_BASE)/dt
```

La implementación usa Euler implícito para las dos cargas y devuelve residuos KCL. Las unidades internas son V, A, Ω, F y s. Con corrientes activas impuestas en cero, un voltaje **constante** del bus no cruza C27 en régimen; un escalón sí produce corriente transitoria. Esto comprueba la topología de acoplamiento, no determina la frecuencia de corte: la corriente de base de Q29, la carga del ladder y la realimentación por Q30 dependen del punto de operación y de la señal. Tampoco están incluidos ESR, fuga ni tolerancias de los electrolíticos. Sus tolerancias de tabla son **+50/−10 %** para C27/C24; la referencia utiliza sólo los nominales.

La incertidumbre de R61 bloquea un parámetro DSP definitivo. Ya existen una [partición ideal condicionada de Q29/Q30](PAR_ENTRADA_FILTRO_IDEAL.md), el [cierre DC de TAIL](COLA_FILTRO_TAIL_Q29_Q30.md) y un [punto DC de BOTTOM y ambas bases](BASES_FILTRO_ACOPLADAS_DC.md) que realimenta sus corrientes para cada candidato de R61. Para llegar a audio se deben calcular la corriente desde los peldaños superiores, sus colectores y límites de región activa, el retorno de resonancia y el bus con sus cinco fuentes. La lectura de la tabla y del esquema permite **topología parcialmente modelada** y **transferencia pasiva condicionada**, no una afirmación de fidelidad del filtro.

```powershell
python tools/filter_input_reference.py
python -m unittest discover -s tests -q
```
