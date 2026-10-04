# Presupuesto condicional del error entrante por nodo y celda

## Identidades y alcance

El [protocolo](BIESTABLE_PRESUPUESTO_ANCLAJE_PROTOCOLO.md), helper y productor
se fijaron en `0a56c1b` antes de medir; datos, suite y validador en `708ade2`
antes de validar. Se reutilizan las seis propagaciones balanceadas, métricas,
vectores de pico y mapas nodales, con sus SHA. Los dos rechazos de reset
permanecen explícitos. No cambian circuito, P, W, norma, anclaje o tasas.
No se resuelve otra inversa ni se calcula otro certificado de tasa.

Para cada celda k y fila nodal n se reconstruyen exactamente los pares
A_kn=sum_b gain_knb*peak_anchor_kb y
F_kn=direct_kn+sum_b gain_knb*peak_forced_kb.
Los máximos de A y F coinciden con los publicados en cada traza anterior.
Hay **752 pares por caso aceptado, 4.512 pares en total**, y tres escenarios
de reserva por caso: **18 presupuestos condicionales**.

Con el gate nominal racional T=1/1000 V, un error entrante ponderado
epsilon>=0 y una reserva nodal hipotética R satisfacen la familia de
majorantes si A_kn*epsilon+F_kn+R<=T para todas las filas.
La capacidad exacta de esta familia es el mínimo de (T-R-F_kn)/A_kn
en filas con A_kn>0. Se guardan todas las restricciones activas.
Coeficiente cero, igualdad en el gate, presupuesto no acotado e inviabilidad
con anclaje cero tienen estados explícitos y pruebas independientes.

Es un objetivo suficiente condicionado a estos majorantes. No es una
medición del error entrante, una cota necesaria del error físico ni una
afirmación de que sus superiores sean alcanzables simultáneamente.
La norma del anclaje es **infinito ponderado común**; su valor en µV no
debe confundirse con el error nodal sin pesos o con la tensión de audio.

## Todos los casos y reservas

R=0, 0,25 y 0,5 mV son escenarios fijados antes de medir. No se ha calculado
una cota del resto no lineal; R=0 tampoco afirma que éste sea nulo.
La reserva representa margen nodal adicional ya propagado hipotéticamente.
Acotar el resto del DAE y convertirlo a este margen sigue pendiente.

| Ventana | N | Anclaje máximo, R=0 (µV) | R=0,25 mV (µV) | R=0,5 mV (µV) | Restricción activa (celda/fila, base cero) |
| --- | --- | --- | --- | --- | --- |
| prefix | 2 | 0,568759094182 | 0,426569302421 | 0,284379510661 | 7 / 21 |
| prefix | 4 | 1,69622680120 | 1,27217008609 | 0,848113370992 | 7 / 21 |
| attack | 2 | 0,185297050491 | 0,138659241413 | 0,0920214323340 | 7 / 66 |
| attack | 4 | 0,714260594643 | 0,535663269107 | 0,357065943572 | 7 / 66 |
| reset | 2 | candidato rechazado | sin presupuesto | sin presupuesto | sin restricción nueva |
| reset | 4 | candidato rechazado | sin presupuesto | sin presupuesto | sin restricción nueva |
| tail | 2 | 1,69622682821 | 1,27217011312 | 0,848113398034 | 7 / 21 |
| tail | 4 | 2,92927337510 | 2,19695502356 | 1,46463667202 | 7 / 21 |

**Ataque N2 exige el objetivo más pequeño**, ~0,185 µV sin reserva y
~0,092 µV al reservar 0,5 mV. Esto cuantifica la amplificación del anclaje
que queda después de reducir el término forzado a ~6,72 µV. No se afirma
que el error entrante actual pase o falle esos objetivos: no está acotado.
Los índices de fila no son números de nodo eléctrico.

La capacidad pareada nunca empeora frente a (T-R-maxF)/maxA: es mayor en
**15/18 presupuestos** e idéntica en los tres de ataque N2. Sin reserva,
el objetivo separado de cola N4 es ~2,90021055538 µV y el pareado
~2,92927337510 µV. No se atribuyen los dos máximos independientes a la
misma fila. Esta mejora del objetivo no cambia la propagación ni la dinámica.

Todos los presupuestos son finitos y factibles para su familia afín.
En cada caso las reservas reducen monótonamente la capacidad. La última
celda limita todos los escenarios, con una sola fila activa. Esto describe
los majorantes seleccionados; no localiza necesariamente el máximo del
error real dentro de una trayectoria.

No se intersectan anclajes reales entre ventanas: son intervalos no
contiguos y hay métricas P distintas. Reset todavía requiere otra prueba,
y deben cubrirse las regiones restantes desde DC. **1 mV global sigue
abierto**, junto con el error inicial, resto no lineal, física, voz y deadline.

## Evidencia y regresiones

[Datos](../evidence/loudness_latch_bdf_static_precision_anchor_budget.json.gz):
**2726955 bytes**, SHA comprimido
`e82d6ec452f0aca0a12c75c1fccd9ee50f17f12ebdb34b3e94dca1a88e38d532`,
SHA canónico `201d24a0bd1c9a092abc33461d353d7a8682c5ab6bc97b489011f5298e599c47`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_anchor_budget_summary.json).
Se conservan todos los pares, soporte, pesos, SHA de propagación y presupuestos
racionales, con sus restricciones activas y comparación separada.

La [suite](../tests/test_loudness_latch_anchor_budget.py) pasa **5/5 al primer
intento**, 7.7524694 s. Usa familias afines con solución conocida, máximos
en filas distintas, ties, coeficientes cero, margen cero e inviabilidad.
Verifica monotonía y guards, productos racionales independientes de la
traza, los 4.512 pares y los 18 presupuestos. Cada capacidad satisface
todas las desigualdades; aumentarla viola una restricción activa.
Comprueba conversiones intactas, rechazos, fuentes, bytes y destinos.
El [recibo](../evidence/loudness_latch_bdf_static_precision_anchor_budget_validation.json)
guarda SHA antes/después idénticos. El [corpus](BIESTABLE_PRESUPUESTO_ANCLAJE_ENTRADAS.md)
recupera dependencias y versiones históricas.

Próximo bloque: inventariar intervalos entre DC y estas ventanas, anclajes
de entrada y conversiones entre métricas. Fijar cobertura y una estrategia
para reset antes de ampliar certificados; mantener el resto no lineal
separado del objetivo condicional que aquí se ha calculado.

```powershell
python tools/loudness_latch_bdf_static_precision_anchor_budget.py
python tools/validate_bdf_static_precision_anchor_budget.py
```
