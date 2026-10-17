# Familia estacionaria CV/BUS: protocolo previo

2026-10-17. CA3046/SVC-204D, SVC-9 pp.5/19; mismo perfil, 25 C,
R8=.2613404652606161, R11=521.3126579373712 ohm, C4=10 pF,
SW6=3/10 y R6=.5 que el contraste CV/carga. Otras cinco entradas
-2.1 V, rails impuestos y NEG4_REF con su red; carga externa adicional=0.
Sin hardware. No sustituir el perfil de fase nominal o la escucha actual.

## Separación previa de ajuste y validación

Ocho ciclos de entrenamiento: KEYBOARD [-3.1,-2.1,-1.1,-.1] V,
BUS [-.125,.125] V. Exportar además IC1_SUM e intensidades de las siete
fuentes CV/BUS: los exports anteriores no contienen la corriente CV.
SPICE Gear2/125 ns, 30 ms, sin fase impuesta, mismo circuito y tolerancias.

Validación reservada, sin entrar al generador de coeficientes:

- Cuatro BUS=0 de la calibración anterior, con sus CV binarios originales.
- Tres CV intermedios [-2.6,-1.6,-.6] V, BUS=.0625 V, nuevos Gear2/125 ns.
- En -1.6/.0625, Trap2/125 ns y Gear2/62.5 ns. Estos dos contrastes
  separan el error del oráculo del error de reducción; no se ajustará con ellos.
- Dos ciclos nativos cargados anteriores -2.1/.125 para contraste heredado;
  están en una frontera de entrenamiento, no cuentan como puntos reservados.

Representar frecuencia por interpolación cúbica de log2(f) en CV y lineal
en BUS. Misma interpolación tensorial para coeficientes Fourier complejos
0..64, integrados exactamente sobre el último ciclo lineal por tramos,
fase definida por sus resets reales a -2 V. Canales: saw, tri, pulse,
IC1_SUM, NEG4_REF, Qa y Q10. Conservar DC. No alinear, normalizar, ajustar
trims, añadir corrección por nota o usar puntos reservados en el ajuste.
El orden y los nodos son parte del candidato; si falla se conserva/replay
antes de decidir otra aproximación. No garantizar error entre puntos.

## Puertos y corrientes

R6=25k ohm, dos mitades 12.5k; R45=33k una vez. Eliminar el wiper por
su KCL exacta: w=(saw/12500+BUS/33000)/(2/12500+1/33000).
Corrientes entrando al panel en [saw,ground,BUS]:
[(saw-w)/12500, -w/12500, (BUS-w)/33000]. Suma cero y disipación
igual a la suma de R*i². No sumar R45 nuevamente al conectar este puerto.
La respuesta saw(BUS) está en la familia; no es una impedancia independiente
de frecuencia ni admisión ante BUS temporal/arbitrario. Derivadas CV/BUS
son derivadas de esta familia estacionaria, no una admitancia dinámica.

Cada corriente CV entrando al circuito es (Vcontrol-IC1_SUM)/R original:
BEND150k, TUNE560k, KEYBOARD51100, MOD51100, EXT51100, RANGE15000 ohm.
Contrastar contra los signos opuestos de i(Vsource) de SPICE. Reducir
IC1_SUM preserva estas leyes; no prueba todo el KCL del circuito eliminado.
Rails fijos y formas tri/pulse cargadas por la topología original: no nuevos
puertos libres. No afirmar conservación de potencia del oscilador activo.

## Gates congelados y alcance

Oráculos: periodicidad <=1e-5 y balance Qa/Q10/C1 <=.002, con exclusión
Q7/cuadratura anterior. Nuevos extremos de entrenamiento contra los ocho
ciclos previos: frecuencia <=1 cent, extremos <=5 mV y DC <=5 mV,
vector de armónicos 1..8 <=2 %. Método/refinamiento igual en el reservado.

Familia en cada reservado: frecuencia <=1 cent; DC de saw/tri/pulse
<=5 mV; norma vectorial de armónicos 1..8 <=2 % por onda. IC1_SUM DC
<=10 uV y armónicos <=10 uV de norma absoluta. Corrientes CV y panel:
DC <=2 nA, norma armónica 1..8 <=2 nA. Error de extremos/picos crudos,
armónicos 9..64 y Qa/Q10 instantáneos son diagnósticos, sin prometer
reproducir el reset rápido con sólo 64 armónicos. Medir Qa/Q10 DC y
balance relativo <=.002. No convertir el pequeño efecto de BUS sobre
frecuencia en requisito de invariancia o resolución física.

KCL del panel <=1e-18 A, identidad de disipación <=1e-18 W; contraste
de sus tres ramas contra solve independiente de nodos. Corrientes fuente
contra leyes originales en todas las muestras retenidas <=2e-12 A.
Derivadas analíticas contra diferencias centradas en puntos interiores
de consulta, tolerancia relativa 1e-5 más 1e-10 absoluto en unidades SI.
Fronteras incluidas; rechazar no finitos y extrapolación, sin clamping.

Motor de consulta fijo sin IO/heap; generador/laboratorio separados.
Comparar consulta Rust contra Python, incluyendo derivadas y puertos;
no promover al motor audible en este bloque. No RT, transitorios CV,
cambio de selector, otros trims o fidelidad vintage por pasar estos gates.

## Recursos y recibos

Un tmp/lab-current vacío al inicio/final. No Cargo/rlib ni WAV nuevo.
ngspice/modelo/compiler congelados por el QA previo. Preservar deck/log,
digest del export completo, cruces asentados, métricas y último ciclo con
contexto exacto float64 en un pack XZ sin pérdida; prefijo sólo regenerable.
No copiar el binario anterior ni crear carpetas por escena. Recibos nuevos
<=32 MiB sin QA, transitorios <=256 MiB, reserva >=1 GiB,
SPICE <=180 s/proceso, compilación <=120 s. Conservar fallo y replay
idéntico con fuentes antes de corregir. Pruebas heredadas por identidad;
no reejecutar la campaña física completa ni sumar ensayos como unit tests.
