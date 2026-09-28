# Bases inferiores del filtro: BOTTOM, Q29/Q30 y TAIL en DC

## Circuito y alcance

La **Fig. 9-11 de SVC-9, PDF p. 13** (SVC-204D p. 69) une la base de Q29 a `BOTTOM` por **R54 = 470 Ω** y la base de Q30 por **R76 = 330 Ω** más el segmento de **R73 REGEN CAL** desde el lado de BOTTOM hasta su cursor (`0…1000 Ω`). El [grafo de entrada](../evidence/filter_input_board4.json) fija C27, C24 y el [conflicto documental de R61](ENTRADA_FILTRO.md): `200 Ω` en el esquema frente a `200 kΩ` en la lista de piezas 7-8, PDF p. 31. Ningún candidato se promueve como valor real.

En DC, C27 y C24 están abiertos. La **Fig. 9-17, SVC-9 PDF p. 19** (SVC-204D p. 75) muestra el extremo inferior de R14 sin conexión; C10 abre su cursor hacia el nodo de recuperación. Así, pin 6 y el extremo derecho de R73 no aportan corriente DC por esa ruta. La base de Q30 devuelve su corriente a `BOTTOM` por R73/R76. El [grafo de regeneración](../evidence/filter_regeneration_path.json) registra el terminal abierto. La corriente que llega a `BOTTOM` desde los peldaños superiores por R52 y el resto del ladder se recibe como **inyección impuesta** `I_L`, positiva al entrar al nodo; todavía no está calculada.

La [referencia ejecutable](../tools/filter_bottom_bias_dc_reference.py) acopla este retorno DC al [Q26/Q28 con β finito](COLA_FILTRO_ACOPLADA_DC.md) y al [par inferior](COLA_FILTRO_TAIL_Q29_Q30.md). Requiere un candidato explícito de R61, resistencia eléctrica de R73, `I_L` en A, `I_S29/I_S30` en A, β29/β30 adimensionales y las fronteras ya exigidas aguas arriba. Todos los voltajes están referidos a masa. Las fuentes ±10 V son ideales en estos escenarios.

## Ecuaciones reducidas

Con `I_T=I_C28`, `s=I_E29/I_T`, `R_B30=R76+R73_izq`, y `I_Bi=I_Ei/(βi+1)`:

```text
I_B29 = I_T·s/(β29+1)                             A
I_B30 = I_T·(1−s)/(β30+1)                         A
V_BOTTOM/R61 + I_B29 + I_B30 = I_L                A
V_B29 = V_BOTTOM − R54·I_B29                      V
V_B30 = V_BOTTOM − R_B30·I_B30                    V

ln[s/(1−s)] = ln{I_S29(1+1/β29)/[I_S30(1+1/β30)]}
             + (V_B29−V_B30)/V_T
```

La última ecuación y las caídas resistivas forman una raíz monótona en `0<s<1`; se resuelve por bisección. Después se calcula `V_BOTTOM=R61(I_L−I_B29−I_B30)`, ambas bases y `TAIL` mediante el [cierre exponencial previo](COLA_FILTRO_TAIL_Q29_Q30.md), basado en [TI SLOA059B, PDF p. 6, ec. (3)](https://www.ti.com/lit/an/sloa059b/sloa059b.pdf). Se devuelven residuos de KCL en las dos bases y BOTTOM, consistencia con las corrientes de base del par, y flags de margen de Q28 y de rieles nominales. Un flag de margen verdadero es **necesario**, no prueba región activa de Q29/Q30: faltan sus colectores.

Por ejemplo, con R39 a `0,1`, R11 al centro, R49 a `250 Ω`, `V16=0 V`, panel sin CV externa ni modulación/teclado, los cuatro `I_S=10⁻¹⁴ A`, los cuatro β `=100`, `T=298,15 K` y R73 a `500 Ω` desde BOTTOM, se obtienen estos escenarios matemáticos:

| R61 elegido | `I_L` impuesto | `V_BOTTOM` calculado | `V_TAIL` calculado |
| --- | ---: | ---: | ---: |
| 200 Ω | 5,5 mA | ≈1,1000 V | ≈0,5954 V |
| 200 kΩ | 5,5 µA | ≈1,0865 V | ≈0,5819 V |

Los dos dan un Q28 **candidato** activo, pero exigen inyecciones distintas por un factor de 1000. No se conoce la inyección real de los peldaños, así que estos resultados **no desambiguan R61**. Con la misma `I_L` impuesta, la diferencia de R61 cambia drásticamente el sesgo; el solver no recorta voltajes fuera de ±10 V ni rescata escenarios inválidos. La posición de R73 es resistencia eléctrica, no escala mecánica del ajuste.

## Límite RACE

Se ha cerrado un **subcircuito DC condicionado** de BOTTOM, ambas bases y `TAIL`. Faltan la corriente real desde R52 y la polarización de los colectores Q29/Q30 y peldaños superiores, las fuentes de panel reales, β e `I_S` de transistores instalados, efecto Early, saturación, tolerancias y transitorios con C27/C24/C10. La [referencia pasiva temporal de entrada](ENTRADA_FILTRO.md) sigue separada; una regresión confirma que reproduce este punto DC al imponer las corrientes acopladas. No se infiere curva de corte, resonancia ni sonido.

```powershell
python tools/filter_bottom_bias_dc_reference.py
python -m unittest discover -s tests -q
```

Las pruebas cubren ambos R61, tres KCL, reparto y realimentación de corrientes de base, límite β infinito, efecto del segmento de R73 y coincidencia con el límite DC de la red pasiva. El siguiente bloque debe obtener `I_L` de las ramas superiores y sus cargas de colector, conservando ambos candidatos de R61 hasta localizar evidencia de población independiente.
