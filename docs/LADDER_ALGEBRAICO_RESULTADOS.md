# Ladder: reconstrucción local con cuatro memorias internas

## Cambio y alcance

El [kernel local](../crates/rf-d-circuit/src/ladder_algebraic.rs) implementa
la transformación de 16 nodos a siete variables algebraicas y nueve
coordenadas retenidas del [protocolo](LADDER_ALGEBRAICO_PROTOCOLO.md).
Resuelve las siete relaciones sin carga y devuelve todos los nodos,
reacciones, Jacobiano implícito de puertos y corrientes de fuentes fijas.
El [generador](../tools/prepare_ladder_algebraic.py) conserva las leyes
del stamp admitido, incluyendo beta finita y uniones BE/BC.

El inventario corrige una omisión del [plan anterior](LADDER_REDUCCION_ALGEBRAICA_PLAN.md):
el capacitor de bias de 220 µF también es memoria. Se conservan tres
voltajes diferenciales internos y V4; el cuarto capacitor de 68 nF sigue
entre los dos puertos de salida. No hay memoria congelada o descartada.
Las tres primeras reacciones y son conjugadas de voltajes diferenciales;
KCL suma sólo las otras seis más las fuentes fijas.

**Admisión local únicamente.** El motor y solver directos siguen activos,
con 118 estados. Este bloque no inserta todavía el kernel en la voz ni
mide reducción del costo; no es una nueva admisión de RT o fidelidad física.
La tarjeta es nominal CA3046, SVC-9 p.13/Fig.9-11, sin acceso a un Moog.

## Ensayo ejecutado

[Runner](../tools/check_ladder_algebraic.py), [probe](../tools/ladder_algebraic_local.rs)
y [recibo final](../evidence/ladder_algebraic_native03.json). Inputs: 24
ROOT ya admitidos, dos etapas por ROOT, perfiles directos 64/32 µs de
`hybrid_direct_native03.json`. No hay nueva trayectoria completa, librería,
input privado de sonido, WAV o árbol de build. Compilación directa con
rustc/rlib congelados; el ejecutable se retiró de `tmp/lab-current`.

| Comprobación nueva | Resultado | Gate / alcance |
| --- | --- | --- |
| 48 stamps locales frente al audio completo | Error 0 A / 0 S; cruces DC externos cero | 20 pA / 2 nS |
| Ida/vuelta HIGH/LOW | Error 0 V | 2 nV |
| 240 solves contrastados, semillas 0/±1/±10 mV | Máximo 6 iteraciones; error reconstruido 0,221229 nV | 2 nV |
| Residual/corrección local máximos | 0,136045 pA / 0,221229 nV | 1 pA / 2 nV |
| Reacciones frente al estado original | Error máximo 0,081831 pA | 20 pA |
| 72 columnas FD implícitas, 144 solves adicionales | Fracción máxima de gate: reacciones 0,000859; fuentes 0,000796 | 2 nS+2e-5·abs(FD) |
| Reconstrucción implícita FD | Fracción máxima 0,00000658 | 2e-5+2e-5·abs(FD), V/V |
| 128 columnas FD de TᵀJT | Fracción máxima 0,0000138 | Gate derivativo previo |
| Conservación con fuentes fijas | 0,041038 pA; 5,30e-18 S | 20 pA / 2 nS |
| Carga y masa de cinco capacitores locales | Error 0 A / 0 S; filas algebraicas sin carga | Mismas incidencias e historial |
| 48 comprobaciones de carga/masa del padre, incluido C10 | Ledger completo bit a bit; separación local error ≤5,30e-23 A / 0 S | 20 pA / 2 nS, sin duplicación |
| Rechazos con recuperación válida exacta | 148 de estado/h/presupuesto/factor + 30 de parámetros | Todos recuperan misma solución bit a bit |
| LU, LOW y h | 8 RHS con swap/fill; una cancelación sólo LOW; dos extremos h | Gates sin relajar |
| Heap del tramo comprobado | 0 asignaciones | Incluye kernel y comprobaciones numéricas |

Las 384 resoluciones contrastadas cuentan semillas y FD implícitas; no
incluyen las llamadas de control/retry. El instrumento de heap rodea cada
etapa de comprobación, después del parseo del input. La evidencia no mide
stack máximo, deadline o costo de la futura unión.

## Intentos y límites

El [primer intento](../evidence/ladder_algebraic_native01.json) conserva
un error de compilación y su replay sin modificar: el fixture LU no
declaraba la longitud del array esperado. Se corrigió sólo esa anotación;
el [segundo](../evidence/ladder_algebraic_native02.json) pasó. Después se
añadieron comprobaciones del padre, Jacobiano transformado y cancelación
LOW, preservando sus [fuentes previas](../evidence/ladder_algebraic_extensions_before01.json).
El tercer intento pasó; no se cambiaron gates o leyes para obtenerlo.

El [cierre](../evidence/ladder_algebraic_tests01.json) conserva por identidad
la admisión anterior y sus 255 tests Rust; esos tests y las trayectorias
globales no se ejecutaron de nuevo. Los checks locales anteriores sí son
nuevos. Precisión medida sólo en la rama nominal existente, no en arranque,
CV general, otras tarjetas o dispersión de componentes.

## Próximo paso concreto

Insertar las nueve coordenadas retenidas en el grafo de voz, con las siete
algebraicas reconstruidas por etapa. Transformar también las filas del
padre y las dos etapas de Radau, conservando el historial físico HIGH/LOW,
todos los acoplamientos y las filas compartidas TAIL/VCA_BASE. La dimensión
esperada sería 111 coordenadas por etapa; es una consecuencia algebraica,
no una reducción global ya ejecutada. Auditar nuevamente las ecuaciones
originales, eventos/rechazos, trayectoria y costo fresco antes de promover.
