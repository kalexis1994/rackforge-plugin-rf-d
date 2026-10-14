# C5 y gatillo compartido: cierre funcional de placa 2

2026-10-14. Base d1d19bda385d8fbe7a1a5b94915fd25cc128f85a.
SVC-9 PDF p9 Fig9-7 y p19 Fig9-17; SVC-204D p65. Sin hardware.
Conservar fuentes y QA anteriores por identidad. Banco nuevo, sin prolongar
las trayectorias de voz anteriores.

## Conectividad revisada

Q12/Q20 y contorno de volumen se conservan una sola vez. R32 10 kΩ añade
pull-up alimentación→Q12C; R37 10 kΩ alimentación→Q20C; R35 10 kΩ lleva
Q20C al ánodo CR1 (1N34A), cátodo Q4B. R26 10 kΩ: Q12C→C1 izquierdo,
C1 10 nF→Q1B. Q1/Q4 NPN a masa: Q1C→R14 33 kΩ→Q4B, Q4C→R3 10 kΩ→Q1B,
alimentación→R4 10 kΩ→Q4C. R6 560 Ω/R5 3,3 kΩ forman la base Q5 PNP
entre alimentación y Q1C. Q5E alimentación, Q5C→R1 100 Ω + R12 panel→C5.
C5 10 µF a masa; su corriente incluye R48/Q22 y la rama de decay.

Q6 NPN: base Q1C, colector alimentación, emisor→R8 10 kΩ→−10 V y
R9 4,7 kΩ→Q7B. Q7 NPN: colector→R15 panel→C5, emisor SUSTAIN_E.
Q8 PNP: emisor SUSTAIN_E, colector→R11 100 Ω→masa; base por R13 4,7 kΩ
desde cursor R18 panel 5 kΩ y por R17 placa 150 kΩ a −10 V. R10 placa
27 kΩ alimentación→SUSTAIN_E; C8 100 pF SUSTAIN_E→masa. CR2 1N4004:
ánodo SUSTAIN_E, cátodo Q12C. R17 placa y R17 Amount panel son distintos.

Q22/Q21, R17 Amount/R74 y Q26/Q28 reutilizan el puerto admitido sin duplicar
R74. Q4B y C5 dejan de ser fuentes: sus corrientes se suman a KCL internas.
C11 47 pF une Q21B/Q21E. Revisión de C12 500 pF: une alimentación y Q21E,
en paralelo con R50. El documento anterior lo dejó fuera y describió su
frontera de forma imprecisa; conservar esa versión y registrar aquí la
corrección, sin alterar el banco ya medido.

## Dominio, memoria y fronteras

54 nodos nativos: 29 de volumen/gatillo, 9 del puerto de filtro y 16 de
temporizador/sustain. Oráculo original con cursor Amount explícito: 55
nodos en posición interior. R12 ataque eléctrico 0..1 MΩ se combina en
serie con R1, sin epsilon. R15 decay eléctrico >0..1 MΩ; tope cero de
decay queda fuera de este primer dominio y requiere unión exacta posterior.
Volumen se prueba con ataque 1 kΩ/decay 10 kΩ, sustain eléctrico 0,5;
filtro con ataque 0 Ω/decay 1 kΩ, sustain 0,5, Amount 0,5/cutoff 0,5.

BJTs/diodes Ebers–Moll/Shockley conservan hipótesis nominales previas.
Q25/Q15, Q1/Q4 y Q12/Q20 incluyen la ley BE/BC de depleción más difusión
nominal ya contrastada: 7/5 pF, potencial 0,75/0,7 V, grading 0,5/0,33,
FC 0,4 y tiempos 1/3 ns. No son parámetros identificados. Otras cargas de
juntura y la alimentación decoupled siguen fuera. Dos recetas C11/C12:
0/0 y 47/500 pF; cada una conserva su propio DC y memoria fija.

Puertos: masa, alimentación 9,3 V, −10 V, +10 V, teclado, base VCA,
TAIL del ladder, Thevenin cutoff y RANGE. Base VCA 0 V, TAIL 1,4 V,
Thevenin cutoff 0 V/RANGE 1 V, rieles ideales. No cerrar aún placa 4,
VCO/voz o audio; ambas envolventes cargan eléctricamente el gatillo.

## Banco y gates antes de medir

DC propio de reposo con KEY 0/S abierto. Radau IIA de dos etapas, historia
anterior fija; paso completo frente a dos medios pasos y publicación sólo
de la solución admitida. Gates Newton KCL 1 pA/corrección 2 nV; control
temporal local 0,2 µV + 2e−7·|V| por nodo. Reloj entero con tick 2⁻³⁰ µs.
Máximos de paso 8/4 µs, 1 ms de reposo, KEY10 en 1 ms, liberación en
10 ms, nuevo gatillo en 20 ms y liberación en 30 ms; final 36 ms.
Probar teclado y S-trigger en escenas propias, conservando memoria al evento.

Contrastar todos los nodos/cargas a clocks comunes (cada 0,25 ms y eventos):
≤20 µV + 2e−6·|V| y corrientes ≤2 nA + 2e−5·|I|. Contrastar KCL originales
en etapas seleccionadas: ≤20 pA y Newton original ≤2 nV, raíces DC ≤1 µV.
Jacobiano DC/dinámico por FD en DC, primer paso, alrededor de eventos y
cambios de biestable: ≤2 nS + 2e−5·|referencia|. Balances integrados de
C5/C2/C1/C4/C7 y junturas: error corriente ≤20 pA por intervalo; publicar
excursión, ataque/decay, efectos del gatillo y tiempos observados sin tratarlos
como calibración vintage. Replay completo por bits, restore de receta y
estado, fallos atómicos; no seleccionar raíces alternativas en un paso fallido.

Preservar cualquier fallo y repetir sin cambios antes de reparar. Privados
nuevos ≤64 MiB, reserva ≥1 GiB, compilación ≤120 s/ejecución ≤300 s por
perfil. Usar biblioteca congelada, sin Cargo/cache/SPICE nuevo. Rechazar
timeout y pasos inválidos conservando estado. Admitir el alcance que realmente
pase y conservar explícitos todos los recorridos rechazados.
