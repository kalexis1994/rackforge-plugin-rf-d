# Nota larga serial: campaña cerrada

2026-10-07. VCO1 CA3046, mezclador, filtro/VCAs/salida y contorno de
laboratorio; candidato activo de seis correcciones. Perfil condicionado,
sin unidad física de referencia. [Protocolo congelado](VOZ_NOTA_LARGA_ARCHIVO_PROTOCOLO.md)
y [productor serial](VOZ_SERIAL_IMPLEMENTACION.md).

## Cobertura y decisión

[Recibo del banco](../evidence/voice_serial_runs01.json): cuatro procesos,
DC propio, 350 ms solicitados, ON a 10 ms y OFF a 200 ms. Gear2/Trap2,
máximos de paso 500/250/125 ns y 7200 s por proceso. Física y gates intactos.

| Escena | Filas | Último reloj (ms) | Resultado | Proceso (s) |
| --- | --- | --- | --- | --- |
| nominal500 | 649113 | 136.630269424749 | Aborto eléctrico | 798.403 |
| nominal250 | 1000821 | 150.293268353277 | Aborto eléctrico | 1203.925 |
| nominal125 | 3703552 | 350.000000000000 | Completa | 4409.839 |
| nominal-trap125 | 155680 | 15.940420728990 | Aborto eléctrico | 182.517 |

**Banco largo rechazado: una de cuatro escenas completa.** Los tres abortos
conservan sus fallos y prefijos. El exit code 0 de ngspice en esas escenas
no equivale a completar el reloj. Las parejas 500→250, 250→125 y
Gear125→Trap125 quedan no medidas por falta de ambas escenas completas.
No se relajan gates ni se genera audio nuevo.

## Gear125 completo

- Frecuencia: 439.142276620584 Hz.
- Dispersión relativa de periodo: 9.13651835359e-07.
- Balance máximo del contorno: 0.170263592308 pC.
- Balance máximo de salida: 0.003552578941 pC.
- Límite de carga: 100 pC. Rest/attack/held/release tienen cobertura completa.

Las métricas íntegras constan en el recibo. Validan esta trayectoria
condicionada; no las parejas ausentes o parámetros de un instrumento real.

## Archivo y auditoría

[Preflight02](../evidence/voice_serial_preflight02.json) admitió XZ/un worker.
Las cuatro trazas conservan sus recibos originales privados, decks, logs y
manifiestos. Los contenedores restauran el export completo por bytes/hash;
se retiraron sólo los intermedios nuevos tras verificar el archivo. No
hubo rechazo de recursos ni error de almacenamiento.

El [auditor congelado](../evidence/voice_serial_validation01.json) restauró
los cuatro recibos y recompuso mediciones/comparaciones. La
[ejecución capturada](../evidence/voice_serial_audit_run01.json) pasó sin
reparar el auditor, lanzar SPICE o recompilar. La
[QA inicial del banco](../evidence/voice_serial_release01.json) conserva el
estado previo a actualizar las portadas. El primer escritor documental
intentó un nombre ya ocupado; su creación exclusiva lo rechazó antes de
modificar el resultado histórico de almacenamiento/preflight01, que sigue
en [VOZ_SERIAL_RESULTADOS](VOZ_SERIAL_RESULTADOS.md). Este documento nuevo
registra la campaña. La [QA final](../evidence/voice_serial_release02.json)
comprueba fuentes, archivos privados, errores eléctricos y decisión;
hereda los 185 controles nativos sin volver a ejecutarlos o admitir el banco.

Los diagnósticos [Gear500](../evidence/voice_serial_prefix_nominal50001.json)
y [Gear250](../evidence/voice_serial_prefix_nominal25001.json) conservan el
reloj anterior con diferencias diminutas en tres columnas. La
[auditoría decimal](../evidence/voice_serial_prefix_decimal01.json) refuta un
error de parseo en los valores cotejados. Ninguno identifica la causa total
de los abortos; un dispositivo nombrado en el log no basta para atribuirla.

## Próximo bloque

[VCO1 nativo con carga cerrada](VCO1_NATIVO_PROTOCOLO.md). Primero verificar
el stamp directo Q29/C27 y el dominio temporal común con la cadena. Luego
conservar cargas/estados de dispositivos y contrastar el oscilador completo.
No aumentar correcciones lineales o cambiar física por tanteo. VCO2/3,
contornos integrados, fuentes restantes, antialias y plazo RT siguen abiertos.
