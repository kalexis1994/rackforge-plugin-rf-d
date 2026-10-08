# VCO1: API de subpasos y control temporal

2026-10-08. Base d6f4159. Nuevo alcance; el banco fijo rechazado y la copia
privada sólo ante rechazo conservan sus resultados. No modificar las leyes,
fuentes, grafo, constantes físicas o tolerancias de Newton anteriores.

## Stamp y raíces

Reutilizar el stamp DC y las cargas/incrementos estables de los BJT/JFET
anteriores. Añadir sólo ΔQ/dt y C/dt, las seis C de placa y las tres C/dos
L de cada 741. Para dt>=125ns delegar al stamp previo, exactamente.
Nuevo dominio dyádico de laboratorio: dt mínimo 125ns/4096=30.517578125ps,
máximo1ms; los otros módulos conservan sus límites. No afirmar que ese
piso es una constante del instrumento: es un límite numérico a verificar.
Usar el mismo Newton 64/24, Armijo y gates residual+corrección.

Antes de ciclos: contrastar todos los residuos, masa y 134×134 entradas
con incidencias/pivotes independientes, para C4 separadas y los doce pasos
125ns/2..125ns/4096. Estados previos completos ligados a exports preservados
en rampa/reset, sin clamps. Checks de nodos/corrientes, rechazo sin publicar
estado y delegación idéntica en el dominio anterior. Sin heap.
Gates de stamp: por fila residual/J absoluto 2e-12 (A/V/S por fila),
relativo2e-11; cero explícito y suma a masa. Gates de raíz anteriores:
2e-7V / 2e-10A, independent2e-14A/2e-12V, native1e-13A/1e-11V,
corrección2e-9V/2e-12A. Registrar precisión Decimal100 con interfaces
binary64 de primitivas.

## Política de precisión, previa a campaña

Paso completo h comparado con dos medios pasos h/2, con la misma entrada
aceptada. Error local en los 98 voltajes <=2e-6V y 36 corrientes <=2e-9A.
No excluir nodos de conmutación o filas internas. Si cualquier solve se
rechaza o error>1, reducir h a la mitad sin publicar candidato. Aceptar
ambos medios pasos sólo cuando pasan; duplicar h siguiente sólo si error
<=0.25, hasta el máximo de escena. Presupuesto máximo 16 intentos, piso
medio paso125ns/4096. Si el piso falla, conservar rechazo; no relajar error.
Los valores son controles numéricos, no parámetros físicos/calibración.

Campaña propia, máximo **aceptado** 500/250/125ns; h máximo es el doble.
Reloj entero en ticks125ns/4096, cada intervalo exporta dt real y todos
los estados/corrientes. 30ms, ventana tras15ms, C4 10/100pF separadas.
Mismos gates de resultado: frecuencia entre escenas250/125 <=1cent,
extremos de tres ondas <=5mV, dispersión de períodos <=1e-5 y balance
finito Qa/Q10-C1 <=0.002. Contraste externo Gear2/Trap2 conservado y
raíces independientes locales, desde su historia entrante declarada.

Heap cero no equivale a deadline. Recursos/export completos comprobados,
inputs/build/compiler/outputs con SHA. Fallos y replay de etapa sin cambios
antes de reparar. Sin audio/RT/carga activa/voz o calibración por esta campaña.
