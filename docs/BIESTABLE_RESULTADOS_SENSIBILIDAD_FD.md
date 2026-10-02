# Resultado de la sensibilidad FD de memoria

El [protocolo previo](BIESTABLE_SENSIBILIDAD_FD_DE_MEMORIA.md) fue fijado
junto al productor en `5bc54fd`. Se completan **40/40 matrices**:
cuatro ventanas, cinco pasos FD y dos rutas. Todas pasan el solve racional,
el residuo exacto antes de redondear y ambos gates algebraicos de 10⁻¹⁰.
El mayor error hacia atrás después de redondear es 1,89712×10⁻¹⁶.

## Comparación de mapas

Diferencia máxima `|X−Xmixto|/(1+|Xmixto|)` de la ruta FD del residuo completo.
El gate previo es **10⁻⁸**; las entradas en negrita pasan:

| Paso FD (V) | Prefijo | Ataque | Reset | Cola |
| --- | --- | --- | --- | --- |
| 10⁻⁴ | 2,49731×10⁻⁶ | 2,49747×10⁻⁶ | 2,49747×10⁻⁶ | 2,49708×10⁻⁶ |
| 10⁻⁵ | 7,10469×10⁻⁷ | 6,82251×10⁻⁷ | 6,61869×10⁻⁷ | 2,46852×10⁻⁸ |
| 10⁻⁶ | **8,66717×10⁻¹⁰** | **1,74284×10⁻⁹** | 1,34857×10⁻⁶ | **1,06786×10⁻⁹** |
| 10⁻⁷ | 7,01510×10⁻⁷ | 6,93423×10⁻⁷ | 1,34721×10⁻⁶ | 6,13754×10⁻⁷ |
| 10⁻⁸ | 7,53187×10⁻⁸ | 7,19746×10⁻⁷ | 6,99270×10⁻⁷ | 3,47618×10⁻⁷ |

La ruta con FD estático y derivadas dinámicas existentes también pasa sólo
prefijo/ataque/cola a ±1 µV: **6/40 comparaciones** en total, correspondientes
a tres ventanas repetidas bajo ambas rutas. No son seis casos independientes.
Ninguna de las diez matrices de reset pasa el gate. Sus máximos con
contribuciones separadas son 2,49747×10⁻⁶, 6,61869×10⁻⁷, 1,34852×10⁻⁶,
1,34725×10⁻⁶ y 6,99270×10⁻⁷, en el mismo orden de pasos.

Las cuatro matrices y mapas de la ruta completa a ±1 µV reproducen
**exactamente** los bytes numéricos del suplemento anterior. Su fallo de
reset no cambia. El barrido no elige un paso nuevo ni modifica el motor.

## Qué localiza y qué no

A ±1 µV en reset, el máximo sigue en nodo 27/memoria 10. Separar la carga
dinámica conserva una diferencia de magnitud similar. Eso no identifica
una causa única ni descarta contribuciones dinámicas menores; la segunda
ruta comparte sus derivadas de carga con el evaluador mixto.

La diferencia escalada de J en ese caso es 2,14586×10⁻¹⁰; el desacuerdo
escalado de X es 1,34857×10⁻⁶. La métrica de J usa una escala de 1 S en
su denominador y sólo es un diagnóstico, sin gate ni interpretación de
precisión física universal. Resolver JX=B con precisión algebraica no
elimina sensibilidad a cómo se aproximó J.

El máximo error relativo de la separación central real en nodos absolutos
llega a 9,48953×10⁻⁸ al pedir ±10 nV. En reset a ±1 µV es 7,48400×10⁻¹⁰;
en coordenadas de incremento es 8,40439×10⁻¹⁴. Estos registros localizan
redondeo de la perturbación; no prueban que explique todo el mapa. Tampoco
se observa convergencia monótona al reducir el paso. No se aplica Richardson
ni se escoge el menor desacuerdo como si fuese una derivada exacta.

## Evidencia y regresiones

- [Matrices completas](../evidence/loudness_latch_bdf_fd_sensitivity.json.gz):
  901.091 bytes, SHA256 comprimido
  `8f0fa6c2af78c2e5e1b3e4a31e834d0c44fb2cf5f4a5f645e6f4480951ff1e04`.
- [Resumen](../evidence/loudness_latch_bdf_fd_sensitivity_summary.json):
  máximos, columnas, error de coordenadas y gates de las 40 matrices.
- [Recibo de validación](../evidence/loudness_latch_bdf_fd_sensitivity_validation.json):
  **3/3 pruebas**, un intento exitoso, entradas sin cambios. Comprueba las
  cuatro matrices originales en bits, los 40 gates, diez eliminaciones
  racionales de reset reproducidas y la identidad canónica/comprimida.

`python tools/validate_bdf_fd_sensitivity.py`

El HEAD contextual de productor y validación es `5bc54fd`. El protocolo y
las fuentes se conservan por SHA; este documento de resultados es posterior
al cálculo y no forma parte de las entradas congeladas.

## Siguiente gate

Auditar por separado el residuo estático de la cadena de audio, sus nodos
y la precisión de sus diferencias antes de usar estos mapas como cota de
propagación. Contrastar las columnas señaladas con otra evaluación de
corrientes/derivadas y direcciones no lineales propias, declarando amplitudes
y precisión alcanzable antes de ejecutar. Después ampliar las ventanas.
La matriz completa de reset, el refinamiento global de 1 mV, los parámetros
físicos, audio y deadline permanecen abiertos.
