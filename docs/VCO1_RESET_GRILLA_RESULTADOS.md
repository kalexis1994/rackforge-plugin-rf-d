# Reset: grilla más fina y segundo límite confirmado

2026-10-08. Base 236f170. [Protocolo](VCO1_RESET_GRILLA_PROTOCOLO.md). Este bloque es un diagnóstico condicional privado; no modifica el motor Rust de producción, circuito, parámetros o gates. La [QA](../evidence/voice_vco1_reset_grid_tests01.json) conserva 235 tests heredados por identidad; no se añaden ni reejecutan tests unitarios. Se contrastan 22 raíces de diagnóstico con Decimal100.

## Adaptador

El [intento 01](../evidence/voice_vco1_reset_grid01.json) no compiló por visibilidad pub(crate) del solver. Se conserva la compilación repetida y los bytes medidos. La [corrección del adaptador](VCO1_RESET_GRILLA_ADAPTADOR.md) copia literalmente las funciones de eliminación previas a un módulo privado; el publicador verifica los bytes. El [intento 02](../evidence/voice_vco1_reset_grid02.json) usa una copia del núcleo con único cambio MIN_DT y un controlador con binding, máximo de ticks y presupuesto declarados. Misma pila de laboratorio 8 MiB, compiler O2, gates 2 µV/2 nA y Newton 64/24.

## Primer intervalo

Desde la historia del rechazo original, cinco tríos full/mid/end coinciden con leyes e incidencias Decimal100. La referencia inicia desde la historia y su propio mid, nunca desde raíces actuales nativas.

| Medio paso | Ratio de error local independiente | Fila limitante |
|---|---:|---|
| 30,517578125 ps | 1,0065511571 — rechazo | Q6 colector |
| 15,2587890625 ps | 0,2489874995 | Q6 colector |
| 7,62939453125 ps | 0,0619079682 | Q6 colector |
| 3,814697265625 ps | 0,0154340991 | Q6 colector |
| 1,9073486328125 ps | 0,0038531282 | Q6 colector |

Las 15 raíces pasan KCL, masa y contraste; error nodal máximo 3,41124e-12 V. La subdivisión recupera **este** intervalo y confirma su origen temporal. No demuestra que el piso elegido cubra el reset completo.

## Continuación condicionada y rechazo

La copia privada intentó 50 µs desde la historia, pero rechazó tras **188,88092041015625 ns**, 32.300 pasos aceptados, 32.301 filas de 274 columnas. Es sólo un prefijo, a tiempo absoluto 2,43452701568603515625 ms. Las filas guardan reloj entero, dt real, residual/corrección/error/intentos y todos los pares hi/lo. Pasos reales 1,9073486328125..30,517578125 ps. Máximo error aceptado 0,999973477. Original y replay byte idénticos; sin error de recursos o timeout. No se ejecutó otra ampliación de dominio ni recorrido.

Cuatro intervalos aceptados — primero, último y los dos de mayor cambio nodal — se resolvieron independientemente con Decimal100 desde sus historias exportadas. Todos pasan; máximo error nodal 1,12081e-12 V. Son contrastes locales de estados condicionales; no una trayectoria independiente global.

El [segundo diagnóstico](../evidence/voice_vco1_reset_grid_floor01.json), con [protocolo](VCO1_RESET_SEGUNDO_PISO_PROTOCOLO.md), usa exactamente la misma copia congelada y su mínimo dt. Las tres raíces full/mid/end cumplen residual/corrección y contrastan hasta 1,67414e-11 V con Decimal100. La incógnita limitante ahora es **XIC3.7, índice 81**, nodo interno del macromodelo del 741 de referencia. Full menos endpoint = **2,0052609348367814 µV**, ratio 1,0026304674 > 1. Se confirma el nuevo rechazo temporal; no se atribuye a redondeo ni a falta de raíces en este intervalo.

## Decisión siguiente

La grilla por sí sola no resuelve el alcance completo: más de 32.000 pasos sólo cubren 189 ns y aparece un nuevo piso. Analizar la dinámica rápida y la discretización del macromodelo 741 antes de extender otra vez el dominio o lanzar ciclos completos. Cualquier cambio de integración debe conservar cargas, retornos, leyes, gates y contraste independiente. Este diagnóstico no demuestra por sí solo la causa física de la dinámica rápida ni autoriza reducir el macromodelo.

Siguen sin admisión ciclos estacionarios, frecuencia/refinamiento, calibración temporal, cierre con mixer, voz, audio nuevo, física y RT. Cero SPICE nuevos. Recursos, fuentes, fallos y copias privadas permanecen protegidos por hash.
