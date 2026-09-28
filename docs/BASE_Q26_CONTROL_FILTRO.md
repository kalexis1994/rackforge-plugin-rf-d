# Base de Q26: control de corte y contorno

## Trazado y alcance

La **Fig. 9-17 de SVC-9, PDF p. 19** (SVC-204D p. 75) dibuja el potenciómetro de panel **R11 FILTER CUTOFF, 5 kΩ** entre −10 V y +10 V. Su cursor llega por **R55, 200 kΩ** al bus `FILTER CONT IN`. Ese bus entra por el **pin 5 CONTROL NODE** de la placa 4 y se conecta **directamente** a la base de Q26 en la **Fig. 9-11, PDF p. 13** (SVC-204D p. 69). En la placa, **R74, 47 kΩ** viene desde el **pin 16 AMT OF CONTOUR** y termina en esa misma base. No está en serie con el pin 5. La base también tiene **C18, 100 pF** a masa y **R49 SCALE, 500 Ω**, con el cursor unido al extremo de la base; el otro extremo llega a masa mediante **R70, 1,8 kΩ**. [Nodos y fuentes](../evidence/filter_cutoff_base_network.json).

El bus de panel recibe además J2 por R51 (100 kΩ), SW15 por R52 (33 kΩ) y SW16/SW17 por R53/R54 (300/150 kΩ). El [modelo del nodo pasivo](../tools/filter_cutoff_base_reference.py) acepta ramas de Thévenin `(voltaje, resistencia positiva)` y la corriente de base Q26 con signo positivo al salir del nodo. El [modelo de las llaves del panel](../tools/filter_cutoff_panel_reference.py) genera esas ramas para los estados trazados. Los voltajes y las impedancias **aguas arriba** siguen siendo fronteras de escenario. Para combinarlo con el [par Q26/Q28 ideal de β infinito](COLA_FILTRO_Q26_Q28.md), la corriente de base debe ser cero; el [modelo DC acoplado con β finito](COLA_FILTRO_ACOPLADA_DC.md) resuelve esa corriente bajo parámetros impuestos.

### Ramas y estados de la Fig. 9-17

| Entrada | Estado | Equivalente visto desde la base Q26 |
| --- | --- | --- |
| J2, R51 = 100 kΩ | Sin plug: contacto normal a masa | `0 V` por `100 kΩ` |
| J2, R51 | Plug conectado | `Vext` por `100 kΩ + Zext` |
| SW15, R52 = 33 kΩ | FILTER MOD OFF | `0 V` por `33 kΩ` |
| SW15, R52 | FILTER MOD ON | `Vmod` por `33 kΩ + Zmod` |
| SW16, R53 = 300 kΩ | FILTER KBD 1/3 OFF / ON | Rama abierta / `Vkbd` por R53 |
| SW17, R54 = 150 kΩ | FILTER KBD 2/3 OFF / ON | Rama abierta / `Vkbd` por R54 |

Los dos interruptores de teclado comparten **la misma línea de fuente**. Con ambos activados, la resistencia vista desde esa línea es `R53 || R54 = 100 kΩ`, en serie con su impedancia aguas arriba `Zkbd`; el modelo **no duplica** `Zkbd` como si hubiera dos fuentes independientes. Con sólo uno activado se usa su propia resistencia más `Zkbd`. Las impedancias `Zext`, `Zmod` y `Zkbd` son no negativas. Cero significa una fuente ideal **impuesta**, no una medición de impedancia cero en el instrumento. `Vext`, `Vmod` y `Vkbd` tampoco son formas de onda inferidas ni calibraciones de 1 V/octava.

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

Un ejemplo numérico del **nodo aislado** con `a=0,5`, `r=250 Ω`, `V16=0 V`, sin ramas adicionales e `Ib26=0 A` da `Vbase=0 V`, `Rknob=201,25 kΩ`, `Rscale=2,05 kΩ` y `τ≈0,194 µs`. El cálculo del **panel completo en reposo** añade obligatoriamente las cargas a masa de R51 y R52. Estos números sólo comprueban la ecuación reducida: `a`, `r`, `V16`, los rieles ideales y las fuentes son fronteras de escenario, no mediciones del Model D.

## Admisión RACE

La topología, resistencias nominales, estados de J2/SW15/SW16/SW17 y C18 están **trazados**; la transferencia pasiva está **calculada bajo fronteras impuestas**. El [punto DC de Q26/Q28 con β finito](COLA_FILTRO_ACOPLADA_DC.md) realimenta la corriente de base a este nodo, pero sus parámetros son impuestos. Los voltajes e impedancias reales de teclado/modulación/entrada externa, las tolerancias, la posición de SCALE, los rieles cargados y la frecuencia real del ladder siguen abiertos.

```powershell
python tools/filter_cutoff_base_reference.py
python tools/filter_cutoff_panel_reference.py
python -m unittest discover -s tests -q
```

Las regresiones comprueban el pin 5 directo y R74 desde pin 16 contra las dos transcripciones, el Thévenin cargado de R11, los estados OFF a masa, la conmutación de modulación, la combinación de las dos rutas de teclado con impedancia común, KCL, evolución de C18 y composición explícita con la carga condicional Q26/Q28. No son una validación sonora.
