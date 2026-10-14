# Reducción exacta del puerto R6/R45 de OSC1

Objetivo nominal SVC-9 pp.5/19, variante SW6 de sierra, OSC1 ON,
R6=25 kΩ y R45=33 kΩ según el grafo admitido. α es la fracción del
cursor desde masa, dominio [0,1]; no modifica frecuencia ni forma de onda.
Tres terminales: sierra, masa física y BUS. Voltajes de laboratorio ±40 V.
Las resistencias se heredan como hipótesis nominales, sin ajuste a hardware.

## Derivación

Rsuperior=R6(1−α), Rinferior=R6α. Eliminar sólo el cursor resistivo:

`E = Vmasa + α(Vsierra−Vmasa)`

`R = R45 + R6α(1−α)`

`Iout = (E−VBUS)/R`

`Isierra = (Vsierra−Vmasa)/R6 + α Iout`

`Imasa = −(Vsierra−Vmasa)/R6 + (1−α) Iout`

`IBUS = −Iout`

Se conserva la carga de 25 kΩ sobre la sierra y la reacción del BUS
sobre ese terminal. Para α=0/1, el cursor es un contacto exacto; R≥33 kΩ,
sin divisiones por un tramo nulo. Jacobiano completo de los tres puertos,
suma de corrientes cero y disipación `(Vsierra−Vmasa)²/R6 + R Iout²`.
Red puramente resistiva: no se elimina ninguna memoria física.

## Gates previos

Oráculo independiente monta los dos tramos y R45, resuelve el cursor y
sus tres corrientes. Barrer α=0,1 y ocho posiciones interiores, fuentes
y BUS de signos opuestos y movimientos comunes. Error I ≤2 fA + 2e−12|I|,
cursor ≤2 pV + 2e−12|V|, Jacobiano ≤2e−16 S + 2e−12|Y|.
Derivadas por FD ±1 µV: ≤2e−12 S + 2e−7|Y|. Suma I ≤2 fA;
potencia terminal/disipada ≤2 fW + 2e−12|P|.

Contrastar además ambos historiales de 100 ms admitidos: corriente R45
desde los nodos BUS12/cursor39 y sierra46, α=.5; cursor y KCL del puerto
en 1602 estados incluyendo DC. No se reajusta el nivel ni la fase.
Rechazar α/voltajes no finitos y entradas fuera del dominio.

El kernel es un módulo de laboratorio sin exportación de plugin. El VCO
completo conserva su reacción a cargas; reemplazar su sierra por un
generador de fase necesitará contraste propio de forma, frecuencia y
dependencia de carga. Este bloque entrega el puerto para esa reducción.
Ejecutable/exports temporales en un único `tmp/lab-current`; retirar al
terminar, guardando métricas y fuentes de un eventual fallo acotado.
