# VCO1 y cadena: BUS conjunto

## Circuito y alcance

SVC-9 pp.5/19: VCO CA3046 clásico, selector SW6 sierra 3/10,
R6 de25 kΩ a fracción eléctrica0,5 y serie de33 kΩ.
SVC-9 pp.19/13/10: BUS, C27 de10 µF, ladder, VCAs y salida J7.
Se heredan las tarjetas nominales, temperatura25 °C y ambigüedades
documentadas de los bloques anteriores. No se identifica una unidad vintage.

Las tres resistencias del panel OSC1 pertenecen al stamp VCO:12,5 kΩ
salida→cursor,12,5 kΩ cursor→masa y33 kΩ cursor→BUS. OSC1 está excluido
del mezclador reducido de la cadena. Los otros cuatro puertos pueden ser
impuestos o estar fuera del subgrafo; su omisión no simula contactos OFF.
Esto evita duplicar la carga sin sustituir el cursor físico por una ecuación
equivalente. No se mantiene una fuente ideal en el BUS.

## Coordenadas

200 incógnitas:134 del VCO menos I(VMIXER), más68 de cadena menos su BUS
duplicado. Nodo VCO12 y cadena66 son la misma coordenada12. Se suman sus
KCL, incluidos C27 y las resistencias de panel. Se suprime fila/columna108
del VCO, exclusivamente la fuente VMIXER. Cadena0..65→133..198; C10_LEFT→199.
Las otras35 corrientes MNA y sus filas KVL conservan unidades y signo.

Estado e incrementos se representan con high/low normalizados. El helper
VCO es una copia aditiva del modelo admitido: mismas funciones BJT/JFET,
dominio y tarjetas741; solo amplía la representación del incremento.
Cargas lineales usan diferencias compensadas de rama, flujos L2/L3 usan
incremento de corriente; las cargas no lineales conservan su aproximación
de primer orden en low. Se hereda la extracción VCO Q/h = Euler−DC;
la cadena mantiene sus cargas explícitas. No se declara mayor precisión
física por esta transformación.

Radau IIA conserva B=[[1,5;0,5];[-4,5;2,5]],400 ecuaciones simultáneas.
Residuos:1e-13 A nodales,1e-11 V restricciones. Correcciones:2e-9 V y
2e-12 A para corrientes MNA. Newton64 iteraciones/24 reducciones, mérito
residual y criterios anteriores sin relajarlos. Intervalo común:
7,62939453125 ps..1 ms. Controles y puertos impuestos constantes en el paso.

## Verificación prevista antes de medir

- Identidad de incidencias y eliminación exclusiva de VMIXER, con comparación
  de matrices de los bloques admitidos; esto es una regresión estructural.
- KCL de interfaz derivada directamente de R45 y C27, con tolerancia
  1e-12 A +1e-12 relativa; derivadas por diferencias centrales1e-7 V,
  puerta1e-8 S +2e-5 relativa.
- Raíces locales acopladas, residuo y corrección <=1; no bastan para
  admitir trayectoria, fidelidad, error temporal ni nota completa.
- Copias de estado por valor: rechazo devuelve error y no publica candidatos.
  Medir heap en rutas concretas; stack de laboratorio no admite tiempo real.

La semilla de cadena proviene del banco independiente anterior y el VCO
de su arranque condicionado. Su BUS histórico común se elige explícitamente;
no equivale a arranque propio de la voz. Fallos, fuentes y replay se conservan
antes de corregirlos. No se exporta audio de pasos aislados.
