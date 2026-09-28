# Panel y Q26/Q28: punto DC acoplado con β finito

## Evidencia y dominio

La placa 4 de **SVC-9, Fig. 9-11, PDF p. 13** (SVC-204D p. 69) fija las conexiones de Q26, Q28, R39/R46/R45/R60 y la base de Q26. La **Fig. 9-17, PDF p. 19** (SVC-204D p. 75) fija las ramas del panel hacia esa base. La [red pasiva con estados de panel](BASE_Q26_CONTROL_FILTRO.md) y la [referencia de par con β infinito](COLA_FILTRO_Q26_Q28.md) son los dos límites previos. La ley de colector exponencial proviene de [TI SLOA059B, PDF p. 6, ec. (3)](https://www.ti.com/lit/an/sloa059b/sloa059b.pdf); `β=I_C/|I_B|` es aquí un **parámetro de ganancia de corriente impuesto**, no un dato medido de los TIS93/TIS92 instalados. El boletín B-804C-2 especifica emparejamiento de `V_BE` a 20 mA, pero no fija `β`, `I_S` ni el punto de operación.

Este [solver DC ejecutable](../tools/filter_cutoff_coupled_dc_reference.py) conecta la corriente de base del PNP Q26 al nodo del pin 5 y la del NPN Q28 al nodo `SHARED`. Usa `I_S26`, `I_S28` en A, temperatura de **unión** en K y β26/β28 adimensionales mayores que 1. Acepta `V_TAIL` impuesto en V para comprobar margen, o **sin `V_TAIL`** cuando el [par inferior Q29/Q30](COLA_FILTRO_TAIL_Q29_Q30.md) lo determina. Admite `β=∞` para contrastar el límite anterior. Mantiene ideales las leyes exponenciales, las fuentes ±10 V y los contactos cerrados; C18 está abierto en DC. La revisión documental y sus valores de componentes no se mezclan con otra generación de Model D.

## Ecuaciones

Sea `V_B0` la base calculada sin corriente de transistor y `G_B` la conductancia total del panel, R74 y R49/R70, en S. En el PNP Q26, la corriente convencional de base **sale del transistor hacia el pin 5**; bajo la convención del nodo pasivo es negativa:

```text
I_B26,nodo = −I_C26/β26                         A
V_B26 = V_B0 + I_C26/(β26·G_B)                 V
V_X = V_B26 + V_T·ln(I_C26/I_S26)              V
I_C28 = I_S28·exp(V_X/V_T)                     A

(V_RANGE−V_X)/(R46+R39,th)
    = I_C26·(1+1/β26) + I_C28/β28              A

V_C26 = −10 + 330·I_C26                       V
V_C28 = V_TAIL − 680·I_C28                    V
```

R39 se reduce a `V_RANGE=10α V` y `R39,th=10000α(1−α) Ω` con fracción eléctrica `0≤α≤1` desde masa. La última KCL muestra dos cargas: corriente de emisor de Q26 y corriente de base de Q28. El solver halla `I_C26>0` por bisección monótona y devuelve residuos independientes de KCL del pin 5, KCL de `SHARED` y ley exponencial. Los criterios **candidatos** de región activa son `V_C26<V_B26<V_X` y `0<V_X<V_C28`; si fallan, las corrientes calculadas dejan de representar un transistor activo. Incluso si se cumplen, no se comprueban márgenes de saturación, efecto Early ni disipación.

La razón de **corrientes de colector** sigue obedeciendo

```text
I_C28/I_C26 = (I_S28/I_S26)·exp(V_B26/V_T)
```

si ambas leyes exponenciales comparten temperatura y región activa. La cancelación de `V_X` **no requiere β infinito**; β sí cambia `V_B26` y, por ello, la razón evaluada. Esta precisión corrige la condición demasiado fuerte de la referencia ideal previa.

Como comprobación numérica, con R39 a `α=0,1`, R11 al centro, R49 a `250 Ω`, J2 sin plug, modulación y teclado OFF, `V16=0 V`, `I_S26=I_S28=10⁻¹⁴ A`, `β26=β28=100`, `T=298,15 K` y `V_TAIL=2 V`, todos **impuestos**, se obtienen aproximadamente `V_B26=0,1225 mV`, `V_X=0,52262 V`, `I_C26=6,792 µA` e `I_C28=6,825 µA`. Ambas pruebas de margen dan verdadero. Son resultados del escenario, no valores del instrumento.

## Admisión RACE

Queda resuelto el **punto DC condicionado de estos dos nodos** con cargas de base finitas. El [cierre de `TAIL` con Q29/Q30](COLA_FILTRO_TAIL_Q29_Q30.md) añade bases y dispositivos inferiores impuestos; todavía no conoce la ganancia real ni `I_S` de cada transistor, su dependencia con temperatura y corriente, las impedancias y formas de onda de las fuentes aguas arriba, la posición calibrada de RANGE/SCALE ni las cargas de colector del ladder. Tampoco se resolvió C18 durante transitorios con corriente de base no lineal. Por tanto, no se deriva frecuencia de corte, tracking ni fidelidad sonora.

```powershell
python tools/filter_cutoff_coupled_dc_reference.py
python -m unittest discover -s tests -q
```

Las pruebas verifican signo de corriente del PNP, dos KCL, ley exponencial, composición con panel, recuperación del límite β infinito, razón de colectores con β finito, rechazo de fronteras inválidas y fallo de margen del colector Q28. El siguiente bloque debe cerrar las bases y cargas de colector del peldaño inferior; después puede estudiarse la dinámica no lineal de C18.
