# VCO1: ensamblaje nativo completo, protocolo previo

2026-10-07. CA3046 nominal, SVC-9 Fig.9-3 p.5 y panel Fig.9-17 p.19.
Se conserva el [grafo](../evidence/vco1_ramp_graph.json), sus controles,
[panel](../evidence/vco1_panel_pulse_width.json) y
[tarjetas](../evidence/vco1_laboratory_devices.json). Semiconductores
condicionados a TEMP=TNOM=25 °C; no hay Moog físico de referencia.

## Alcance y ecuaciones

100 elementos exteriores, dos 741 originales de 41 elementos cada uno.
56 nodos de placa y 42 internos: 98 voltajes, 11 fuentes exteriores,
22 ramas internas y tres corrientes de trims: 134 incógnitas.
Cada trim mantiene V(a)-V(b)-R I=0, también con R=0 exacta. No epsilon R.
R8 0..1 y R11 0..1000 ohm; seis CV eléctricos y bus dentro de ±40 V,
carga exterior NEG4 dentro de ±1 A. Frontera fija SW6 3/10, R6 alpha=.5,
ON y bus impuesto. Esta versión posee R6/R45; no conectar el nuevo mixer
que también los posea sin transferir su propiedad primero.

Conserva convertidor, C1, ambos E402 en fuente común, Schmitt Q5/Q6/reset
Q10, tres waveformers, panel y NEG4 por R166/R174/C14. C4 10/100 pF
son perfiles separados. Todos los elementos llevan nombres, terminales,
valores y procedencia regenerables; no se inventan umbrales/timers/reset.

Reutiliza sin cambios BJT/JFET y el stamp completo 741 de 37 filas.
Las cinco filas de sus pines se suman a los nodos compartidos, incluidas
alimentaciones y masa de IC1. Historia aceptada por identidad de nodo:
seis capacitores exteriores, seis de 741, cuatro corrientes de inductores,
28 cargas BE/BC y cuatro GS/GD. No se duplica una carga ni se intercambia
GS/GD al invertir canal. Euler 125 ns..1 ms, historia fija durante cada
linealización. Candidato provisional, jamás publicación parcial.

## Gates fijados antes del banco

Referencia ajena a Rust: netlist anterior más incidencias Decimal100 de
las tres primitivas ya admitidas. Todos los residuos y las 134×134
entradas, incluidas cero, deben contrastarse. Diferencia por entrada:
KCL 2e-11 A + 3e-11 relativa; restricciones 2e-10 V + 3e-11 relativa;
Jacobiano 2e-10 en sus unidades + 3e-11 relativa. Conservación de suma de
98 KCL más retorno a masa: 1e-11 A. FD central de las 134 columnas:
2e-6 absoluto + 2e-5 relativa, perturbación 1e-7 V o 1e-10 A.

Dos circuitos ngspice originales, C4 10 y 100 pF, DC y transitorio
completos de 200 us. Exportar todas las incógnitas, sin parámetros nativos
como semillas. DC: KCL <1e-11 A y restricciones <1e-11 V, según contrato
[VCO1 previo](VCO1_NATIVO_PROTOCOLO.md). Snapshots transitorios sólo
excitan stamps; no son trayectoria nativa ni admiten oscilación nativa.

Contrastar dt125/250/500 ns, historia igual y distinta, DC, endpoints
R8/R11, repetición pura, memoria candidata, dominio y todos los puertos.
1000 stamps completos sin heap en test aislado; no acredita deadline.
Preservar fallos, copia/hash del export original antes de replay idéntico.
Sources/docs binarios privados con hashes antes/después. No nueva escucha.

## Siguiente admisión

Newton conjunto con arranque propio, trayectoria autónoma, refinamiento,
calibración reservada y carga activa del mixer tienen gates posteriores.
Este banco admite el ensamblaje, no esas trayectorias ni fidelidad física.

## Ajuste de alcance antes del segundo banco

El intento reference01 y su replay idéntico rechazan el punto DC libre:
ngspice informa fallo del operating point y no exporta. Se conserva ese
rechazo; no se admite DC libre ni se relaja su gate. El banco reference02
separa por perfil un DC de arranque con fuente explícita Vstartup que
impone C1=0 y un transitorio con la .ic original, sin Vstartup. La KCL
de RAMP_C1 incluye la corriente medida de esa fuente y su retorno a masa.
El gate sigue siendo 1e-11 A/V para todas las filas de ese circuito.
Son cuatro procesos, dos fronteras distintas y documentadas. Ningún
snapshot condicionado se usa como mecanismo de arranque nativo.

Reference02 y replay conservan DC condicionado con residual máximo
1.1652e-11 A: no pasa el gate 1e-11. Antes de reference03 se endurecen
sólo los criterios del solver SPICE a reltol=1e-10, abstol=1e-15 A y
vntol=1e-12 V. Tarjetas, fuentes, conexiones y gates permanecen idénticos.

Reference03 pasa el DC condicionado estricto; su transitorio estricto y
replay abortan a 5 ns. Se retienen ambos exports, con copia previa al
replay. Reference04 conserva esos criterios estrictos sólo para DC;
los snapshots transitorios usan las tolerancias originales del oráculo.
La trayectoria SPICE deberá completar 200 us, pero sólo excita el stamp,
no se contrasta contra una supuesta trayectoria nativa de Euler.

Reference04 completa C4=10 pF, pero rechaza y reproduce el DC de arranque
con trims calibrados y CV=-1.1 V. Ese alcance queda pendiente. Reference05
usa los mismos CV/trims nominales para ambos C4, aislando la discrepancia
10/100 pF; no declara cobertura del arranque calibrado rechazado.

Reference05 completa los cuatro procesos; el adaptador de inventario
rechaza endpoints porque el netlist cambia el designador R a V. El fallo
se conserva, antes de corregir sólo ese mapeo. Reference06 representa
ambos designadores por la misma fila aumentada V-R I=0 y excluye esos
contactos del contador de fuentes exteriores. El nativo no cambia.
