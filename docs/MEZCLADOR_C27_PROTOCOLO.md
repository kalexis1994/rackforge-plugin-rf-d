# Acoplamiento ON del mezclador con C27: protocolo

## Alcance fijado antes de ejecutar

SVC-9 Fig. 9-17 p.19: red ON nominal de cinco fuentes; Fig. 9-11
p.13 y tabla 7-8 pp.30–31: C27 = 10 µF entre BUS y BASE_Q29, positivo
hacia BASE. Se conservan los valores del puerto ON ya admitido y la
orientación histórica `v_C27 = BASE − BUS`. C27 ideal, nominal, sin ESR,
fuga o tolerancia (+50/−10 % documental). Las fuentes son tensiones
impuestas, α es fracción eléctrica, las ramas omitidas no son contactos OFF.

El puerto elimina BUS y devuelve corrientes y Jacobiano en OSC1, OSC2,
OSC3, NOISE, EXT y BASE_Q29. Permite estampar una carga dinámica en la
ecuación de Q29; no resuelve todavía el ladder, no cambia su código ni
admite la voz integrada. La reducción conserva la carga sobre las fuentes.

En Euler implícito, `g_c=C27/dt`, `h=BASE_anterior−BUS_anterior`,
`i_BASE=g_c·(BASE−BUS−h)`, positivo desde BASE hacia C27. KCL del BUS:
`I_mezclador_BUS−i_BASE=0`. La carga `h` está fija en cada evaluación
provisional: el llamador confirma `next_capacitor_v` sólo al aceptar el
paso conjunto. No hay integración adicional dentro del puerto.

Para `G=Y_BUS,BUS`, `u=BUS` con corriente de placa cero:
`m=G/(G+g_c)`, `c=g_c/(G+g_c)`, `k=G·c`.
`BUS=u+c·(BASE−h−u)`, `Δv_C27=m·(BASE−h−u)`.
Se calculan los cocientes con el menor/mayor para evitar desbordar la suma.
Se devuelve Δv directamente además de h+Δv para diagnosticar pérdida de
precisión al restar dos estados próximos. Es un método numérico, no un
parámetro audible calibrado ni equivalencia física con un Moog.

## Regresión independiente y gates

Oráculo Decimal de 80 dígitos: nodos resistivos originales (cursores
interiores explícitos, contactos límite unidos) más C27 como conductancia
de Euler y fuente de historia. Se elimina BUS y cursores con pivoteo;
no usa la fórmula reducida Rust. 31 conjuntos ON × nueve perfiles × tres
pasos `dt` (0,5 µs, 20 µs, 1 ms): 837 casos con historia y BASE no nulas.
Contraste de BUS, seis corrientes, todos los elementos 6×6 del Jacobiano,
Δv y próxima memoria. Gates absolutos: 1e−10 V, 1e−13 A, 1e−12 S.

Además: tangentes por diferencias simétricas, simetría/pasividad del
Jacobiano, identidad de energía de C27 y disipación numérica de Euler,
evaluaciones repetidas sin confirmar carga, continuidad entre pasos,
entradas no finitas/dt inválido/red vacía. Medición aislada del asignador
para 10 000 evaluaciones; cero heap no demuestra deadline de audio.
No nuevos solves SPICE para esta regresión; ensayo largo independiente
en curso conserva sus fuentes y gates. Compilación directa rustc con
binario privado conservado y hashes antes/después; no crear cache Cargo
que compita con el presupuesto serial de la nota larga.
