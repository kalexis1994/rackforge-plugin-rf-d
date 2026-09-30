# Control nativo de cutoff Q26/Q28

## Alcance y procedencia

`cutoff.rs` reproduce cuatro nodos de la placa 4 del perfil documental clásico: base Q26, emisor Q26/base Q28, colector Q26 y colector Q28. SVC-9 Fig. 9-11, PDF p. 13, fija R39=10 kΩ, R46=68 kΩ, R45=330 Ω, R60=680 Ω y C18=100 pF. SVC-9 Fig. 9-17, PDF p. 19, y Table 7-8, PDF pp. 30–31, fijan las ramas de panel. La transcripción previa está en [base Q26](BASE_Q26_CONTROL_FILTRO.md) y [cola Q26/Q28](COLA_FILTRO_Q26_Q28.md).

Las fuentes de contorno, teclado, modulación y jack son fronteras eléctricas impuestas en V y Ω. Su generación y las curvas angulares de los potenciómetros siguen pendientes. No se convierte una posición eléctrica en frecuencia de cutoff mediante una curva ajustada.

## Red de panel y ecuaciones

R11 de 5 kΩ entre −10/+10 V aporta `Vth=−10+20a` V y `Rth=5000a(1−a)` Ω, en serie con R55=200 kΩ. R74=47 kΩ recibe el contorno. R70=1800 Ω y el segmento activo R49 de 0..500 Ω terminan a masa. J2 sin cable mantiene R51=100 kΩ a masa; con cable añade la impedancia declarada. SW15 OFF termina R52=33 kΩ a masa; ON conecta la fuente de modulación. SW16/SW17 OFF abren las ramas de teclado de 300/150 kΩ. Con ambas ON se calcula su paralelo antes de sumar una sola vez la impedancia compartida del teclado.

La reducción calcula `G=Σ1/R` S y `Vth=Σ(V/R)/G` V. La corriente saliente de base es `(Vbase−Vth)G`. R39 RANGE usa la misma reducción de potenciómetro: `Vrange=10b` V y resistencia `68000+10000b(1−b)` Ω.

Q26 PNP y Q28 NPN usan ambas junturas de Ebers–Moll: `F=Is expm1(s Vbe/Vt)`, `R=Is expm1(s Vbc/Vt)`, `Ib=F/βf+R/βr`, `Ic=F−(1+1/βr)R`, con polaridad s y `Vt=kT/q`. Se conserva KCL de las tres terminales. Esto extiende la referencia anterior de región activa y permite conducción base-colector de Q28 cuando TAIL pierde margen. No incluye Early, ruptura, carga almacenada ni capacitancias de juntura.

C18 usa Euler implícito: `I=C18/dt*(Vbase−Vbase_anterior)`. La condición DC abre C18. El puerto TAIL entrega `(Vtail−VcolectorQ28)/680` A y su derivada local en S, obtenida resolviendo el Jacobiano de cuatro nodos con historial fijo. Las evaluaciones son provisionales: sólo un paso convergido publica el estado.

## Dominio e incertidumbre

Posiciones eléctricas 0..1; R49 0..500 Ω; impedancias de fuente ≥0 Ω; dt>0 s; parámetros BJT positivos y finitos. Los interruptores ON exigen una fuente declarada. El solver rechaza exponentes de juntura >45, datos no finitos, falta de descenso y agotamiento de presupuesto. Máximo Newton 16 iteraciones y 16 divisiones de búsqueda; tolerancia KCL 10 pA. El estado queda intacto ante fallos.

Is, β directo/inverso y temperatura son hipótesis explícitas. Los escenarios 285/298,15/315 K y β distintos no identifican un instrumento real. B-804C2 exige emparejar Q26/Q28 por VBE; no determina estos parámetros. Rails ±10 V ideales y ausencia de ruido/deriva siguen siendo límites.

## Contraste

`tools/cutoff_ebers_moll_reference.py` calcula KCL independiente con Jacobiano por diferencias finitas. `tools/cutoff_native_vectors.py` congela 72 pasos a 48 kHz en tres escenarios, incluyendo C18, RANGE, contorno, teclado, modulación, jack y TAIL bajo. `tests/test_cutoff_native_vectors.py` regenera la evidencia y contrasta el límite activo con la referencia previa. `crates/rf-d-circuit/tests/cutoff_vectors.rs` compara los cuatro nodos (<1 µV), corriente (<1 nA), red pasiva y tangente, además de fallos atómicos. Se comprueba asignación cero en el test global de procesamiento.

El puerto aislado queda contrastado en cálculo condicionado. Aún falta medir el costo del circuito integrado y contrastar audio externo; estas pruebas no prueban fidelidad sonora ni cumplimiento de tiempo real.
