# Lectura pasiva de J7 a 48 kHz

## Dominio y derivación

Misma escena CA3046/SVC-204D, leyes y puertos SVC-9 pp.9/19/13/10 del
[arranque admitido](CHAIN_STARTUP_PROTOCOLO.md): 0–100 ms, KEY ON 1 ms,
OFF 75 ms. Fuente de fase periódica ya existente. No añadir ganancia,
impedancia ni fuente de corriente a J7. Leer su tensión en voltios.

Cada Accepted publica dos pasos fine Radau. Interpolar sólo el escalar J7
en cada mitad, con el polinomio cuadrático que pasa por inicio, etapa a
theta=1/3 y final a theta=1. En incrementos HIGH/LOW respecto al inicio:
V(theta)=V0+4,5 theta(1-theta) delta1+(1,5 theta²-0,5 theta) delta2.
Los extremos devuelven el voltaje del estado admitido directamente.
Es una lectura numérica interior, sin nueva raíz eléctrica ni estado
interpolado que pueda alimentar memorias o pretender KCL interior exacta.

Reloj racional n/48000 s, comparaciones en u128 contra ticks enteros de
125 ns/65536. Sin suma acumulativa de periodos. Intervalos (inicio,final],
con muestra inicial separada: 4801 muestras entre 0 y 100 ms inclusive.
No forzar pasos eléctricos en fronteras de audio ni cruzar cambios KEY.
Almacén fijo del llamador; rechazo atómico ante capacidad, discontinuidad,
tiempo/estado/etapas inválidos. Sin heap ni archivos en la lectura.

## Gates previos a la campaña

Perfil 32 us: DC, ROOT, eventos, GRID y estado final iguales por bits a la
campaña de arranque. Perfil adicional máximo 8 us, mismo inicio y eventos;
comparar las 4801 muestras: diferencia RMS relativa <=0,001, máximo de
diferencia dividido por pico de referencia <=0,003 y media absoluta <=1 uV.
El refinamiento debe ejecutar una trayectoria distinta. Conservar Newton
1 pA/2 nV y error <=1; mismo estado eléctrico tras lectura, heap cero.
Rechazos/reintentos exactos, capacidad agotada y extremos sin duplicación.
Comprobar además extremos interpolantes contra etapas publicadas y un
oráculo polinómico independiente. Registrar gates fallidos y replay sin
cambios antes de cualquier corrección.

Esto admite un búfer offline en voltios de una nota de laboratorio. No
admite antialias, WAV normalizado, plugin ni tiempo real o parecido físico.
48 kHz es el reloj de lectura elegido, no evidencia de banda limitada.
Compiler/rlib congelados; recibos <=8 MiB sin QA; un tmp/lab-current vacío
al terminar, sin cache, Cargo, biblioteca o carpetas de muestras nuevas.

## Refinamiento conservado tras el primer fallo

32/8 us falla el gate previo de 0,1 % RMS: 0,98138 % observado. Conservar
el ensayo y replay; no relajar gates ni cambiar leyes, ganancias o memorias.
La grilla anterior de 125 us y dos propuestas 64/32 us no bastaba para
acreditar la salida a reloj de audio. Medir ahora máximos 4/2 us, mismos
4801 puntos y mismos límites. El control exacto de la trayectoria previa
se conserva en el perfil 32 us archivado, cuya implementación de lectura
no cambia. La admisión de precisión dependerá de la pareja nueva.


4/2 us también falla: RMS 0,1486675 % y máximo 0,3316821 % del pico.
Conservar segundo fallo/replay y contrastar ahora 2/1 us, sin mover gates.
Reutilizar la trayectoria de 2 us por identidad de modelo, lector y receta;
ejecutar sólo la nueva referencia 1 us. No duplicar simulaciones admitidas
para completar un par que ya tiene su primer miembro archivado.
