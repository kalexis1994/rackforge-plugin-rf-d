# Base de Q26: control de corte y contorno

## Trazado y alcance

La **Fig. 9-17 de SVC-9, PDF p. 19** (SVC-204D p. 75) dibuja el potenciómetro de panel **R11 FILTER CUTOFF, 5 kΩ** entre −10 V y +10 V. Su cursor llega por **R55, 200 kΩ** al bus `FILTER CONT IN`. Ese bus entra por el **pin 5 CONTROL NODE** de la placa 4 y se conecta **directamente** a la base de Q26 en la **Fig. 9-11, PDF p. 13** (SVC-204D p. 69). En la placa, **R74, 47 kΩ** viene desde el **pin 16 AMT OF CONTOUR** y termina en esa misma base. No está en serie con el pin 5. La base también tiene **C18, 100 pF** a masa y **R49 SCALE, 500 Ω**, con el cursor unido al extremo de la base; el otro extremo llega a masa mediante **R70, 1,8 kΩ**. [Nodos y fuentes](../evidence/filter_cutoff_base_network.json).

El bus de panel recibe además J2 por R51 (100 kΩ), SW15 por R52 (33 kΩ) y SW16/SW17 por R53/R54 (300/150 kΩ). El [modelo ejecutable](../tools/filter_cutoff_base_reference.py) los acepta como ramas de Thévenin **impuestas** `(voltaje, resistencia positiva)` en el nodo de base. Cada voltaje debe corresponder al estado real de la llave y su fuente. Esta etapa no decide esos estados ni sustituye la impedancia de las fuentes por cero. También recibe la corriente de base de Q26 como frontera con signo positivo cuando sale del nodo. Para combinar con el [par Q26/Q28 ideal de β infinito](COLA_FILTRO_Q26_Q28.md), esa corriente debe ser cero.

## Reducción y ecuaciones

Sea `a` la **fracción eléctrica** del cursor R11 desde −10 V (`0≤a≤1`) y `r` la resistencia activa de R49 desde el lado de R70 hasta su cursor (`0≤r≤500 Ω`). Su posición mecánica o ley de giro no está documentada. Con rieles ideales nominales:

```text
V11 = −10 + 20a                                     V
R11,th = 5000a(1−a)                               Ω
Rknob = 200000 + R11,th                            Ω
Rscale = 1800 + r                                  Ω

G = 1/Rknob + 1/47000 + 1/Rscale + Σ(1/Rj)        S
J = V11/Rknob + V16/47000 + Σ(Vj/Rj) − Ib26       A
Vbase,DC = J/G                                     V

C18·dVbase/dt + G·Vbase − J = 0
τ = C18/G                                          s
Vbase(t+Δt) = Vbase,DC + [Vbase(t)−Vbase,DC]·exp(−Δt/τ)
```

Cada `Vj, Rj` es una rama adicional **impuesta** de panel; `V16` es el voltaje impuesto del pin 16 e `Ib26` es corriente de base firmada. La solución dinámica es exacta para voltajes, corriente y resistencias **constantes durante el intervalo**. El condensador no conduce en DC. El resultado es un voltaje de control candidato, no una ley de Hz por voltio ni una frecuencia de corte.

Un ejemplo numérico con `a=0,5`, `r=250 Ω`, `V16=0 V`, sin otras ramas e `Ib26=0 A` da `Vbase=0 V`, `Rknob=201,25 kΩ`, `Rscale=2,05 kΩ` y `τ≈0,194 µs`. Estos números sólo comprueban la ecuación reducida: la carga real de las otras ramas del panel y los parámetros del transistor no están incluidos. `a`, `r`, `V16`, los rieles ideales y las ramas son fronteras de escenario, no mediciones del Model D.

## Admisión RACE

La topología, resistencias nominales y C18 están **trazados**; la transferencia de este subcircuito pasivo está **calculada bajo fronteras impuestas**. El punto de operación transistor por transistor, el aporte completo de teclas/modulación/entrada externa, las tolerancias, la posición de SCALE, los rieles cargados y la frecuencia real del ladder siguen abiertos. En particular, el modelo Q26/Q28 de β infinito no calcula una corriente de base con la cual realimentar este nodo. El siguiente acoplamiento debe resolver esa corriente y las ramas del panel antes de convertir este voltaje en control musical.

```powershell
python tools/filter_cutoff_base_reference.py
python -m unittest discover -s tests -q
```

Las regresiones comprueban el pin 5 directo y R74 desde pin 16 contra las dos transcripciones, el Thévenin cargado de R11, KCL, signo de otras ramas y de `Ib26`, evolución de C18 y composición explícita con la carga condicional Q26/Q28. No son una validación sonora.
