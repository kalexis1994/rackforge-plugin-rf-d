# VCO1: coordenadas incrementales y memoria de dos componentes

2026-10-08. Base cad6841. CA3046 nominal, 25Â°C, SW6 3/10/0.5 ON,
CV/rieles/mixer impuestos. Mantener los rechazos anteriores, circuito,
constantes y gates de Newton/refinamiento. No hay acceso fÃ­sico.

Estado aceptado completo:134 pares hi+lo, normalizados, volts en98 nodos
y amperes en36 ramas. TwoSum conserva el error de suma en radix2/redondeo
exacto: Shewchuk1997, teorema7/p.8 (PDFp.12),
[fuente primaria](https://people.eecs.berkeley.edu/~jrs/papers/robustr.pdf).
Usar TwoSum sin condiciÃ³n de tamaÃ±o, nunca reassociation/fast-math.
El acumulador de dos componentes se verifica por Decimal100; no se llama
aritmÃ©tica exacta de precisiÃ³n arbitraria al motor completo.

Resolver134 incrementos delta con la misma memoria hi+lo entrante durante
trials. C de placa/741 usan C*(delta_a-delta_b)/dt; L usa L*delta_I/dt.
El candidato guarda ambas componentes, no reconstruye memoria desde hi.
Se reutilizan DC, I/J/Q/C y Î”Q estables de los dispositivos existentes.
Para tÃ©rminos DC, R(hi)+J(hi)*lo; para junturas, Î”Q(hi_actual,hi_previo)
+ C_actual*lo_actual-C_previo*lo_previo. Jacobiano en hi: aproximaciÃ³n
cuasi-Newton. TÃ©rminos omitidos de orden loÂ² deben quedar debajo del gate
por contraste contra leyes/incidencias Decimal100 sin redondeo intermedio.
No presentar esta expansiÃ³n como una ley fÃ­sica nueva o idÃ©ntica bit a bit.

Dominio anterior de nodos/ramas/junturas y dt30.517578125ps..1ms;
lo finito normalizado, rechazo de memoria inconsistente. Capacitancias,
trims y parÃ¡metros permanecen en sus grafos previos. Gates de stamps:
2e-12 absoluto (unidad de fila/J),2e-11 relativo, masa1e-11A.
Gates raÃ­z: native1e-13A/1e-11V y correcciÃ³n2e-9V/2e-12A;
independent2e-14A/2e-12V y correcciÃ³n2e-10V/2e-13A;
contraste2e-7V/2e-10A. Presupuesto64/24 y Armijo anteriores.

Banco:48 tuplas de subpasos anteriores (C4 separadas/rampa/reset/doce dt),
mÃ¡s el rechazo preservado de NEG4_REF en61.03515625/30.517578125ps;
incidencias y leyes Decimal100 completas, pivotes propios. Verificar toda
matriz, partes bajas y KCL/fuente/masa, sin seeds SPICE nuevos. Historiales
de laboratorio sÃ³lo para raÃ­ces locales condicionales.

DespuÃ©s: step doubling con2ÂµV/2nA,16 intentos y reloj entero anterior,
publicaciÃ³n atÃ³mica de midpoint/endpoint completos.30ms, tras15ms,
mÃ¡ximo aceptado500/250/125ns, C4 separadas. Mantener1cent/5mV entre250/125,
dispersiÃ³n1e-5 y balanceQa/Q10-C1 .002. Cada export guarda hi+lo, dt real,
corrientes y ratios; comparar intervalos de reset con raÃ­ces independientes.
Corpus, fuentes/compiler/outputs por SHA; fallo y replay sin cambios antes
de reparar. Tests sin heap; no deadline, fÃ­sica, carga activa o audio por
una sola trayectoria. Si falla, no ampliar campaÃ±a ni relajar los gates.
