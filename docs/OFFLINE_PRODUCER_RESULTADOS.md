# Productor offline admitido para la escena nominal

[Protocolo previo](OFFLINE_PRODUCER_PROTOCOLO.md),
[implementación](../crates/rf-d-circuit/src/nominal_offline_producer.rs),
[banco](../tools/offline_producer_probe.rs),
[recibo](../evidence/offline_producer_native01.json) y
[QA](../evidence/offline_producer_tests01.json).

## Propiedad del paso y avance cooperativo

Producer une estado HIGH/LOW, reloj entero, propuesta adaptativa,
fronteras de KEY/grilla, Pipeline y un único old/Accepted pendiente.
El workspace se presta aparte. El reloj eléctrico puede adelantar al
lector ese único paso: getters distintos evitan confundir cálculo y
consumo. El pendiente conserva también coarse/fine, incrementos, etapas,
residuales, correcciones, h/error, iteraciones e intentos.

pump recibe cuota de invocaciones del integrador y un slice de Frames.
Retorna escritos, invocaciones, pasos consumidos y motivo de parada.
Una llamada puede publicar pasos antes de parar; la atomicidad corresponde
a cada entrega de Accepted. Sin espacio se retiene el paso y se impide
resolver otro. Cuota cero puede drenar ese pendiente; no inicia un solve.
Un error eléctrico es terminal y conserva progreso/diagnóstico; reintentar
no lo convierte en falta de capacidad ni repite el solve fallido.

cold_start resuelve DC antes de pump: no se factura dentro de esa cuota.
from_initial valida representación/t=0, no demuestra que el estado sea
un DC del circuito. Finales admitidos: múltiplos de 125 us hasta 301 ms;
KEY ON 1 ms/OFF 200 ms. Los finales cortos sirven como prefijos. Ningún
flush con futuro inventado, normalización o cambio de retardo del FIR.

## Contraste real

| Recorrido | Cuotas | Capacidades | Llamadas pump principales | Pendientes/reanudaciones |
| --- | --- | --- | ---: | ---: |
| Escalar con control | 1 | 0 en primeros Frames, luego 1 | 5170 | 2 |
| Irregular | 0/7/31/3/127 | 0/1/3/0/17/2/64 | 313 | 78 |
| Ráfagas | 1024/1/509/0/17 | 0/0/128/7/0/2 | 81 | 35 |

Cada recorrido integra realmente 0–10 ms: 5170 Accepted, 3841 entradas
384 kHz y 433 Frames. Cada valor/índice coincide por bits con el prefijo
AA8 archivado de 301 ms. Los 236 HIGH/LOW finales coinciden con el recibo
anterior de salida continua; Pipeline y planificación final coinciden
entre los tres recorridos. No se reejecuta una nota larga.

En el primero se ejecuta además un control independiente del mismo motor,
con el planificador anterior. Se comparan por bits los 5170 Accepted
completos y estados, no sólo J7: coarse, ambas fine, etapas/incrementos,
h/error, iteraciones e intentos. El Buffer RAW anterior coincide por bits
con sus 3841 valores archivados. La sustitución del solver sólo existe
como seam interno de crate para contraste/inyección; pump público usa
voice::advance. Los otros dos recorridos llaman pump directamente.

Mínimo full 3,90625 ns; máximo residual 0,999767797 pA, corrección
1,995961016 nV, estimador 0,958472920. Estos diagnósticos se miden en el
primer recorrido/control; los campos 1/0/0/0 de los otros dos en stdout
son centinelas de no medición, no un residual eléctrico cero acreditado.
Las leyes y el motor son idénticos a la auditoría previa; no hay nuevas
filas de ecuaciones originales auditadas.

Los 115 pendientes se clonan/reanudan con workspace nuevo. Antes de
drenarlos se repiten dos llamadas sin capacidad, con cuotas 0 y 1000:
cero solves/publicaciones, mismo estado/Accepted/historia y sentinela de
salida. Luego cuota cero publica exactamente una vez y ambas ramas quedan
idénticas. El primer pendiente termina en KEY ON 1 ms; otro ya atravesó
KEY sin perder fase o carga. Se comprueban final idempotente y conteos.

Tres tests unitarios nuevos cubren constructor/fronteras, fallo inyectado
con progreso parcial y diagnóstico terminal, y cuota cero/final sin
padding. KEY OFF 200 ms se comprueba sintéticamente en el planificador;
no se atribuye a este ensayo una integración real hasta ese evento.
Los cuatro tests anidados anteriores se filtran y se heredan de su QA.

## Memoria y alcance

sizeof Producer = 36328 bytes; Pending = 24760 bytes, ya incluido en
Producer. Workspace = 279824 bytes, separado y no incluido en ese tamaño.
Heap medido cero en pump, clones, control y reanudación. No es medición
de pico total de stack. Una invocación puede contener hasta 32 reintentos
adaptativos y Newton/line search: una cuota no representa milisegundos
de CPU ni un deadline. La cadena sigue offline.

Se conservan origen/SHA de voz, solver, inicializador, lector y FIR.
Compiler/rlib congelados, fixtures recuperados de dos recibos por hash;
ningún input sonoro privado nuevo. tmp/lab-current vacío al terminar,
sin nuevo WAV, muestras, Cargo, cache o rlib. El único WAV anterior
permanece con su SHA admitido. QA hereda 261 tests y ejecuta tres nuevos:
264 cubiertos, sin reejecutar la suite histórica o los 301 ms.

Siguiente: entrada de render offline que una cold_start, productor,
progreso/cancelación entre cuotas y el único export regenerable. Validar
su ciclo completo conservando escala/latencia y comparando contra la
referencia admitida. Mantener separado ese uso del trabajo posterior de
controles musicales, VCO físico y ejecución en tiempo real.
