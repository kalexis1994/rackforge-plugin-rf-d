# Biestable: incrementos y memoria compensada

## Contrato y procedencia

Laboratorio Python de 94 nodos, R61=200 Ω, BUS=0 V, KEY=10 V constante
durante cada intervalo. Conserva el grafo SVC-9 Fig.9-7/p.9 y los pasivos de
Figs.9-11/p.13, 9-8/p.10 y 9-17/p.19. Q25/Q15 usan los mismos parámetros
sintéticos de [carga conservativa](BJT_INTRINSECO_CARGA_CONSERVATIVA.md), con
TF=1 ns/TR=3 ns; las otras cargas de semiconductor siguen omitidas.

La versión nueva está en `tools/loudness_latch_increment_reference.py`.
Los helpers, gates y evidencias históricos permanecen intactos. No se
identifica una pieza vintage ni se admite audio o ejecución en tiempo real.

## Representación y ecuaciones

El desconocido Newton es δ relativo al estado aceptado: `v = hi + lo + δ`.
Los potenciales estáticos se evalúan con su suma redondeada a binary64.
Las diferencias capacitivas se calculan con `math.fsum` antes de multiplicar
por la conductancia. Para una rama lineal sin resistencia:

`I = (C/h) · fsum(vL_hi, vL_lo, δL, −vR_hi, −vR_lo, −δR, −Vc_hi, −Vc_lo)`.

Las unidades son V, F, s y A; no hay cambios de signo de KCL física.
El Jacobiano capacitivo se estampa analíticamente como `C/h`. C10 conserva
25,5 kΩ en serie: su conductancia equivalente es `1/(h/C + R)`, y la memoria
publicada satisface `Vc_new = Vc_old + h·I/C`. Los otros veinte capacitores
publican la diferencia compensada de sus terminales. Los nodos también
conservan `(hi,lo)`; se serializan ambos componentes de las 21 memorias.

`pair(terms)` calcula la suma redondeada y luego el residuo de esa suma.
El formato es `rf-d/compensated-state/v1`; la conversión explícita desde
el historial antiguo conserva todos sus valores con colas cero. Nunca se
inventa una cola del pasado. Los cuatro historiales QBE/QBC permanecen en
su representación anterior, calculados desde los potenciales redondeados.
Esta solución reduce el límite observado de los capacitores lineales;
no promete precisión arbitraria para todos los dispositivos.

Se mantienen `max|KCL| < 1e−11 A`, `max|corrección| < 1e−8 V`, 80 iteraciones
y 24 fracciones de búsqueda. Un rechazo no modifica el estado entrante.
La entrada antigua por coordenadas absolutas rechaza un estado compensado
para evitar descartar accidentalmente sus colas.

## Contraste del intervalo que falló

Informe: `evidence/loudness_latch_increment_probes.json`. Parte exactamente
del historial de la primera mitad registrada en el
[diagnóstico anterior](BIESTABLE_RECHAZO_Y_ORIGEN_CARGA.md), con h=47,68371582 ps.

- Jacobiano híbrido y FD completo convergen en dos iteraciones: KCL máxima
  **2,45938e−16 A** y corrección **2,47774e−15 V**.
- C2 queda `(0,8489549250860621 V, −5,246413962787076e−17 V)`.
  Descartar esa cola vuelve a incumplir KCL en la fila 92.
- El Jacobiano completo por FD difiere como máximo **2,15e−10** con escala
  elemento a elemento `|ΔJ|/(1+|J|)`; el gate previo a medir es 1e−8.
- Se conservan y verifican 32 pasos consecutivos adicionales con el mismo h.
- En un intervalo ordinario de 50 µs desde DC, la diferencia máxima respecto
  del solver anterior es **4,26326e−14 V**, inferior al gate de equivalencia
  de 1e−8 V. No cambia la rama por una política de selección.

La regresión comprueba las ecuaciones de rama y las corrientes de carga
publicadas mediante Decimal de 80 dígitos sobre los valores binarios
almacenados. Reevalúa KCL después del ciclo serializar/reconstruir, conserva
el snapshot previo y rechaza historiales truncados o de otro circuito.
Este contraste de aritmética es independiente del cálculo de diferencias
capacitivas; los modelos estáticos siguen siendo compartidos.

## Criterio adaptativo v2

`tools/loudness_latch_increment_time.py` compara el paso completo con dos
medios pasos sin publicar ninguno hasta aceptar ambos. Usa errores de
potenciales nodales y de las cuatro diferencias BE/BC:

`ratio = |Vfull − Vfine| / (Vabs + Vrel·max(|Vfull|, |Vfine|))`.

Las diferencias incluyen las colas compensadas. El criterio no depende del
origen convencional de Q; una regresión cambia ese origen ±1 nC y conserva
exactamente las razones. Q(V) es univaluada en este modelo restringido:
controlar sus argumentos es útil, pero no representa una cota demostrada
del error de carga o corriente. No equivale al criterio v1, cuyos rechazos
permanecen publicados.

Para el próximo barrido se fijan antes de ejecutar:

| Política | Vabs nodos y junturas | Vrel nodos y junturas | Δjuntura máxima por medio paso | (h/2)·λ+ máximo |
| --- | --- | --- | --- | --- |
| A2 | 100 µV | 1e−4 | 50 mV | 0,1 |
| B2 | 25 µV | 2,5e−5 | 25 mV | 0,05 |

Macro h máximo=100 µs, mínimo=1 ps, presupuesto=2000 intentos por política.
Las razones ≤1 permiten aceptar; crecimiento ×2 requiere razones <0,25 y
ambos otros límites por debajo de la mitad. λ+ sigue siendo un diagnóstico
del descriptor congelado, no estabilidad de toda la trayectoria.

## Reproducción y siguiente gate

`python tools/loudness_latch_increment_probes.py`

`python -m unittest discover -s tests -p test_loudness_latch_increment.py -v`

El siguiente gate es repetir 0..3 ms desde DC con A2/B2, comprobar cobertura,
conservación publicada y diferencias entre mallas. El cierre del intervalo
puntual no admite por sí solo refinamiento temporal ni conmutación física.
