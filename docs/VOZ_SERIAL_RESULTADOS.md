# Productor serial preparado y control de archivo admitido

2026-10-07. Implementa el [protocolo de archivo](VOZ_NOTA_LARGA_ARCHIVO_PROTOCOLO.md)
con el [contrato serial](VOZ_SERIAL_IMPLEMENTACION.md). Se conservan las
fuentes y recibos congelados del [control binario anterior](VOZ_EXPORT_BINARIO_RESULTADOS.md).

## Implementación y comprobaciones

El productor ejecuta Gear500→Gear250→Gear125→Trap125 desde DC propio,
una escena por vez. Usa build11 y el runner binario congelados, con 7200 s
por proceso, 350 ms y teclado ON 10 ms/OFF 200 ms. La implementación incluye
preflight numerado, recursos antes de cada escena, manifiestos de archivo,
restauración exacta, medidas y tres contrastes largos originales. El auditor
del banco queda implementado para esa futura campaña; aún no tiene un banco
largo nuevo que auditar.

Doce [regresiones ejecutadas](../evidence/voice_serial_regression01.json)
pasan: ambos codecs, fallo del consumidor, cambio del temporal, corrupción,
recibo incorrecto, verificación fallida, intentos existentes, rutas exactas,
hardlinks, redirección del manifiesto, aritmética del pico, escenas incompletas
y separación de faltas de almacenamiento/recursos frente a fallos eléctricos.
Al fallar una operación se conservan sus archivos. Ningún prefijo incompleto
se convierte en cobertura completa o comparación medida.

## Control con export real: copias nuevas

El [control de almacenamiento](../evidence/voice_serial_storage_control01.json)
copia el raw y recibo del control nativo ya admitido a dos carpetas nuevas,
una por codec. Archiva cada copia, verifica todos los bytes restaurados,
retira sólo esa copia intermedia y vuelve a restaurarla para leer sus valores.
El manifiesto enlaza recibo, raw original lógico y contenedor por hash/tamaño.

| Codec | Archivo conservado | Valores comparados | Diferencias de bits | Copia/temporal retirados |
| --- | ---: | ---: | ---: | --- |
| gzip9 | 20473174 bytes | 3642566 | 0 | Sí, con identidad verificada |
| XZ6/CRC64 | 16234580 bytes | 3642566 | 0 | Sí, con identidad verificada |

La [auditoría](../evidence/voice_serial_storage_validation01.json) repite
restauración, layout, bits y retiro del temporal. Verifica que los originales
ASCII/raw/recibo históricos permanecen idénticos antes y después. Se conservan
contenedores, manifiestos y recibos de las copias nuevas. No hay solves ni
compilaciones adicionales: son operaciones de almacenamiento sobre datos
ya medidos. El control también comprueba el cierre de handles en Windows.

## Nuevo presupuesto y extensión pendiente

El [preflight serial 01](../evidence/voice_serial_preflight01.json) recalcula
con la disponibilidad posterior al control. Su
[auditoría de aritmética](../evidence/voice_serial_preflight_validation01.json)
pasa; la decisión de recursos es **rechazada** para ambos codecs.

| Codec | Requeridos | Disponibles registrados | Déficit |
| --- | ---: | ---: | ---: |
| gzip9 | 3905525222 | 3508764672 | 396760550 |
| XZ6/CRC64 | 3658422626 | 3508764672 | 149657954 |

El presupuesto conserva el mayor intermedio y 2 GiB de margen, sin contar
dos veces archivos ya escritos al avanzar la campaña. La densidad y filas
estimadas no son cotas. El preflight rechazado se conserva; no se reescribe
cuando cambie el espacio libre.

La [QA de publicación](../evidence/voice_serial_tests01.json) valida las doce
ejecuciones capturadas y hereda 153 por identidad de sus entradas: **165
cubiertas**, sin volver a ejecutar o contabilizar esas 153 como nuevas.
Sólo cambian las tres portadas de estado entre los inputs anteriores.

El banco largo con seis sigue **no medido**, no rechazado eléctricamente.
No existe su carpeta de producción ni se genera audio nuevo. El siguiente
intento, después de disponer de recursos suficientes, usa:

```powershell
python -B tools/voice_serial_long.py --preflight 2 --run
```

El comando vuelve a verificar espacio y QA antes de iniciar SPICE; si falla
el gate deja otro preflight y no ejecuta escenas. La admisión de almacenamiento
no identifica una unidad vintage, no completa otras notas y no admite RT.
