# Núcleo activo DC del primer VCA

## Lectura de circuito y fronteras

La **Fig. 9-11 de SVC-9, PDF p. 13** (manual SVC-204D completo p. 69) muestra Q16/Q15 como par diferencial TIS97, con emisor común por R35 a Q18. Su tabla 7-8, **PDF pp. 30–31**, da R35 `1 kΩ`, R34 `820 Ω`, R36 `510 Ω`, R37 `6,8 kΩ`, R43 `270 kΩ` y R59 `68 kΩ`. Q18 recibe la señal de contorno por R59; su emisor va a masa por R37 y a −10 V por R43. **SVC-204D §2.9, PDF p. 12** describe la primera multiplicación controlada por Q18, seguida por otra controlada desde EXTERNAL LOUDNESS. No se conoce aún la ley del contorno.

La misma Fig. 9-11 lleva el colector de Q16 por R19 `100 Ω` al extremo izquierdo de **R14 de placa 4, `25 Ω` (`1ST VCA BAL`) y el de Q15 por R23 `100 Ω` al derecho. El cursor llega por R22 `120 Ω` a **Q15_BASE**. La pista se representa mediante dos segmentos que suman `25 Ω`; el cursor se expresa en ohmios eléctricos, porque su posición mecánica no está calibrada. Este R14 es distinto del R14 de panel `50 kΩ` de EMPHASIS. C6 y C15 se abren para DC; la [frontera pasiva anterior](FRONTERA_ENTRADA_VCA1.md) permanece como referencia aislada AC.

El [grafo](../evidence/vca1_active_core.json) registra esas conexiones. El [solver DC](../tools/vca1_active_core_dc_reference.py) impone el voltaje del cursor R14 y el voltaje **más allá de R59**. El primer voltaje representa la red aún no cerrada R13/R11/R10, segundo VCA y riel positivo. La [extensión de nueve nodos](ALIMENTACION_BALANCE_VCA1.md) ya calcula el primer cursor a través de R13 con el **segundo** cursor impuesto. Las bases de Q14/Q13, conectadas a los colectores Q16/Q15, absorben corriente cero en ambos cortes. Por ello todavía no se predice el sesgo real de una placa completa.

## Ecuaciones y dominio

Cada transistor usa las dos junturas de la [referencia Ebers–Moll del ladder](LADDER_EBERS_MOLL_DC.md): `I_F=I_S·expm1(V_BE/V_T)`, `I_R=I_S·expm1(V_BC/V_T)`, `I_B=I_F/β_F+I_R/β_R`, `I_C=I_F−I_R−I_R/β_R`, `I_E=I_B+I_C`. `V_T=kT/q`; los tres `I_S`, `β_F` y `β_R` son parámetros **impuestos**, no fichas medidas de TIS97. La ley incluye conducción de la juntura base colector; no incluye almacenamiento de carga, capacitancias, resistencia de expansión, alta inyección ni dispersión térmica. La KCL usa amperios y las tensiones son absolutas respecto de masa:

```text
Q16_BASE:      (V15b−V16b)/R34 − IB16 = 0
Q15_BASE:      (Vw−V15b)/R22 + (V16b−V15b)/R34 − V15b/R36 − IB15 = 0
PAIR_EMITTER:  IE16 + IE15 − (Ve−V18c)/R35 = 0
Q18_COLLECTOR: (Ve−V18c)/R35 − IC18 = 0
Q18_EMITTER:   IE18 − V18e/R37 − (V18e+10)/R43 = 0
Q16_COLLECTOR: (Vw−V16c)/(R19+R14izq) − IC16 = 0
Q15_COLLECTOR: (Vw−V15c)/(R23+25−R14izq) − IC15 = 0
Q18_BASE:      (Vcontorno−V18b)/R59 − IB18 = 0
```

La eliminación de los terminales extremos de R14 en las dos KCL de colector es exacta **dado el cursor ideal impuesto**. El sistema resuelve ocho nodos y devuelve residuos y conductancia diferencial local de 8×8 en siemens. Newton con búsqueda amortiguada evita dar por válido un punto que no cierre corriente. No se usa en tiempo real.

## Comprobaciones condicionadas

Con `Vw=5 V`, `Vcontorno=2 V`, `R14izq=12,5 Ω`, riel −10 V, `I_S=10⁻¹⁴ A`, `β_F=100`, `β_R=5` y `T=298,15 K`, el cálculo da `I_C18≈221,38 µA`, `I_C16≈107,71 µA`, `I_C15≈111,48 µA`; el residuo de las ocho KCL es `<10⁻¹² A`. Los colectores Q16/Q15 quedan en `≈4,9879/4,9875 V`. Es un **escenario de verificación numérica**, no una calibración de Model D. A `Vcontorno=0 V` el mismo modelo deja `I_C18≈0,14 nA`; de 0 a 3 V la corriente crece monótonamente para esa frontera. Con `Vw=3 V`, `Vcontorno=2 V`, Q18 presenta `V_BC>0`, y se conserva ese estado en vez de forzar región activa directa.

Las [regresiones](../tests/test_vca1_active_core_dc_reference.py) comprueban las ocho KCL, conservación de la corriente de cola, límite casi apagado, redistribución por el balance y una juntura base colector directa. No verifican la forma de onda ni la semejanza sonora. El próximo cierre debe resolver la red de alimentación/balance y las bases Q14/Q13; después se puede sustituir la frontera de corrientes de base cero en la [red cargada de 27 nodos](CARGA_VCA1_FILTRO.md).

```powershell
python tools/vca1_active_core_dc_reference.py
python -m unittest discover -s tests -q
```
