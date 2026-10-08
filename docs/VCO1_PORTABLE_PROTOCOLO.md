# VCO1 portable: contrato antes de medir

Migrar el kernel residual Radau admitido en `06b78be` al crate existente.
Conservar por bytes el cuerpo, álgebra, orden de sumas, tarjetas, gates y
Newton 64/24. El único cambio del kernel es el nombre del módulo fine.
Fine debe ser idéntico a la copia admitida y al módulo incremental antiguo
salvo su piso declarado de 125 ns/65536. No cambiar el API antiguo.

Perfil físico nominal clásico CA3046: SVC-9 PDF p.5/19; 25 °C,
C4=10 pF, controles y bus mixer impuestos. Heredar las fuentes, unidades,
dominios e incertidumbre de VCO1_STAMP/INCREMENTOS/RADAU_CICLOS; copiar
el solver no identifica hardware ni amplía el dominio eléctrico probado.
Radau sobre las 134 incógnitas hi/lo, ambos 741 y flujos completos.

## API y publicación

Engine de referencia con memoria fija. Checkpoint contiene estado completo,
controles, reloj absoluto u64, propuesta, máximo y presupuesto de intentos.
Máximos medios 65536/131072 ticks (125/250 ns), mínimo medio 4 ticks;
reloj y destinos múltiplos de 8 ticks. Rechazar destinos que no se pueden
partir en pares completos; jamás truncar, redondear o agregar tiempos.
Restaurar exige dominio finito y normalización hi/lo, además del contrato
de reloj/controlador. La historia restaurada no se declara propia.

Cada llamada propone un par. Resolver full/mid/end; error máximo de
full−end <=1 con 2 µV/2 nA, sin división Richardson. Halvar por rechazo;
crecer hasta máximo si error <=0,25. Máximo configurable 1..20 intentos,
sin cambiar presupuesto Newton. Publicar ambos endpoints y observaciones
solamente si todos pasan; fallo conserva checkpoint íntegro. Corrientes
Qa/Q10/Q7 usan derivada Radau, R6=12,5 kohm para panel. No emitir, guardar,
loggear ni reservar heap desde las funciones del engine.

## Verificación delimitada

Reejecutar intervalos seleccionados admitidos y el rechazo local recuperado,
comparar estados con Decimal100 heredado: 2e-7 V/2e-10 A; corrientes
2e-10 A. Confirmar gates residual/corrección <=1. No contar el uso de una
raíz guardada como solve independiente nuevo. La identidad exacta del
kernel permite heredar los dos recorridos de 30 ms sin reejecutarlos.

Probar arranque propio, continuidad checkpoint/restore, reloj >u32, límite
u64, destinos inválidos y rollback de rechazo temporal/no lineal. Medir heap
de arranque, restauración, aceptaciones y rechazos con contador; fixtures y
asserts fuera del intervalo medido. Compilar O2, GNU fijado y pila de
laboratorio 8 MiB. Preservar fuentes/comandos/stdout/stderr de cada intento.
Presupuesto proceso 900 s; disco reserva 1 GiB + estimación build 128 MiB,
serial. No volver a ejecutar 235 tests heredados sin cambio en sus módulos.

Pila 8 MiB y heap cero no admiten deadline, thread de audio, otra plataforma,
VCO cargado por mixer activo, C4=100 pF ni render de voz completa. La
integración de cadena sigue pendiente: mínimos de paso y cargas comunes
necesitan contrato conjunto, sin duplicar R6/R45 ni sujetar pasos por fuerza.
