# Familia estacionaria CV/BUS: resultado

2026-10-17. [Protocolo previo](VCO_FAMILIA_PROTOCOLO.md),
[oráculos](../evidence/vco_family_oracle03.json.gz),
[generación](../evidence/vco_family_generation01.json),
[contraste](../evidence/vco_family_model01.json) y
[QA](../evidence/vco_family_tests01.json).

## Candidato y dominio

CA3046/SVC-204D, SVC-9 pp.5/19, nominal 25 C; C4=10 pF,
R8=.2613404652606161, R11=521.3126579373712 ohm; SW6=3/10, R6=.5.
KEYBOARD [-3.1,-.1] V, BUS [-.125,.125] V, otras cinco entradas -2.1 V;
rails impuestos, NEG4_REF con red original y carga externa adicional 0 A.
Son voltajes de placa. Sin calibración MIDI ni identificación de un vintage.

Ocho entrenamientos: cuatro CV en ambas fronteras BUS. Interpolación
cúbica de log2(f) y de coeficientes complejos en CV, lineal en BUS.
Integración Fourier exacta del ciclo lineal por tramos entre los últimos
resets reales a -2 V, coeficientes 0..64 de saw/tri/pulse/IC1_SUM/NEG4/Qa/Q10.
DC conservado, sin retirar nivel, alinear fase extra o reajustar por nota.
El dato Rust es idéntico al generado al retirar las secciones reservadas.
No se interpolan dispositivos o estados internos y no se garantiza un
límite de error en todo el continuo por comprobar puntos finitos.

## Puntos reservados y errores

Cuatro BUS=0 regenerados con resets densos, conservando sus CV binarios originales; tres
CV nuevos [-2.6,-1.6,-.6] con BUS=.0625 V. Estos siete lugares no entran
al ajuste. Nueve comparaciones reservadas: las siete anteriores más
Trap2/125 ns y Gear2/62.5 ns en -1.6/.0625. Los dos últimos son el mismo
lugar y no se cuentan como lugares independientes. Todas las trayectorias
completas nuevas tienen 30 ms, arranque propio SPICE sin fuente periódica.
Los datos BUS=0 eran conocidos: reserva para ajuste, no experimento ciego.

| Máximo reservado | Medido | Gate previo |
|---|---:|---:|
| Frecuencia | 0.0853243099 cent | 1 cent |
| DC saw/tri/pulse | 1.45419943e-05 V | .005 V |
| Vector armónicos 1..8 | 0.000122796523 relativo | .02 |
| DC corriente panel | 1.32152434e-10 A | 2e-9 A |
| Armónicos 1..8 corriente panel | 2.56875548e-10 A | 2e-9 A |
| DC corriente CV | 1.93204827e-16 A | 2e-9 A |
| Armónicos 1..8 corriente CV | 1.56506149e-15 A | 2e-9 A |

IC1_SUM pasa DC y norma armónica absoluta <=10 uV en los cinco contrastes
nuevos reservados (tres lugares, dos métodos adicionales). No hay corriente
CV exportada en los cuatro BUS=0 de salida densa: allí sólo se califican ondas,
frecuencia y panel. Qa/Q10 DC conservan balance relativo <=.002 con la
exclusión heredada de Q7/cuadratura. Armónicos 9..64 se guardan como
diagnóstico, sin afirmar exactitud de picos rápidos con una serie finita.
No se produce audio ni se usa esta serie como antialias ya admitido.

Los ocho entrenamientos coinciden con sus oráculos anteriores con gates
1 cent/5 mV/2%; las dos referencias nativas 250/125 ns del punto
-2.1/.125 contrastan forma/frecuencia/panel. Son una frontera entrenada,
no dos puntos reservados ni nuevas trayectorias nativas. Método y paso
SPICE pasan sus gates propios en -1.6/.0625. No se amplía por eso el
único punto dinámico nativo anterior a toda la matriz.

## Resolución del oráculo reservado

El primer contraste de panel con BUS=0 coarse falla y repite: 32 nA DC y
90.6 nA de armónicos, frente a 2 nA. Se conserva
[fallo/modelo](../evidence/vco_family_model_failure01.json) y fuente. No
se cambia el candidato ni el gate. Se regeneran sólo esos cuatro oráculos
con su ciclo denso y el mismo circuito, bajo
[decisión previa](VCO_FAMILIA_RESERVA_DENSA.md). La reserva densa pasa los
gates originales. Las tablas antiguas conservan su contraste de
frecuencia/forma con 5 mV/2%; sus corrientes coarse quedan explícitamente
sin admisión. El oráculo de salida nuevo exporta ocho columnas, no los
estados completos o corrientes CV del VCO.

Los tres JSON de intentos de oráculo se archivan gzip sin pérdida;
[índice](../evidence/vco_family_receipt_storage01.json) y
[lector](../tools/vco_family_receipts.py) restauran cada byte y SHA original.
No duplicar todo el recibo dentro de otro: sus entradas se vinculan por
hash y el QA fija los archivos comprimidos efectivamente commiteados.

El [diagnóstico de derivadas](../evidence/vco_family_derivative_diagnostic01.json)
conserva fallo/replay de la diferencia centrada BUS con incremento 10 uV:
la sensibilidad de frecuencia es -0.000548798 Hz/V y la resta entre dos
frecuencias de unos 311 Hz pierde cifras. Incrementos 0.1/1 mV convergen.
Se selecciona 1 mV antes de repetir toda la grilla, conservando el gate
relativo 1e-5 más 1e-10 absoluto y el candidato por bytes. El cambio es
del contraste numérico; no se modifica la derivada expuesta por la familia.

## Puertos y conservación eléctrica

Eliminación algebraica exacta del wiper de R6=25k dividido por mitades
y R45=33k una sola vez. Salen tres corrientes entrando al panel desde
saw, ground y BUS; suma <=1e-18 A y potencia terminal igual a disipación
resistiva <=1e-18 W. Comparación con MNA independiente del panel:
1.35525272e-20 A de error máximo. El modelo activo total
no tiene aquí una demostración de conservación global de potencia.

IC1_SUM reducido conserva las seis leyes (Vcontrol-sum)/R de las entradas
originales. Las fuentes SPICE independientes contrastan esos seis signos
más Vmixer en todas las muestras retenidas, <=2e-12 A. La sensibilidad
saw(BUS) está en la interpolación: no añadir una R45 externa duplicada.
El jacobiano expuesto diferencia la familia estacionaria a fase fija;
no es una admitancia de pequeña señal dinámica de todos los dispositivos.
Rails, selector y los otros CV permanecen fijos por contrato.

Consulta Rust: 245 puntos de CV/BUS/fase y 9 entradas inválidas. Incluye
fronteras, fases 0/1, NaN, infinito y extrapolación rechazada. Cero
asignaciones medidas durante consultas válidas e inválidas; impresión y
lectura están fuera del kernel. Python/Rust, derivadas por diferencias
centradas, KCL, disipación y MNA pasan. Controles negativos de +2 cent,
+10 mV de DC saw y +100 uV de IC1_SUM son rechazados. No se añaden unit
tests que repitan estos ensayos; 272 tests previos se heredan por identidad.
No se mide deadline de voz, otra plataforma o seguridad frente a CV temporal.

## Fallos, formatos y recursos

[Import inicial](../evidence/vco_family_preflight_failure01.json): EXE
pertenece al módulo lm741_reference; replay previo sin trabajo científico.
[Corrección](../evidence/vco_family_import_correction01.json) de import.
[Primer candidato](../evidence/vco_family_oracle01.json.gz) falla el wiper:
los índices de cycle_v omiten tiempo, los del export crudo lo incluyen.
Se guarda fuente, ventanas y replay idéntico antes de corregir sólo
columnas; [decisión](../evidence/vco_family_column_correction01.json).

[Segundo](../evidence/vco_family_oracle02.json.gz) conserva seis ciclos
válidos y el rechazo/replay del ASCII alto que supera 256 MiB.
[Decisión binaria](../evidence/vco_family_binary_decision01.json): no
ampliar límite ni cambiar ecuaciones. El export rechazado fue retirado
antes de registrar tamaño exacto/digest: consta sólo su límite inferior,
con deck/log/fuente/replay. No atribuirle identidad de bytes o reanálisis.
[Control del formato](../evidence/vco_family_binary_control01.json):
280x25 valores ASCII/binario del mismo plot corto, cero diferencias por
bits incluido cero con signo. [Contrato](VCO_FAMILIA_EXPORT_BINARIO.md).
El lector estricto añade sólo unidad corriente para i(Vsource); nombres,
escala y payload se verifican, sin suponer el orden del raw.

El candidato completo reusa seis entrenamientos sin copiarlos y añade
siete trayectorias binarias, más cuatro de salida BUS=0 densa. Diecisiete trayectorias válidas únicas nuevas,
cuatro procesos fallidos contando replays y un control corto de formato.
Ventanas float64 exactas en packs sin pérdida, con offsets/digests,
y coeficientes regenerados por bits de las diecisiete ventanas. El pack fallido
por columnas se archiva por deduplicación exacta: las dos ventanas comprimidas
son idénticas, se guarda una y la receta de repetición. Se reconstruyen todos
los bytes del pack original y su hash, sin quitar muestras o precisión;
[recibo](../evidence/vco_family_failure_storage01.json) y
[restaurador](../tools/vco_family_failure_archive.py). El JSON fallido no cambia. El prefijo de
cada recorrido se retira tras digest/métricas y sólo es regenerable.
Una sola área temporal queda vacía; sin Cargo, nueva rlib, cache o WAV.
Compiler/ngspice/macromodelo y escucha anterior siguen por hash. El límite
32 MiB incluye todos los recibos/packs de este bloque, excluyendo QA.

## Admisión y siguiente paso

Se admite el kernel de laboratorio estacionario y sus puntos contrastados.
No modifica la voz activa, renderer, productor, solver o escucha actual.
No acredita CV/BUS variables en el tiempo, acoplamiento dinámico a la
cadena, otro selector/trim, RT o parecido audible con un instrumento.
Siguiente: evaluar el acoplamiento del puerto reducido con el mezclador y
contrastar corrientes/forma frente al circuito completo en escenas fijas,
antes de usarlo en una nota integrada. Separar luego la respuesta con
memoria ante CV/BUS temporal de esta aproximación estacionaria.
