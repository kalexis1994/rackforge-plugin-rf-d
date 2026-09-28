# Control de corriente del filtro: Q26/Q28

## Red documentada

La **Fig. 9-11, SVC-9 PDF p. 13** (SVC-204D p. 69) muestra el trimmer interno **R39 RANGE, 10 kΩ** entre +10 V y masa. Su cursor alimenta **R46, 68 kΩ**, cuyo otro extremo comparte el **emisor del PNP Q26** con la **base del NPN Q28**. La línea hacia Q28 cruza la de C27 sin punto de unión. La base de Q26 llega directamente al **pin 5 CONTROL NODE** y recibe el **pin 16 AMT OF CONTOUR** por R74; la [red pasiva de base](BASE_Q26_CONTROL_FILTRO.md) detalla R49/R70/C18 y el panel. El colector de Q26 va por **R45, 330 Ω**, a −10 V. Q28 tiene emisor a masa y colector conectado por **R60, 680 Ω**, al emisor común de [Q29/Q30](PAR_ENTRADA_FILTRO_IDEAL.md). La **tabla 7-8, SVC-9 PDF pp. 30–31** confirma los valores y cataloga Q26 como TIS93 (alternativa 2N3906), Q28 como TIS92 (alternativa 2N3904). [Transcripción de nodos](../evidence/filter_cutoff_q26_q28.json).

El [boletín B-804C, hoja 2](https://synthfool.com/docs/Moog/minimoog/factory_service_bulleting_804C2.jpg) corrige la nota de selección Q26/Q28 a `V_BE` emparejados dentro de **±3 mV a I_C=20 mA**. No fija su corriente de operación ni las corrientes de saturación `I_S`. R39 es un **ajuste de servicio**, no la perilla CUTOFF del panel. La referencia de Q26/Q28 recibe el voltaje de base como frontera; la [reducción pasiva R11→R55→pin 5 y pin 16→R74](BASE_Q26_CONTROL_FILTRO.md) ya puede calcular un candidato condicionado.

## Dos ecuaciones útiles y una carga DC condicionada

Si `α` es la **fracción eléctrica** de R39 desde masa al cursor (`0≤α≤1`), el potenciómetro con +10 V nominal y sus extremos de baja impedancia equivale, visto desde R46, a:

```text
V_RANGE_th = 10·α V
R_RANGE_th = 10000·α·(1−α) Ω
R_fuente = R46 + R_RANGE_th
```

En el nodo compartido de voltaje `V_X`, la [referencia ejecutable](../tools/filter_cutoff_pair_reference.py) desprecia ambas corrientes de base y usa la [ley bipolar ideal de TI, ec. (3)](https://www.ti.com/lit/an/sloa059b/sloa059b.pdf):

```text
(V_RANGE_th−V_X)/R_fuente = I_S26·exp[(V_X−V_B26)/V_T] = I_26
I_28 = I_S28·exp(V_X/V_T)
I_28/I_26 = (I_S28/I_S26)·exp(V_B26/V_T)
V_T = kT/q
```

La última razón cancela el nodo compartido, **sólo** bajo las hipótesis de transistores activos directos, misma temperatura, `β→∞` y ley exponencial ideal. `V_B26` está en V, `I_S26` e `I_S28` en A, `T` es temperatura de unión en K y `V_T` en V. Las [constantes SI exactas](https://physics.nist.gov/cuu/pdf/all.pdf) se comparten con la referencia del VCO. La ecuación de carga se resuelve por bisección; no ajusta una curva auditiva.

La referencia también calcula `V_C26 = −10 V + I_26·R45` y, para un `V_TAIL` impuesto, `V_C28 = V_TAIL − I_28·R60`. Comprueba como **candidatos** de región activa `V_C26 < V_B26 < V_X` y `0 < V_X < V_C28`. Si falla alguno, las corrientes exponenciales devueltas ya no son una solución física válida del transistor correspondiente. La tensión de TAIL tampoco sale de esta red aislada: depende del par Q29/Q30 y del ladder.

Por ejemplo, con `α=0,1`, `V_B26=0 V`, `I_S26=I_S28=10⁻¹⁴ A`, `T=298,15 K` y `V_TAIL=2 V` **todos impuestos**, salen `V_X≈0,523 V` e `I_26≈I_28≈6,92 µA`; ambas condiciones de región activa dan verdadero. **Ninguno de esos parámetros impuestos es una medición ni una calibración del Model D.** Cambiar `I_S`, el voltaje de base, la carga del ladder o el estado de R39 cambia la corriente. El criterio de ±3 mV del boletín a 20 mA no identifica `I_S26/I_S28` ni el comportamiento de baja corriente de un par concreto.

## Límite de admisión

El [modelo ideal de Q29/Q30](PAR_ENTRADA_FILTRO_IDEAL.md) ya puede recibir una corriente de cola **candidata** de esta red, pero todavía no hay un punto de operación acoplado: la red pasiva de base tiene ramas de panel y corriente de base impuestas; también faltan el voltaje `TAIL` por los dispositivos del ladder y el sesgo de los colectores. Quedan `β`, efecto Early, saturación, dispersión y temperatura real. La matriz de fidelidad conserva por tanto **transferencia condicionada**, sin frecuencia de corte ni resonancia inferidas.

```powershell
python tools/filter_cutoff_pair_reference.py
python -m unittest discover -s tests -q
```

Las pruebas comprueban el equivalente cargado de R39, KCL, razón exponencial y fallo de margen en el colector Q28. El próximo paso es resolver las ramas restantes del panel y el ladder inferior de forma simultánea.
