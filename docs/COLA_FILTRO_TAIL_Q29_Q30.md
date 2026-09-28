# TAIL del filtro: cierre DC condicional de Q29/Q30 con Q28

## Evidencia y fronteras

En **SVC-9, Fig. 9-11, PDF p. 13** (SVC-204D p. 69), Q29/Q30 son el par inferior **TIS97 NPN** con emisores unidos en `TAIL`. Ese nodo baja por **R60 = 680 Ω** al colector de Q28; Q29 recibe la [entrada tras C27](ENTRADA_FILTRO.md) y Q30 el [retorno de regeneración](REGENERACION_FILTRO.md). La tabla 7-8 de SVC-9, PDF pp. 30–31, confirma designadores y valores. [Grafo](../evidence/filter_input_pair.json). La ley exponencial de colector empleada es la de [TI SLOA059B, PDF p. 6, ec. (3)](https://www.ti.com/lit/an/sloa059b/sloa059b.pdf).

La [referencia ejecutable](../tools/filter_bottom_tail_dc_reference.py) obtiene la corriente de colector candidata de Q28 desde el [panel y Q26/Q28 acoplados](COLA_FILTRO_ACOPLADA_DC.md), **sin imponer `TAIL`**. Exige como fronteras los dos voltajes de base Q29/Q30 en V, sus `I_S` en A y sus β adimensionales mayores que 1; acepta β infinito para contrastar el límite anterior. Emplea la misma temperatura de unión impuesta al bloque Q26/Q28. C27/C24 se abren en DC. Ningún voltaje de base, β, `I_S` ni corriente del ejemplo procede de una unidad física.

## Cierre de corriente y margen

Sean `V_E=V_TAIL`, `I_28` la corriente de colector calculada de Q28 y `V_T=kT/q`:

```text
I_C29 = I_S29·exp[(V_B29−V_E)/V_T]                 A
I_C30 = I_S30·exp[(V_B30−V_E)/V_T]                 A
I_E29 = I_C29·(1+1/β29)                           A
I_E30 = I_C30·(1+1/β30)                           A

I_E29 + I_E30 = I_28                              A
V_E = V_T·ln{[I_S29(1+1/β29)e^(V_B29/V_T)
             +I_S30(1+1/β30)e^(V_B30/V_T)]/I_28}  V

V_C28 = V_E − 680·I_28                             V
```

El logaritmo de suma se evalúa de forma estable para diferencias grandes de bases. El solver devuelve ambas corrientes de colector, emisor y base, residuos de KCL en `TAIL` y caída en R60. El criterio candidato de Q28 activo directo es `0<V_B28=V_SHARED<V_C28`. Si falla, `I_28` y el `TAIL` calculado dejan de representar ese circuito con Q28 activo. También se comprueba que cada unión base emisor inferior esté polarizada directa; **no se conocen los voltajes de colector Q29/Q30**, así que su región activa completa no puede certificarse todavía.

Como escenario ilustrativo se imponen R39 a `0,1`, R11 al centro, R49 a `250 Ω`, panel sin CV externa ni modulación/teclado, `V16=0 V`, `I_S26=I_S28=I_S29=I_S30=10⁻¹⁴ A`, β26/28/29/30 `=100` y `T=298,15 K`. Si `V_B29=V_B30=1,1 V`, resultan `I_28≈6,825 µA`, `V_TAIL≈0,59545 V`, `V_C28≈0,59080 V` y ambas ramas inferiores reciben `≈3,412 µA` de emisor; Q28 conserva margen. Con **las mismas hipótesis** pero bases inferiores a `0,9 V`, `V_C28` cae por debajo de `V_SHARED` y el modelo señala Q28 fuera de su región admitida. **Estos voltajes de base son ensayos matemáticos, no puntos DC identificados del Model D.**

## Admisión RACE

El cierre de `TAIL` es una **transferencia DC condicionada** de cuatro transistores y R60, no un punto de operación del ladder completo. Siguen abiertos los voltajes de colector y cargas de Q29/Q30, la corriente de base de Q29 sobre R54/C27 y la de Q30 sobre R73/C10, el valor conflictivo de R61, los voltajes e impedancias de las fuentes del panel, dispersión, efecto Early, saturación y temperatura efectiva. Los flags de región activa son condiciones necesarias; no sustituyen un modelo de saturación. No se infiere frecuencia de corte, resonancia ni fidelidad audible.

```powershell
python tools/filter_bottom_tail_dc_reference.py
python -m unittest discover -s tests -q
```

Las pruebas comprueban KCL de emisor y R60, relación entre corrientes de base/colector/emisor, simetría, recuperación del reparto ideal de β infinito, estabilidad con bases muy distintas, cambio de margen Q28 al variar bases y rechazo de fronteras inválidas. El próximo paso es resolver las bases inferiores con R54/R61 y R73 bajo cargas del ladder, conservando los dos candidatos de R61 hasta contar con evidencia discriminante.
