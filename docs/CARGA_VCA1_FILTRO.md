# Carga pasiva del primer VCA sobre el filtro

## Conexión y método

La [frontera R2/C6/R34/C15/R36](FRONTERA_ENTRADA_VCA1.md) procede de **SVC-204D §2.9, PDF p. 12**, **SVC-9 Fig. 9-11, PDF p. 13** y tabla 7-8, pp. 30–31. La Fig. 9-11 conecta el colector simple del recuperador Q5–Q8 a R2 `82 kΩ`, seguido por C6 `0,33 µF` hacia la base de Q16. R34 `820 Ω` une Q16_BASE y Q15_BASE; C15 `220 µF` y R36 `510 Ω` referencian la base de Q15 a masa. La [referencia de 27 nodos](../tools/filter_vca1_loaded_small_signal_reference.py) agrega tres tensiones a la [red de 24 nodos del ladder, recuperador y EMPHASIS](LAZO_EMPHASIS_PEQUENA_SENAL.md). R2/R34/R36 se estampan en siemens; C6/C15, en faradios. Se mantiene el retorno C10/R14/R73 a Q30, con el mismo ajuste de R73 en DC y AC.

El bus de mezcla es una fuente ideal de perturbación normalizada a 1 V. Las corrientes de base Q16/Q15, la red de balance y las demás etapas del VCA quedan abiertas. La solución incluye la **impedancia incremental del recuperador** en lugar de imponer un colector ideal; por eso R2/C6 afectan ligeramente el colector y el tap. El cociente `V_Q16/V_RECOVER_COLLECTOR` de la solución conjunta coincide con la [transferencia de tres nodos aislada](FRONTERA_ENTRADA_VCA1.md), como debe ocurrir para esa red pasiva lineal. Las pruebas verifican KCL en los 27 nodos y la igualdad de corriente entre R2 y C6.

## Contraste condicionado

Con `I_S=10⁻¹⁴ A`, β directo `100`, β inverso `5`, `298,15 K`, R73_L `500 Ω`, R14 eléctrico `0 Ω`, C10 `10 µF` y `100 Hz`:

| Candidato R61 | `|V_col/V_bus|`, C6 abierto | `|V_col/V_bus|`, VCA pasivo | `|V_Q16base/V_bus|` |
| ---: | ---: | ---: | ---: |
| `200 Ω` | 11,962 | 11,964 | 0,1183 |
| `200 kΩ` | 6,165 | 6,102 | 0,0603 |

Los cambios de colector son pequeños en este punto, pero no idénticos ni forzosamente del mismo signo: el lazo tiene fase y múltiples caminos. A `0 Hz`, C27/C6 bloquean la perturbación de BUS. Los residuos complejos de prueba son `<10⁻¹¹ A/V`. Estas son derivadas locales V/V; una magnitud de colector mayor que uno **no** significa que se puedan aplicar 1 V reales sin saturación. Ninguna cifra es nivel de jack, ganancia completa del VCA o medida de fidelidad.

## Límite de la frontera

El punto DC de Q16/Q15 y Q18 sigue abierto. Sus corrientes de base, el balance R14/R19/R23/R22/R13, la carga del segundo multiplicador Q14/Q13, la conversión Q12/Q17 y el volumen/salida podrían modificar la transferencia. La [referencia temporal no lineal](TRANSITORIO_FILTRO_ACOPLADO.md) tampoco contiene aún C6 ni el VCA; el siguiente trabajo debe resolver el sesgo activo y añadirlo al transitorio antes de inferir graves o recorte de la voz completa. La discrepancia documental de R61 continúa sin resolución física.

```powershell
python tools/filter_vca1_loaded_small_signal_reference.py
python -m unittest discover -s tests -q
```
