# Contorno de filtro: seguidor y puerto cargado

2026-10-14. Perfil documental Model D clásico CA3046; sin unidad física.
[Protocolo y derivación](CONTORNO_FILTRO_PUERTO_PROTOCOLO.md),
[grafo](../evidence/filter_contour_port_graph01.json) y
[revisión visual](../evidence/filter_contour_port_review01.json).

## Función cerrada

Q22 NPN/Q21 PNP forman un par complementario con realimentación: emisor
Q22 y colector Q21 comparten OUT. R17 Amount de 50 kΩ carga esa salida;
su cursor llega por R74 de 47 kΩ a Q26. El puerto incluye Q26 PNP/Q28 NPN,
el panel restante y C18. Tiene nueve nodos y ocho terminales con corrientes
y tangentes, incluidos masa, alimentación y retorno de reset. R74 aparece
una sola vez; la antigua fuente ideal V16 se sustituye por el cursor cargado.

La reducción elimina únicamente el cursor resistivo. Los topes se unen
exactamente, conservando la carga de R17 y R74. El oráculo monta las ramas
originales con diez nodos en posiciones interiores y nueve en los topes;
Newton y derivadas se calculan por diferencias finitas, sin importar el
stamp, el Jacobiano analítico ni el solver nativos.

Las cargas C11/C18 conservan su historia durante Newton. `provisional`
entrega una respuesta sin publicar; `step` publica sólo al converger.
El estado vincula la variante C11: no permite cambiar 0↔47 pF en vuelo.
Cada variante inicia con su propio DC. C18 es siempre 100 pF.

## Observación funcional DC

Reset 0,01 V, cutoff 0,5, RANGE 0,1, escala 250 Ω y TAIL impuesto a 1,4 V.
La corriente tabulada entra desde TAIL hacia R60/Q28; no representa Hz.
Son hipótesis nominales de Ebers–Moll, no mediciones de un instrumento.

| C5 impuesto | Amount 0: TAIL µA | Amount 0,5: TAIL µA | Amount 1: TAIL µA |
|---|---:|---:|---:|
| 0,85 V | 6,824899 | 8,236628 | 10,926338 |
| 3 V | 6,824899 | 26,738357 | 164,727848 |
| 6 V | 6,824899 | 119,632033 | 516,631516 |

Con Amount cero C5 deja de controlar Q26, pero R17 continúa cargando OUT.
Con Amount activo la corriente cambia de forma no lineal. Para C5=3 V,
OUT cambia de 2,480168 V a 2,478053 V entre Amount 0/1: el generador siente
la carga del control.

## Cobertura admitida

[Banco final native05](../evidence/filter_contour_port_native05.json):
60 DC, 96 pasos en cuatro trayectorias locales de 128 µs, máximos de paso
8/4 µs y C11 ausente/47 pF. Excitación local C5 0,85→0,851→0,85 V,
eventos en 32/96 µs con clocks enteros. 32 observaciones comunes entre
resoluciones, contrastando todos los nueve nodos y ocho puertos.

| Comprobación | Resultado máximo | Gate |
|---|---:|---:|
| Raíz nativa/original | 7,758 nV | 1 µV |
| Corrientes nativa/original | 6,300 pA | 1 nA |
| KCL original | 0,692 pA | 1 pA |
| KCL nativo dinámico | 4,984 pA | 10 pA |
| Corrección nativa dinámica | 7,389 nV | 10 nV |
| Refinamiento local: nodos | 0,311092 µV | 2 µV |
| Refinamiento local: puertos | 0,094695 nA | 2 nA |
| ΔQ independiente | 7,389×10⁻¹⁹ C | 20 pA·dt |
| KCL más retornos | 2,741×10⁻¹⁹ A | 20 pA |

Se evalúan 1520 filas originales: 560 DC y 960 dinámicas. Las 45084
entradas FD del stamp incluyen nodos, puertos y ambos cruces en DC y cada
paso. Las 9984 tangentes cargadas se contrastan re-resolviendo la red
original ante cada perturbación. Gates 2 nS + 2×10⁻⁵·|referencia|;
fracciones máximas 0,000091618 y 0,011314, respectivamente.

96 pasos repetidos conservan estado completo, corrientes y tangentes por
bits. Las 96 llamadas provisionales no publican. 24 rechazos preservan
estado: parámetros, historia, dt, budget, overflow y cambio de variante.
Sin Cargo, dependencias, nueva biblioteca o SPICE. El llamador de laboratorio
compila el módulo nuevo junto con la biblioteca assembly congelada. El módulo
queda fuera de `lib.rs` y de la voz hasta cerrar su dominio de integración.

## Estrés rechazado y alcance pendiente

[native01](../evidence/filter_contour_port_native01.json) conserva el error
E0689 y su compilación repetida sin cambios; se explicitó f64 en la grilla.
[native02](../evidence/filter_contour_port_native02.json) conserva el salto
impuesto C5 0,85→3 V. Sus raíces, corrientes, cargas y tangentes pasan,
pero el refinamiento falla: 668,677 µV y 622,610 nA. La repetición del
auditor reproduce el fallo. Ese recorrido sigue rechazado; la admisión
local no sustituye el gate original ni certifica gran señal.

native03 separa el banco local; native04 amplía su Jacobiano dinámico;
native05 vincula C11 al estado. Fuentes de los intentos fallidos y datos
privados permanecen identificados. No se rebajaron tolerancias ni se ajustaron
componentes para hacer pasar el estrés.

C5, base Q4, alimentación 9,3 V y TAIL siguen impuestos. Quedan pendientes
temporizador, biestable, gatillo compartido, C12 opcional de 500 pF y respuesta
conjunta del ladder. El paso próximo es cerrar C5 con su corriente de entrada,
para obtener ataque/decay continuos y medir su refinamiento antes de conectar
la voz. Sin audio nuevo, contorno completo, calibración vintage, fidelidad
física, medición de heap/deadline o admisión RT.

[QA global](../evidence/filter_contour_port_tests01.json) conserva todas las
fuentes y entradas previas, biblioteca, historias y WAV anteriores por identidad.
