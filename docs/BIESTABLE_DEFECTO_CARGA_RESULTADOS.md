# Defecto de carga y publicación RC: testigos conocidos

El [protocolo](BIESTABLE_DEFECTO_CARGA_PROTOCOLO.md),
[leyes](../tools/loudness_latch_bdf_charge_defect.py) y
[productor](../tools/loudness_latch_bdf_static_precision_charge_defect.py)
quedaron congelados en **`fe5c437`**, el 2 de octubre de 2026, antes de medir.

## Resultados

| Contraste | Resultado |
| --- | --- |
| BDF2, grados 0..8, cuatro razones y dos escalas | 72/72 identidades racionales exactas y cotas polinómicas pasan |
| Arranque BE, grados 0..8 y dos escalas | 18/18 identidades racionales exactas |
| RC serie/directa, dos relojes, dos arranques | 512/512 pasos propios reproducen error forzado exactamente |
| QBE/QBC: Simpson 32 por tramo | 20/32 pasan; 12 fallos conservados, máximo gate 44,2399 |
| QBE/QBC: Simpson 64 por tramo | 30/32 pasan; dos fallos conservados, máximo 2,76768 |
| QBE/QBC: Simpson 128 por tramo | 32/32 pasan; máximo 0,173022 |
| QBE/QBC: Simpson 256 por tramo | 32/32 pasan; máximo 0,0108146 |

Los dos niveles finales eran el gate de cuadratura declarado; no se
eligen después de medir. Los 32 defectos y las cuadraturas finales
pasan Decimal80/100. No se añaden solves no lineales del circuito.

La masa del kernel BDF2 es **-h(h+k)/6**. Para Q=t³, el defecto de
corriente discreta menos exacta es **-h(h+k)**. Se anulan constantes,
lineales y cuadráticas. El kernel es no positivo; una cota requiere
supremo de |Q'''| en todo el historial, no un máximo de muestras.
En BE se anulan grados <=1 y la masa del kernel de Q'' es **-h/2**.

Para delta = exacto menos numérico, el residual de la referencia exacta
entra con signo positivo en la recurrencia forzada. En una rama RC serie,
**r=beta*tau** en KCL y **z=R*beta*tau** en la memoria de voltaje.
Los ocho testigos RC usan memoria numérica propia durante 64 pasos.
Omitir z conserva error no nulo en la rama serie pese a historia inicial
exacta; R=0 verifica r=tau y z=0. La excitación es manufacturada y no
representa una transición Model D validada.

Las cargas de juntura se evalúan sobre voltajes conocidos, sin atravesar
su knee. Su tercera derivada temporal incluye Q_v''', v', v'' y v'''.
No basta la tercera derivada respecto al voltaje. La suite contrasta
esa cadena mediante FD de la segunda derivada temporal, sin usar la
fórmula de Q''' en la evaluación desplazada. Parámetros siguen sintéticos.

## Evidencia

[Datos](../evidence/loudness_latch_bdf_static_precision_charge_defect.json.gz):
119.792 bytes; SHA comprimido
`bfb9da972848c00083048014320c12355efc0f3d073003818a92df11c162886c`;
SHA canónico
`cb63faca14182f03fbe1fdcd45dfcc53cf7876e434c94751e5adafc7caf73547`.
El [resumen](../evidence/loudness_latch_bdf_static_precision_charge_defect_summary.json)
identifica **158 entradas**, cada nivel y todos los fallos.
El [recibo](../evidence/loudness_latch_bdf_static_precision_charge_defect_validation.json)
conserva **6/6 pruebas**, primer intento, **1,8828773 s**, SHA antes/después
idénticos. La [suite](../tests/test_loudness_latch_bdf_static_precision_charge_defect.py)
verifica pesos independientes de Lagrange, kernels, signos, publicación,
historiales, cadena no lineal, dominios y almacenamiento.

```powershell
python tools/loudness_latch_bdf_static_precision_charge_defect.py
python tools/validate_bdf_static_precision_charge_defect.py
```

La identidad exacta de estos testigos no conoce Q''' de RF-D, ni deriva
su defecto exacto en una conmutación. El siguiente diagnóstico necesita
separar diferenciación temporal, reloj, coeficientes redondeados y error
de la reconstrucción de Q'. El gate global de **1 mV desde DC**, física,
audio y deadline siguen abiertos.
