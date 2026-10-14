# Recorridos de ceros: identidad, memoria y costo rechazado

## Decisión

Dos variantes de laboratorio pasan números y fallan la utilidad fijada antes de medir. No se promueven. La voz pública, su biblioteca, los puertos, cargas, reloj y WAV de 68 ms siguen idénticos al bloque anterior. No hay duración ni audio nuevos.

| Variante | Ratio mediano | Peor ronda | Scratch solver referencia/candidato (bytes) | Gate ≤0,95 / ≤1,05 |
| --- | --- | --- | --- | --- |
| Soporte LU real + bloques nulos CSR | 1.00002962358 | 1.02748825664 | 459656 / 564144 | rechazo de mediana |
| Solo CSR por OR de bits sin signo | 0.977922928728 | 0.98505855027 | 459656 / 459656 | rechazo de mediana |

La primera añade 104488 bytes fijos y no mejora tiempo. La segunda reduce 2.207707 % del tiempo del banco, sin scratch adicional; el gate pide 5 %. No se reduce ese umbral después de observar el resultado. Cinco rondas alternadas por variante, mismo proceso, banco, flags y compiler congelado; la mediana es el cociente de medianas de tiempos agregados. Son resultados de este banco y equipo, no una garantía para cualquier escena ni un deadline.

## Identidad y alcance

Banco 168 pares: 78 anteriores y 90 coarse/mid/end seleccionados de las dos liberaciones extendidas propias. Se verifican 1834 f64 por par, counters de cada variante y 35471184 campos completos de stamp por bits. Los 24 pares nominales conservan counters históricos conocidos; los 144 pares seleccionados no adquieren retrospectivamente iteraciones/trials históricos, aunque las ejecuciones actuales sí se comparan por completo.

1280 fixtures directos por variante contrastan LU frente a las sustituciones densas originales: ±0, subnormales, extremos y overflow. 260 rechazos por variante coinciden. El control con matriz identidad/RHS −0 demuestra que omitir ceros sin atender al signo cambia bits; ambas variantes preservan el resultado denso. Seis fixtures de solver completo conservan clases de rechazo. Los métodos del circuito y sus puertas eléctricas son los anteriores; no se presenta este banco como un nuevo solve independiente de la red original.

La variante LU recoge soporte del factor real, conserva columnas en orden y ejecuta huecos cuando el acumulador es ±0. Comprueba finitud por fila; una fila no finita no puede recuperarse al dividir por una diagonal finita no nula. CSR1 omite solo grupos comparados iguales a cero; CSR2 usa OR u64 y máscara del signo, sin eliminar mantisa/exponente. Ambos respetan no nulos, NaN/Inf, capacidad, floor, suma y dirección de las conexiones. No se reemplaza el patrón real por un preset. Los helpers de acceso a LU privado pertenecen solo al laboratorio.

## Perfil de la familia pública actual

Un tercer ejecutable instrumenta la aritmética actual con los wrappers de reloj ya existentes, adaptados a `block_decay_voice/solver`; 168 pares y todos sus 1834 campos/counters coinciden con la referencia. Los relojes son **anidados**: las columnas siguientes no se suman para calcular costo total. No se resta overhead; el perfil cambia compilación y añade clocks/atomics de laboratorio, por lo que su tiempo frente al ejecutable sin instrumentar no se promociona como ganancia.

| Fase | Llamadas | Tiempo acumulado (ms) | Respecto de step instrumentado |
| --- | --- | --- | --- |
| step | 168 | 783.361000 | 100.0000 % |
| initialize | 618 | 431.863300 | 55.1295 % |
| parts | 1236 | 331.908500 | 42.3698 % |
| joint_parts | 1236 | 253.587800 | 32.3718 % |
| prepare | 618 | 259.103300 | 33.0758 % |
| factor64 | 1236 | 11.422800 | 1.4582 % |
| factor58 | 618 | 5.383800 | 0.6873 % |
| factor132 | 618 | 29.664900 | 3.7869 % |
| factor140 | 618 | 44.697700 | 5.7059 % |
| rhs64 | 13818 | 34.207600 | 4.3668 % |
| rhs58 | 1965 | 4.123000 | 0.5263 % |
| rhs132 | 3201 | 32.751000 | 4.1808 % |
| rhs140 | 729 | 8.687500 | 1.1090 % |
| support | 618 | 77.735200 | 9.9233 % |
| residual | 729 | 4.261800 | 0.5440 % |
| correction | 729 | 23.810400 | 3.0395 % |
| solve | 618 | 290.574400 | 37.0933 % |

El ensamblado `initialize` ocupa 55.1295 % del step e incluye `parts`; las leyes de `parts` ocupan 42.3698 %, incluyendo `joint_parts` 32.3718 %. El solve ocupa 37.0933 %. El CSR/support ocupa 9.9233 % y las cuatro sustituciones agregadas 10.1829 %, con llamadas desde prepare y correction. No sumar esos hijos con sus padres. El siguiente experimento debe atacar el ensamblado/`parts` o sus copias reales antes de ampliar el mismo detector de ceros.

## Evidencia

- [Protocolo previo](VOZ_CEROS_PROTOCOLO.md), [variante CSR aislada](VOZ_CEROS_SCAN_PROTOCOLO.md), [entradas propias](../evidence/voice_zero_inputs01.json).
- [LU + CSR medidos](../evidence/voice_zero_bench01.json), [CSR aislado medido](../evidence/voice_zero_scan01.json), [perfil actual](../evidence/voice_zero_profile01.json).
- [QA](../evidence/voice_zero_tests01.json). Los ejecutables, banco binario y productos privados quedan ignorados y protegidos por hashes; ninguna fuente/binario de los candidatos se sobrescribe.

Sin Cargo, nueva biblioteca, SPICE ni caché de compilación. Reserva 1 GiB y presupuesto nuevo 96 MiB. 255 tests Rust y dos definiciones Python heredados sin reejecución; los fixtures ejecutados aquí se contabilizan separados de esos tests. No se mide heap o deadline y no se admite RT, nueva fidelidad física ni nueva trayectoria independiente. Sigue disponible la escucha real anterior de 68 ms.
