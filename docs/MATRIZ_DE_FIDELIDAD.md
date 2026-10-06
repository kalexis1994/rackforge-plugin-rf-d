# Matriz de fidelidad

Estado actual: [contorno cargado por filtro/dos VCA/salida](CONTORNO_PLACA4_RESULTADOS.md)
con diez escenas de 350 ms, tres contrastes y escucha de notas completas.
La entrada senoidal, alimentación de contorno y base Q21 siguen impuestas;
los semiconductores son tarjetas condicionadas. La [voz con VCO bajo carga](VOZ_ACOPLADA_RESULTADOS.md)
sigue nominal: cutoff bajo y ambos mute rechazan. Integración del contorno
con VCO [ensayada y rechazada](CONTORNO_VCO_UNION_RESULTADOS.md): cuatro
escenas monolíticas y control de puerto R45 fallido. Diecisiete recibos
auditados; completar cada parte no cierra su interfaz. Contorno de filtro,
parámetros físicos y ruta portable abiertos.
Convergencia finita no identifica una unidad vintage ni admite tiempo real.
Las reseñas numéricas anteriores se conservan como historial.

El [refinamiento de memoria](BIESTABLE_MEMORIA_JUNTURAS_RESULTADOS.md)
cierra el soporte 33 con dieciséis macroceldas, manteniendo curva, radio,
reloj y 22 memorias reales en P fija. **34 soportes hasta ≈350 µs**,
local nuevo **≤0,644 µV**, acumulado **≤0,793 µV**. El control de ocho celdas
rechaza y se conserva; 32/64 quedan no medidas por primera admisión.
Una inversa y tres tasas reutilizadas por identidad; 24 budgets y 192
subcertificados nuevos idénticos a los del control original en todos sus bytes.
Diez pruebas pasan al primero. Corpus de 763 entradas, 214 informes y 259
hashes propios, con 20 fuentes históricas y las tres excepciones CRLF.
No hay solves, candidatos o sistemas P nuevos ni reinicio del anclaje.
Próximo: [continuación refinada 34–39](BIESTABLE_CONTINUACION_REFINADA_PLAN.md).
**1 mV global sigue abierto.**

El [segundo banco preparado](BIESTABLE_CONTINUACION_PREPARADA_SEGUNDA_RESULTADOS.md)
certifica **33 soportes contiguos hasta ≈337,5 µs**, acumulado **≤0,793 µV**.
Los cuatro anchos admiten el soporte 32 y rechazan el 33: mejor cota rechazada ≈1,164 µV
para radio 1 µV. Se conserva el primer hueco y seis plantillas no alcanzadas.
Cinco inversas/preparaciones, 495 tasas, 64 budgets y 512 subcertificados
se reproducen contra el control completo. El grupo de cuatro junturas domina
el forcing acotado del nodo 66 en el interior; su término directo es pequeño.
Once pruebas aceptadas: nueve primarias al primero y dos archivísticas al
segundo. Corpus de 723 entradas, 184 informes y 228 hashes propios; 19
fuentes históricas más el fallo propio del fixture archivado con fuente exacta.
Próximo: [refinar memoria en el hueco](BIESTABLE_HUECO_MEMORIA_JUNTURAS_PLAN.md).
**1 mV global sigue abierto.**

La [continuación con preparación explícita](BIESTABLE_CONTINUACION_PREPARADA_RESULTADOS.md)
certifica **32 soportes contiguos hasta ≈325 µs**, acumulado **≤0,793 µV**.
Renueva nueve candidatos, una inversa uniforme y 99 consultas de tasa;
una preparación identifica el dominio nuevo en 64 budgets y 512 subcertificados.
Transporta las 22 memorias reales en P fija. Pico local nuevo ≤0,524 µV,
nodo 66 dentro del soporte 31; C7 termina con ≤461,567 nV.
Diez pruebas nuevas pasan al primero, con comparación completa contra control;
corpus de 688 entradas, 159 informes, 202 hashes propios y 19 fuentes históricas.
Parada por límite declarado. Próximo:
[segundo banco preparado, soportes 32–39](BIESTABLE_CONTINUACION_PREPARADA_SEGUNDA_PLAN.md).
Este banco no mide rendimiento nuevo. **1 mV global sigue abierto.**

La [preparación exacta de acciones](BIESTABLE_ACCIONES_PREPARADAS_RESULTADOS.md)
reproduce **64 presupuestos y 512 subcertificados idénticos en bytes** frente
al control y archivo original. Una pasada balanceada AB/BA reduce el wall
**24,39 %**, de 286,72 s a 216,79 s con preparación e identidades incluidas.
Son tiempos del laboratorio offline en este equipo. Se conservan **24 soportes
hasta ≈225 µs**, acumulado **≤0,793 µV**. Corpus: 657 entradas, 138 informes,
180 hashes propios y 18 fuentes históricas conservadas. Las siete pruebas
primarias pasan al segundo, tras corregir una expectativa de representación
sin cambiar helper, banco o tiempos. Las dos del corpus pasan al segundo;
ambos fallos de fixtures quedan archivados. Próximo:
[continuación con preparación explícita](BIESTABLE_CONTINUACION_PREPARADA_PLAN.md).
**1 mV global sigue abierto.**

La [continuación compartida](BIESTABLE_CONTINUACION_COMPARTIDA_RESULTADOS.md)
certifica **24 soportes contiguos hasta ≈225 µs**, acumulado **≤0,793 µV**.
Ocho referencias nuevas transportan 22 memorias reales; pico local nuevo
≤0,418 µV. Se renuevan nueve candidatos, una inversa uniforme, 99 consultas
de tasa y 512 acciones, sin solves de trayectoria o sistemas nuevos de P.
Diecisiete artefactos completos y su manifiesto fijan todas las identidades.
Nueve pruebas nuevas pasan al primero; corpus de 643 entradas y 135 informes.
La parada es por límite declarado. Próximo:
[preparar acciones con equivalencia exacta](BIESTABLE_ACCIONES_PREPARADAS_PLAN.md).
**1 mV global sigue abierto.**

El [recinto compartido](BIESTABLE_RECINTOS_COMPARTIDOS_RESULTADOS.md)
vuelve a certificar los mismos 16 soportes hasta ≈125 µs, error acumulado
≤0,793 µV. Una inversa uniforme sustituye 64 recintos y requiere 99 consultas
de tasa frente a 6336; se recalculan las 512 acciones con defecto y cola.
Ocho pruebas nuevas pasan al primero; corpus de 613 entradas y 115 informes.
P, curvas, RHS y transporte real se conservan. Este bloque reduce costes
de certificación offline; no amplía la cobertura temporal ni admite audio.
Próximo: [continuación con dominios nuevos](BIESTABLE_CONTINUACION_COMPARTIDA_PLAN.md).
**1 mV global sigue abierto.**

El [prefijo curvo por soportes](BIESTABLE_PREFIJO_CURVO_RESULTADOS.md)
certifica dieciséis intervalos nominales hasta ≈125 µs, pico local nuevo
≤0,372 µV y acumulado ≤0,793 µV. Renueva recintos, inversas, tasas y
acciones en cada referencia, con reloj real y transporte de 22 memorias.
El manifiesto completo alcanza el límite declarado de ocho soportes nuevos;
no se encontró hueco ni se certifican soportes posteriores por extrapolación.
Circuito e integrador se conservan. Trayectoria completa, 1 mV global,
hardware, sonido, voz, audio nativo y deadline mantienen sus gates.

La [referencia curva con extremos conservados](BIESTABLE_REFERENCIA_CURVA_RESULTADOS.md)
certifica el octavo soporte nominal: hasta ≈25 µs, pico local ≤0,327 µV
y acumulado ≤0,793 µV. Recalcula residual completo, cargas, RC y leyes
por piezas, y renueva inversas, tasas y acciones alrededor de la curva.
La cota se mide respecto a esa referencia; los endpoints e integrador
se conservan. Soportes siguientes, trayectoria completa, 1 mV global,
hardware, sonido, voz, audio nativo y deadline mantienen sus gates.

La [coordenada auxiliar de C7](BIESTABLE_FORCING_C7_RESULTADOS.md) conserva
el signo temporal y certifica el séptimo soporte nominal: hasta ≈12,5 µs,
error nodal ≤0,793 µV. Paga incertidumbre y Bp en todas las ecuaciones,
además del desplazamiento nodal y memoria final restituida. No modifica
trayectoria, cargas o parámetros físicos. El octavo soporte, trayectoria
completa, 1 mV global, hardware, audio y deadline mantienen sus gates.

El [prefijo dirigido renovado](BIESTABLE_PREFIJO_DIRIGIDO_RESULTADOS.md)
certifica seis soportes nominales hasta ≈6,25 µs, error nodal ≤0,754 µV.
Transporta 22 memorias y renueva recintos, tasas y acciones en P fija.
El séptimo soporte queda sin certificar; el forcing de C7 domina su
cota condicional. Dos ramas de 10 µV recuperan sus presupuestos exactos y rechazan,
con sus fallos originales de registro conservados. Hardware, sonido, voz completa,
meta global de 1 mV y deadline mantienen sus gates independientes.

La [acción de inversa sobre el RHS firmado](BIESTABLE_ACCION_RESIDUAL_RESULTADOS.md)
certifica el cuarto soporte y extiende el prefijo nominal hasta ≈1,5625 µs,
con error nodal ≤0,754 µV heredado del pico anterior. Cambia presupuestos
con defecto y cola probados; conserva restos independientes, circuito,
trayectoria y normas. No admite hardware, audio, 1 mV global o deadline.

El [prefijo con memoria individual y P retenida](BIESTABLE_PREFIJO_22_RESULTADOS.md)
certifica tres intervalos nominales hasta aproximadamente 781,25 ns, con
error nodal ≤0,754 µV. El cuarto rechaza por ≈4,3743 nV de exceso en
radio 1 µV; la invertibilidad y tasa interna negativa no admiten ese
tramo. Se transporta sólo memoria probada, sin reset. Hardware, audio,
trayectoria completa, 1 mV global y deadline siguen abiertos.

La [partición fina con anclajes conocidos](BIESTABLE_MEMORIA_COORDENADA_RESULTADOS.md)
prolonga la cobertura real hasta 390,625 ns, con dos intervalos contiguos
y error nodal ≤0,588 µV. Mejora 16 cotas lineales sin cambiar circuito
o reconstrucción. El cierre depende de los recintos medios y norma
certificados; no identifica hardware ni admite audio. Global 1 mV sigue abierto.

La [continuación con memoria saliente](BIESTABLE_PREFIJO_CERTIFICADO_RESULTADOS.md)
verifica interfaces y puentes de norma, pero rechaza el segundo intervalo
por presupuesto nodal ≈7,35 µV > radio 1 µV. Duración real certificada
permanece en 195,3125 ns; la parada conserva el certificado anterior.
Las cotas rechazadas no miden error físico. Global 1 mV sigue abierto.

La [comparación dirigida no lineal](BIESTABLE_TUBO_BLOQUES_RESULTADOS.md)
certifica t=0+ hasta 195,3125 ns para el modelo nominal: error nodal
≤0,586 µV con tubo de 1 µV. No hay solves nuevos ni cambios físicos.
La memoria final queda acotada en sus normas explícitas. El recorrido
completo, gate global de 1 mV, hardware, audio y deadline siguen abiertos.

El [primer tubo no lineal](BIESTABLE_PRIMER_TUBO_RESULTADOS.md) prueba
24 inversas del descriptor medio sobre 195,3125 ns, pero rechaza los tres
radios por falta de inclusión estricta de sus presupuestos nodales.
En aquel corte no se certificaba error continuo: su cobertura real quedó
en cero. Las cotas excesivas no son medidas de inestabilidad física.

La [publicación high+low y trayectoria propia](BIESTABLE_POST_KEY_ARRANQUE_RESULTADOS.md)
acotan el anclaje nodal inicial del integrador offline a ~37,51 nV, con
memorias conservadas. 512 pasos pasan publicación y KCL hasta ~2,332 ms;
coinciden con el histórico dentro de ~3,59 pV nodales en endpoints iguales.
Duración de error continuo realmente certificado: cero. El motor nativo,
resto temporal, hardware, voz audible y deadline mantienen gates separados.

El [evento post-KEY](BIESTABLE_POST_KEY_RESULTADOS.md) tiene raíz local
consistente para toda la caja de cargas DC, con error <=37,51 nV por nodo
y <=37,51 V/s por tasa de coordenada en la publicación racional. El reloj
seguía en cero en ese corte; quedaban publicación en el integrador y
certificación de trayectoria pendientes. Es una prueba del modelo nominal sintético. El gate
backward binary64 sigue rechazado; física, audio, deadline y 1 mV global
mantienen sus gates separados.

El [recinto del DC KEY=0](BIESTABLE_DC_EVENTO_RESULTADOS.md) certifica
existencia y unicidad local del modelo nominal, con ~74 pV de error nodal
y ~148 pV de memoria ponderada. Es precisión numérica de parámetros
sintéticos, sin identificación física vintage. La auditoría de CR10 refuta
conservar todos los voltajes al pasar KEY a 10 V dentro del dominio vigente.
Ese corte dejaba abiertos el estado post-evento y el error temporal global.

Los [sellos analíticos binary64](BIESTABLE_SELLOS_BINARIOS_RESULTADOS.md)
pasan ocho contrastes de corriente/derivada y ocho solves algebraicos.
Los mapas compensados pasan 4/4; el ordinario falla reset. Los 48 contrastes
reutilizan 24 respuestas centrales anteriores y no añaden solves no lineales.
Cuatro regresiones pasan. La cobertura de un intervalo no modifica todavía
el integrador ni los gates de trayectoria, física, audio y tiempo real.

La [transcripción estática Decimal](BIESTABLE_PRECISION_ESTATICA_RESULTADOS.md)
verifica el bloque de audio de 66 nodos: cuatro contrastes de corriente,
28 solves y 12/20 contrastes FD de derivada/mapa. Los mapas anteriores
pasan sólo prefijo/cola frente a la nueva referencia; ataque/reset fallan.
48 inyecciones y cinco regresiones pasan bajo sus gates propios. El resto
del modelo espacial y las cargas dinámicas siguen compartidos; no admite
refinamiento global, hardware ni audio.

La [sensibilidad FD](BIESTABLE_RESULTADOS_SENSIBILIDAD_FD.md) conserva
40 matrices: todas pasan álgebra, seis comparaciones de mapa pasan
(tres ventanas repetidas en dos rutas), y las diez de reset fallan.
Tres regresiones verifican replay y alcance. No identifica una derivada
exacta, el paso óptimo o una cota de error; no cambia física ni audio.

La [propagación local de memoria](BIESTABLE_PROPAGACION_DE_MEMORIA.md) pasa
32 contrastes centrales y 64 continuaciones hipotéticas (1024 intervalos).
Los 64 mapas mixtos pasan sus gates algebraicos. Las cuatro matrices FD
se resuelven con residuo racional cero; la comparación de mapas pasa 3/4,
con **reset fallido**. Diez regresiones preservan ese alcance y sus fallos.
No admite la matriz completa, error acumulado, conmutación física ni audio.

El [contraste E4G8 desde DC](BIESTABLE_CRECIMIENTO_DESDE_DC.md) añade 6486 intervalos y 1724 consultas válidas a tolerancias E4 fijas. Conserva 8,234 mV frente a D4; E4/E4G8 pasa sólo la selección muestreada con 0,426 mV. Menos rechazos no implica menor error o deadline: se añaden 564 ensayos aceptados y sólo se evitan 56 intentos totales. Las [identidades escalares de memoria](BIESTABLE_DEFECTO_Y_MEMORIA.md) no identifican una cota del DAE, cargas físicas ni sonido vintage.

El [barrido BDF2 de doble paso D4/E4](BIESTABLE_BARRIDO_DOBLE_PASO.md) añade 9446 intervalos publicados y 18884 medios provisionales aceptados, con gates de carga verificados. Las 866 consultas válidas conservan el máximo de 7,81 mV: falla el refinamiento global de 1 mV. El prefijo muestreado pasa con 4,615 µV; no cierra la transición, identificación física, error continuo ni audio. El solve FD del pico coincide, compartiendo el modelo espacial.

El [prototipo BDF2 de doble paso](BIESTABLE_ESTIMADOR_BDF2_DOBLE_PASO.md) verifica memoria y conservación de tres rutas en doce sondas; la diferencia cruda máxima es 0,684 µV. Es una sonda local, sin trayectoria adaptativa nueva ni cota global, y no modifica el fallo de 26,79 mV del contraste condicionado ni el de 126,37 mV desde DC.

Los [94 máximos por nodo consultados](BIESTABLE_MAXIMOS_CON_HISTORIAL_COMUN.md) y la rejilla retenida completan 664 solves y FD en ambos picos. El máximo consultado condicional de 26,79 mV falla 1 mV; no valida la trayectoria original de 126,37 mV desde DC, el circuito físico ni audio.

El [contraste condicionado a los mismos dos historiales](BIESTABLE_HISTORIAL_COMUN.md) reduce el máximo interpolado a 28,95 mV, pero no pasa 1 mV ni valida el prefijo desde DC. Verifica 1992 intervalos B3 nuevos y 4019 C3 heredados, sin reinicio ni selección de raíz. El máximo original de 126,37 mV conserva su fallo.

El [dominio de observación v2](BIESTABLE_DOMINIO_DE_OBSERVACION.md) completa 772/772 consultas sin retimar. El prefijo muestreado tiene 59,0 µV de diferencia máxima y pasa su gate diagnóstico; no demuestra error continuo. El máximo de 0,126368 V conserva el fallo global de refinamiento. No modifica las columnas de física o audio.

La [rejilla de observación B3/C3](BIESTABLE_OBSERVACION_ENTRE_MUESTRAS.md) guarda 772 consultas: 633 válidas y 139 fallidas, todas con pasos por debajo de 1 ps. Los máximos consultados/FD distinguen interpolación del pico persistente de 0,126368 V. Cobertura incompleta impide admitir el prefijo; permanecen abiertos los gates de trayectoria, física y audio.

La [política C3](BIESTABLE_TERCERA_MALLA_BDF2.md) divide por cuatro las tolerancias B3 y completa 3 ms con 4364 intervalos adicionales. El contraste máximo B3/C3 es 0,126368 V; al final 39,8792 µV. Persiste el fallo del gate global de 1 mV, sin admisión física ni audio.

La [auditoría de consultas](BIESTABLE_PREFIJO_Y_CONSULTA_TEMPORAL.md) reduce a 39,4 µV la separación de un punto de trigger inicialmente interpolado como 3,75 mV. En el máximo de transición, un solve al mismo tiempo conserva 0,563358 V. Son consultas provisionales con carga intacta/FD, sin modificar el gate temporal fallido ni admitir física/audio.

El [barrido BDF2](BIESTABLE_BARRIDO_BDF2.md) conserva 3236 intervalos y ambas políticas completan 3 ms. La diferencia final es 0,141 mV; la máxima de 0,563 V en ATTACK_GATE_LOWER impide admitir refinamiento de la trayectoria. El contraste con Euler y la fidelidad física permanecen abiertos.

El [corte BDF2](BIESTABLE_BDF2_CARGA.md) añade un segundo integrador temporal con conservación directa de carga, memoria doble, FD y RC analítico. Comparte el modelo espacial; no es una verificación independiente del circuito completo ni una admisión de transición/audio.

Los [cruces interpolados](BIESTABLE_TIEMPOS_DE_TRANSICION.md) sitúan adelantos B2 de 2,32 µs en ATTACK_OUT y 2,59 µs en la caída final de Q25. Las ventanas alineadas sólo son diagnósticas; todavía difieren hasta 61,5/126,2 mV y no cambian el gate temporal fallido al mismo reloj.

El [barrido compensado A2/B2](BIESTABLE_BARRIDO_COMPENSADO.md) cierra cobertura 0..3 ms y conservación publicada de 4152 medios intervalos. El contraste al mismo tiempo falla su gate de 1 mV: 5,147 V máximos y 6,45 mV finales. No se admite refinamiento, conmutación física ni audio.

El [corte de incrementos compensados](BIESTABLE_INCREMENTOS_COMPENSADOS.md) resuelve un límite numérico de C2 y comprueba memoria serializada y 32 intervalos posteriores con aritmética Decimal. Conserva el fallo adaptativo original. No añade identificación física, refinamiento de la trayectoria completa ni admisión de audio.

Los estados `desconocido`, `hipótesis`, `modelado`, `contrastado` y `cerrado para alcance declarado` se aplican **por columna**. Una fuente que documenta un control no prueba el audio. El estado inicial de todos los bloques es `desconocido` o `hipótesis`. La columna de audio identifica evidencia **externa**, no mediciones propias: RF-D se desarrolla [sin acceso físico](VALIDACION_SIN_HARDWARE.md).

| Bloque | Controles/datos | Topología/tiempo | Transferencia/cálculo | Audio externo | Riesgo audible | Próximo gate |
| --- | --- | --- | --- | --- | --- | --- |
| Teclado/glide/ruedas | Hipótesis | Desconocido | Desconocido | Desconocido | Medio | Grafo de placa 2 y escenas de legato simuladas |
| Tres osciladores | VCO1 con CV de placa explícito; ley completa de panel y osciladores 2/3 pendientes | [Grafo CA3046 y retornos auditados](VCO1_AUDITORIA_RETORNOS.md), convertidor, FET, Schmitt/reset, triángulo, pulso y panel | [Oráculo VCO1 funcional](VCO1_RESULTADOS_CIRCUITO.md): 14 escenas de convergencia revalidadas, dos C4 y calibración R11/R8 220–1760 Hz con dos notas reservadas; BJT/JFET condicionados, otros controles/rieles y mixer impuestos | Sin comparación física; escucha de ciclo estacionario del modelo | Alto | Ruta portable, mejor identificación de dispositivos, barrido CV/modulación, cargas compartidas de -4 V, mapa SW6 y bus de mezcla real |
| Ruido/modulación | Hipótesis | Hipótesis de manual | Desconocido | Desconocido | Medio | Redes y espectro calculado |
| Mezclador/feedback | Cinco fuentes e interruptores ON [trazados](MEZCLADOR_PANEL.md); J2 y SW15/16/17 de control de filtro con estados [trazados](BASE_Q26_CONTROL_FILTRO.md); R14 EMPHASIS 50 kΩ identificado, ley de giro y contactos OFF del mixer pendientes | Bus, [entrada C27/Q29](ENTRADA_FILTRO.md), [retorno C10→R14→R73→Q30](REGENERACION_FILTRO.md), [par inferior](PAR_ENTRADA_FILTRO_IDEAL.md), [base Q26](BASE_Q26_CONTROL_FILTRO.md) y [red Q26/Q28](COLA_FILTRO_Q26_Q28.md) trazados; R61 conflictivo | [KCL de cinco fuentes](MEZCLADOR_PANEL.md), [dos cargas pasivas](ENTRADA_FILTRO.md), [retorno pasivo](REGENERACION_FILTRO.md), [lazo AC cargado](LAZO_EMPHASIS_PEQUENA_SENAL.md) y [transitorio no lineal acoplado](TRANSITORIO_FILTRO_ACOPLADO.md) condicionados; ley de panel y carga de salida pendientes | Desconocido | Alto | Resolver R61, red OFF del mixer, variación de controles, fuentes y parámetros reales; contrastar niveles y resonancia |
| Filtro ladder | R39 RANGE y R73 REGEN CAL identificados; ley de panel y R61 físico pendientes | [Columna de 820 Ω](COLUMNA_RESISTIVA_LADDER_DC.md), [dos pilas de cinco transistores](PILAS_ACTIVAS_LADDER_DC.md), cuatro capacitores y [recuperación activa Q5–Q8](RECUPERACION_ACTIVA_FILTRO.md) trazados | [Oráculo ngspice de placa 4 con 19 escenas y cargas resueltas](FILTRO_VCA_RESULTADOS_CIRCUITO.md); [Cierre Ebers–Moll de 16 nodos](LADDER_EBERS_MOLL_DC.md), [lazo EMPHASIS AC](LAZO_EMPHASIS_PEQUENA_SENAL.md), [transitorio no lineal de 24 nodos](TRANSITORIO_FILTRO_ACOPLADO.md), [sensibilidad de 162 escenarios](SENSIBILIDAD_EMPHASIS.md), [ladder nativo](LADDER_SALIDA_NATIVA.md) y [C10 cerrado hasta J7](EMPHASIS_NATIVO_C10.md) contra oráculo de 62 nodos; el nativo incumple plazo | Candidatos sin analizar | Muy alto | β inverso y población R61, solver DSP acotado, ajuste de servicio, audio externo |
| Contornos/VCA | Dos multiplicadores, R13/R16/R19 y decay final trazados; giro→Ω y jack cargado pendientes | [Grafo volumen/gatillo de diez BJTs](CONTORNO_VOLUMEN_CIRCUITO.md), C2/C4/C7 y biestable con raíces ambiguas; redes de ambos VCA transcritas | [Puerto Q3/Q2/CR6 de cinco nodos](SEGUIDOR_VOLUMEN_NATIVO.md), 60 oráculos/derivadas y heap cero; [Ambos VCA y conversión con entrada eléctrica, mute/control/carga y escucha](FILTRO_VCA_RESULTADOS_CIRCUITO.md); contorno/base Q21 impuestos | Desconocido | Alto | Conmutación estable del biestable, cierre de R59/base Q18, alimentación/cargas compartidas, parámetros físicos, contorno de filtro y dominio físico de fuentes |
| Salida | R75/R77, C2, R20 VOLUME, R21 HEADPHONE VOL, C19/R50/R53, C21/R56/J7 y R57/R58 HI/LO documentados; ley angular e impedancias externas desconocidas | [Conversión PNP, diodos y acoplamiento C2](CONVERSION_SALIDA_DC.md), [R20, divisor HI/LO](SALIDAS_PANEL_HI_LO.md), [SW18 OFF](SW18_OFF_SALIDA.md), [grafo activo Q16/Q11/Q10](TOPOLOGIA_AMP_AURICULARES.md), [entrada pasiva de placa 3](ENTRADA_AMP_AURICULARES.md) y [salida pasiva a J7](ACOPLAMIENTO_SALIDA_AURICULARES.md) trazados; los CR1/CR2 de placa 4 siguen [condicionados por hoja moderna](DIODOS_SALIDA_1N458A.md) | [Salida AC de 51 nodos y reducción temporal](SALIDAS_PANEL_HI_LO.md), [transitorio de 48 nodos](TRANSITORIO_HASTA_SALIDA.md), [entrada pasiva AC de 54 nodos](ENTRADA_AMP_AURICULARES.md), [DC activo de 11 nodos](PUNTO_DC_AMP_AURICULARES.md), [AC de 12 nodos de placa 3](AC_AMP_AURICULARES.md), [BUS→J7 AC acoplado](AURICULARES_AC_ACOPLADO.md), [transitorio aislado de doce nodos](TRANSITORIO_AMP_AURICULARES.md) y [acoplado de 62 nodos](TRANSITORIO_AURICULARES_ACOPLADO.md) con [bloque analítico de placa 3](JACOBIAN_ANALITICO_AURICULARES.md), [estrés corto de 256 pasos](ESTRES_TRANSITORIO_AURICULARES.md), [estrés bipolar de 768 pasos](ESTRES_BIPOLAR_AURICULARES.md), [refinamiento temporal de 672 pasos](CONVERGENCIA_TEMPORAL_AURICULARES.md), [sensibilidad AC de 324 escenarios](SENSIBILIDAD_AC_AURICULARES.md), [81 escenarios de placa](SENSIBILIDAD_SALIDA.md) y [54 de panel](SENSIBILIDAD_PANEL_SALIDA.md) condicionados | Desconocido | Medio | Completar las 50 columnas anteriores y solver acotado; identificar curvas de diodos/TIS, contactos y cargas reales |

## Afirmación pública actual

La [reutilización de dirección Newton](DIRECCION_NEWTON_REUTILIZADA.md) conserva 23224 valores en bits en las capturas de apagado, los gates globales y heap cero. Reduce 23,18 % la media precisa a 2,953 ms/bloque; 640/640 bloques aún exceden deadline. No amplía audio externo ni admite el host.

La [continuación DC de fuentes VCA](DC_VCA_CONTINUACION.md) admite 18 semillas para primer/segundo/ambos controles a cero, con 1,568833 nV frente a raíces independientes, 576 puntos intermedios y 18 cargas reconstruidas. Añade 1152 pasos nativos manteniendo esas fuentes. Es preparación fuera de audio, con 33 solves DC; no resuelve Note Off ni reemplaza el contorno, ni modifica C6/C7.

Los [saltos temporales VCA con cargas fijas](SALTOS_VCA_HISTORIAL_FIJO.md) pasan 384 muestras con integración independiente (7,150162 nV), 24 Jacobianos y rescate de 16 rechazos. No se integra el tiempo entre etapas y sólo se publica el estado final. El costo y un gate de identidad de stack de 1 pV siguen fallidos; no se selecciona automáticamente ni identifica el contorno.

El [perfil 8/16/32 y estado temporal común](ETAPAS_VCA_Y_REPRODUCIBILIDAD.md) amplía a 1152 pasos y reduce 38,46 % el costo de esas escenas con ocho etapas; 30/30 bloques siguen fuera de plazo. Con entradas completas iguales, los workers coinciden exactamente tras 32768 pasos y observan 328 KiB de stack comprometido. El fallo de identidad desde semillas DC distintas se conserva; no amplía C6/C7 ni identifica la causa de la variación de arranque.

El [criterio temporal KCL + corrección de voltaje](CRITERIO_VOLTAJE_TRANSITORIO_GLOBAL.md) corrige las 96 sondas de apagado (0,150 nV máximo), pasa heap cero y 752384 muestras de estrés. Su costo aumenta 69,3 % a 3,939 ms/bloque; C7 sigue fallido. No resuelve los saltos abruptos ni el contorno físico.

El [apagado de los VCAs con rampas impuestas](APAGADO_VCA_GLOBAL_66.md) registró 20/96 sondas >1 µV interno con la política anterior, hasta 1,318 mV. El criterio de voltaje corrige esa brecha. Las cuatro escenas de salto directo siguen fallando de forma atómica.

La [semilla DC completa y el criterio de corrección de voltaje](DC_GLOBAL_SEMILLA_COMPLETA.md) contrastan 14 puntos (2,25 nV máximo) y resuelven cutoff máximo desde el centro. Dos semillas desplazadas fallan en RANGE=0; no se garantiza cualquier semilla. La nueva observación de stack es 324 KiB y C7 sigue abierto.

El [barrido de extremos global](EXTREMOS_CONTROLES_GLOBAL_66.md) no pasa: conserva seis fallos de arranque/apagado. [R20 exacto](R20_EXTREMOS_EXACTOS.md) pasa ocho escenas ON/OFF y 128 pasos independientes (error interno máximo 0,279225 µV). [R21 exacto](R21_EXTREMOS_EXACTOS.md) pasa 128 pasos con integración independiente e historiales propios (0,219477 nV), ambos topes/R61, corrientes y Jacobianos. El barrido actualizado acepta 17408 muestras sin rechazar topes R21; la ruta por particiones aún exige R21 interior. No amplía la validación contra audio vintage.

El [banco de stack Win64](STACK_GLOBAL_66_WIN64.md) pasó 98304 muestras en workers de 2 MiB/1 MiB/512 KiB en la compilación anterior (288 KiB comprometidos). Con el criterio DC se repiten 32768 muestras a 512 KiB y se observan 324 KiB, incluidas guardas. Valida inicialización, reintento y rechazo atómico para la escena; no mide el pico exacto ni admite el host.

El [refinamiento global 48/96/192 kHz](REFINAMIENTO_TEMPORAL_GLOBAL_66.md) pasa 26880 pasos con descenso máximo/RMS de J7, C2 y R21. El cociente cercano a dos es consistente con Euler de primer orden en las escenas suaves. No fija error absoluto contra tiempo continuo ni admite oversampling del plugin.

Las [ventanas de estrés con oráculo independiente](VENTANAS_INDEPENDIENTES_ESTRES_GLOBAL.md) contrastan 192 pasos a tres tasas y ambos R61, con historiales nativos declarados. Error máximo interno 0,204625 µV y J7 0,397665 nV. El alcance son cuatro pasos por ventana; C6 y C7 siguen abiertos.

El [estrés largo global](ESTRES_LARGO_GLOBAL_66.md) acepta 752384 muestras en seis escenas, sin fallos ni reintentos: 11756 auditorías de KCL y 188084 controles de historial C10 abierto. Amplía la validación de convergencia con fronteras sintéticas; no es un oráculo independiente de esas nuevas trazas ni una admisión de deadlines.

La [evaluación compartida de exponenciales](EXPONENCIALES_GLOBAL_66.md) añade un gate específico de corriente/derivada y reduce otro 9,306 % la media global a 2,23336 ms/bloque. No altera las ecuaciones ni admite la ruta en el host; C6 y C7 siguen abiertos.

El [ensamblado global ordenado](ENSAMBLADO_GLOBAL_ORDENADO.md) conserva las 66 KCL y los gates numéricos. Reduce 5,013 % la media local a 2,46534 ms/bloque; los 640 bloques medidos aún exceden el plazo. Se admite como optimización experimental; C6 y C7 siguen abiertos.

El [solver global de 66 nodos](SOLVER_GLOBAL_66_NODOS.md) añade Jacobiano completamente analítico y eliminación de ceros exactos, con arrays fijos. Reproduce 128 pasos del oráculo Python (J7 0,248 nV) y pasa el contraste de 8192 muestras contra la partición, después de hacer más estricta la tolerancia del primer VCA. Cinco corridas alternadas reducen el costo medio 9,39 veces a 2,559 ms/bloque; 640 de 640 bloques globales aún exceden 1,333 ms. El estado de audio externo permanece abierto y C7 no pasa.

El [puerto nativo Q26/Q28](CUTOFF_NATIVO_Q26_Q28.md) añade C18, ambas junturas y carga TAIL variable en 72 pasos aislados. La [integración hasta J7](CUTOFF_LADDER_J7_NATIVO.md) reemplaza la corriente de cola impuesta y coincide en 128 pasos con un oráculo de 66 nodos: error J7 22,4 nV e interno 1,374 µV. Red pasiva, tangentes e historial de C18 están contrastados; las fuentes de control y los parámetros BJT siguen impuestos. El nuevo escenario tarda ~25,7 ms por bloque y no pasa C7.

La [malla temporal de 15 supuestos de semiconductores y temperatura](SENSIBILIDAD_TRANSITORIA_SEMICONDUCTORES_AURICULARES.md) amplía la evidencia numérica de la fila **Salida**. El [ladder nativo hasta J7](LADDER_SALIDA_NATIVA.md) amplía el cálculo condicionado con C10 abierto y los dos valores de R61. Sus amplitudes BUS→J7 no cambian el estado de audio externo ni validan la población vintage.

El [solver denso NumPy opcional](SOLVER_DENSO_AURICULARES.md) acelera esos barridos offline y fue cotejado contra la ruta Python; no es aún una implementación DSP de tiempo real.

Un [presupuesto Newton 16/16](PRESUPUESTO_NEWTON_AURICULARES.md) cerró KCL en 3136 pasos sintéticos de salida. La política de fallo y el cumplimiento de plazos en DSP nativo siguen pendientes.

El [reintento por subpasos](REINTENTO_SUBPASOS_AURICULARES.md) es un experimento offline de recuperación; muestra una diferencia de discretización medible y no se admite automáticamente como política del motor de audio.

Los [vectores de portabilidad BUS→J7](VECTORES_PORTABILIDAD_AURICULARES.md) fijan tolerancias de equivalencia numérica para la ruta acoplada. El [puerto nativo de placa 3](PUERTO_NATIVO_PLACA3_AURICULARES.md) coincide con 192 pasos aislados, la [frontera R77/R21→placa 3](PUERTO_NATIVO_PANEL_AURICULARES.md) con 96 pasos y la [salida C2→J7](PUERTO_NATIVO_C2_SALIDAS.md) con otros 96. El [paso Q1/Q12/Q17→C2→salidas](PUERTO_NATIVO_CONVERSION_C2_ACOPLADA.md) reproduce 32 pasos; [Q1_BASE/C4](PUERTO_NATIVO_C4_CONVERSION_SALIDA.md) añade 28, [VCA2→J7](VCA2_SALIDA_NATIVA.md) añade 16 y [VCA1/R2/C6/C15→J7](VCA1_SALIDA_NATIVA.md) añade 12. La [traza de 192 muestras](TRAZA_AUDIO_NUMERICA_VCA1.md) prueba señal y cambios de controles en esa ruta parcial. El [cierre nuevo de 62 nodos](EMPHASIS_NATIVO_C10.md) extiende la equivalencia numérica hasta BUS con C10, sin aportar evidencia de fidelidad sonora.

El [punto DC nativo de Q1/Q12/Q17](PUERTO_NATIVO_CONVERSION_SALIDA_DC.md) reproduce tres escenarios condicionados de placa 4 e inicializa C2. Su [paso temporal](PUERTO_NATIVO_CONVERSION_C2_ACOPLADA.md) carga Q17 con la corriente dinámica de C2 y el [bloque siguiente](PUERTO_NATIVO_C4_CONVERSION_SALIDA.md) resuelve Q1_BASE con R10/R11/C4. El [puerto hacia VCA2](PUERTO_NATIVO_HACIA_VCA2.md) entrega tres corrientes y su tangente local; el [segundo VCA unido hasta J7](VCA2_SALIDA_NATIVA.md) resuelve Q14/Q13/Q21 y el segundo cursor en 16 pasos contra un oráculo de 15 variables. Su [puerto hacia VCA1](PUERTO_NATIVO_HACIA_VCA1.md) expone cuatro corrientes y una matriz `4×4`; el [primer VCA unido](VCA1_SALIDA_NATIVA.md) incluye R2/C6/C15 y coincide con un oráculo de 25 variables. Su [puerto de R2](PUERTO_NATIVO_HACIA_FILTRO.md) devuelve corriente y admisión local al [recuperador Q5–Q8 nativo](RECUPERACION_SALIDA_NATIVA.md), que coincide con un oráculo de 33 variables. El [puerto C5/C1 hacia el ladder](PUERTO_NATIVO_HACIA_LADDER.md) entrega dos corrientes y una matriz `2×2`; el [ladder nativo](LADDER_SALIDA_NATIVA.md) las carga y [C10/EMPHASIS](EMPHASIS_NATIVO_C10.md) añade un tercer puerto de retorno. Ambos R61 se compararon con un oráculo completo de 62 nodos y la traza de 192 muestras añadió cambios de R14/SW18. El plazo medido de audio sigue excedido; faltan el mezclador y las leyes de control.

En el ladder, la [columna resistiva DC](COLUMNA_RESISTIVA_LADDER_DC.md), las [pilas activas](PILAS_ACTIVAS_LADDER_DC.md) y el [cierre Ebers–Moll de 16 nodos](LADDER_EBERS_MOLL_DC.md) están trazados. El cálculo condicionado incluye corrientes de tap y conducción base colector; un [barrido de 72 supuestos](BARRIDO_SESGO_LADDER_DC.md) comprueba el límite activo. Transferencia temporal y audio permanecen desconocidos, así como β inverso y el valor físico de R61.

RF-D **pretende** recrear un Model D clásico. No hay aún una implementación sonora ni resultados de comparación que permitan afirmar fidelidad.

El [cierre de contorno/cadena de 94 nodos](CONTORNO_CADENA_94_Y_ESTABILIDAD.md) calcula C2 y reset con 21 historiales. Se reproducen tres raíces con FD independiente, se conservan 370 pasos y ocho rechazos del refinamiento temporal. La [auditoría de cargas rápidas](BIESTABLE_TRES_RAICES_Y_CARGA_RAPIDA.md) encuentra un modo creciente en la raíz intermedia bajo 54 escenarios de cargas hipotéticas. Es diagnóstico: ninguna carga física identificada, rama seleccionada, estabilidad global, conmutación ni audio admitidos.

El [puerto cargado de C2/reset](PUERTO_CONTORNO_CADENA_71.md) contrasta cuatro derivadas de corriente y gradientes de todos los nodos en 36 escenarios DC/temporales; diferencia máxima de admisión 2,04 pS, refinamiento FD y candidato temporal comprobados, heap cero. Es cálculo condicionado con fuentes impuestas. No cierra la estabilidad del biestable, el contorno físico, audio externo ni recursos de la voz.

El [seguidor/R59/Q18 y cadena de 71 nodos](SEGUIDOR_VCA_CADENA_71.md) cierra topología y cálculo condicionado en veinte destinos DC y 256 pasos: nodos 2,50 nV, dieciocho cargas y corrientes verificadas, cero heap. Conserva doce rechazos primarios recuperados por continuación con memoria fija y un rechazo de preparación desde una semilla apagada. C2/reset permanecen impuestos. El biestable, audio externo, voz completa y deadline no están admitidos.

La ausencia de hardware propio es permanente para este plan. Cada bloque puede alcanzar `cerrado para alcance declarado` en **topología** y **cálculo**, mientras su audio externo permanezca abierto. Ese estado nunca se interpretará como identidad sonora con un ejemplar vintage.

Las [primitivas de carga de juntura](CARGAS_JUNTURA_Y_DOMINIO_BIESTABLE.md) tienen verificación matemática de dos terminales (300 sondas sintéticas y siete pruebas), con doce sesgos del biestable auditados. Cero sesgos coinciden con la medida Cob a 10 V; tiempos de tránsito, carga en saturación, partición BJT completa y dispersión siguen desconocidos. Su informe original no modifica el circuito ni admite física/audio.

El [BJT intrínseco conservativo](BJT_INTRINSECO_CARGA_CONSERVATIVA.md) pasa 72 puntos contra ngspice46 y matrices AC completas. El [circuito cargado](BJT_CARGADO_TRANSITORIOS.md) añade 252.000 pasos y refinamiento independiente, con error observado máximo 1,35 mV. Cierra implementación matemática en el subconjunto declarado (qb=1, TF/TR constantes y sin resistencias internas); parámetros físicos, transporte más completo y conmutación del biestable siguen pendientes. No cambia la admisión del motor/audio.

La [sonda del biestable no lineal](BIESTABLE_CARGA_NO_LINEAL.md) añade cuatro cargas Q25/Q15 a las 21 memorias del circuito de 94 nodos. Doce masas locales pasan contraste con AC ngspice y FD; los descriptores conservan rango 25 y un modo creciente en cada raíz intermedia. Doce repeticiones conjuntas del paso de 1 ms siguen dando tres soluciones por escena, con reproducción FD desde otra semilla. Falta trayectoria refinada desde el arranque y dinámica de los otros dispositivos. No es contraste independiente de la cadena completa ni admisión de conmutación física/audio.

El [primer barrido adaptativo desde DC](BIESTABLE_TRAYECTORIA_ADAPTATIVA.md) añade 2982 intervalos publicados y 72 rechazos conservados. La política A llega a 3 ms; B se detiene a 2,444485 ms ante el paso mínimo. La discrepancia observada de 5,00592 V en ATTACK_OUT impide admitir refinamiento. Sus gates locales pasan en los pasos guardados, pero no sustituyen un oráculo independiente ni resuelven la incertidumbre física del contorno.

El [diagnóstico del último rechazo](BIESTABLE_RECHAZO_Y_ORIGEN_CARGA.md) sitúa un límite de representación en C2: el residuo de 11 pA queda fuera del gate y los vecinos `float64` también. FD reproduce el fallo. Dos sombras de origen de carga cambian el criterio relativo sin alterar los incrementos terminales; no se publican ni corrigen la trayectoria. El [corte de incrementos](BIESTABLE_INCREMENTOS_COMPENSADOS.md) cierra ese intervalo con memoria compensada y define la métrica v2; el refinamiento completo sigue siendo un gate separado.

La [auditoría estática sobre cuatro ventanas](BIESTABLE_VENTANAS_ESTATICAS_RESULTADOS.md) pasa 64/64 mapas compensados frente a Decimal y 256 solves algebraicos. Las rutas ordinaria/mixta conservan 10/40 discrepancias, respectivamente. Cuatro regresiones pasan; aún no admite integrar desde DC, conmutación física ni audio.

La [variante explícita J66 compensado](BIESTABLE_INTEGRADOR_COMPENSADO_RESULTADOS.md) conserva el residual original y completa 64 intervalos con memoria propia. Nodos/memorias pasan 10 nV; corrientes, correcciones y publicación conservan sus gates. Cuatro regresiones pasan tras corregir un adaptador de presupuesto con fallo archivado. No es trayectoria desde DC, refinamiento global ni admisión de audio/deadline.

El [reloj completo compensado](BIESTABLE_RELOJ_COMPLETO_COMPENSADO_RESULTADOS.md) conserva 6.486 intervalos propios, DC fresco y publicación; máximo nodal 6,21 pV y memoria 8,77 pV bajo 10 nV. Cuatro pruebas pasan. El reloj impuesto no valida el controlador, refinamiento global, física ni audio/deadline.

El [controlador compensado E4G8](BIESTABLE_CONTROLADOR_COMPENSADO_RESULTADOS.md) conserva decisiones, reloj, 49 rechazos y 12.968 sombras. Sus 6.486 estados publicados coinciden exactamente con la variante a reloj fijo. Cinco pruebas pasan. Las comparaciones D4/E4 permanecen en 8,234/1,002 mV y fallan 1 mV; equivalencia del controlador no admite error global, física, audio ni deadline.
