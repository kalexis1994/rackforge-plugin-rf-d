# ON/C27 cerrado con la cadena nativa hasta J7

El [módulo nativo](../crates/rf-d-circuit/src/mixer_chain66.rs) inserta el
puerto de entrada dinámico en la cadena de 66 nodos. Elimina BUS y cierra
C27 con Q29, ladder, recuperación, ambos VCAs y salidas J4/J5/J7 en la
misma solución. Fuentes de tensión impuestas; no es un VCO nativo ni
una envolvente completa. El [protocolo](MEZCLADOR_CADENA_PROTOCOLO.md)
conserva fuentes, hipótesis, dominio y gates previos.

## Qué se mantiene y qué cambia

Los 66 nodos, leyes y memorias de `circuit66` permanecen intactos. El
adaptador sustituye sólo el stamp fijo de C27 en fila6 por la corriente y
tangente de ON/C27 reducido. `dt` admite **0,5 µs..1 ms**: la resta de
conductancias del adaptador no acredita pasos arbitrariamente pequeños.
Newton natural conserva las cargas originales durante predictor, fallback
y búsqueda de paso. Requiere KCL <10 pA, constraints <10 pV y corrección
Newton completa <10 nV. Sólo confirma el estado conjunto final; cualquier
fallo deja el estado del llamador intacto. No se interpola una fuente ni se
avanza la historia para conseguir una raíz.

## Evidencia ejecutada

El [oráculo](../tools/mixer_chain_vectors.py) monta explícitamente BUS y
cursores junto a los 66 nodos. Son sistemas de **67 y 71 incógnitas**,
con Jacobiano FD, DC y trayectoria propios. Ambos candidatos R61, sólo
OSC1 o cinco rutas ON, α=0,5, 16 pasos por escena a 48 kHz: **64 pasos**.
No toma tensiones nativas como semillas. El primer resultado y su
[replay ligado antes/después](../evidence/voice_mixer_chain_vectors_validation01.json)
se conservan; éste verifica también los inputs de la QA anterior.

El [ensayo de laboratorio](../evidence/voice_mixer_chain_native_attempt01.json)
compila una raíz que referencia módulos de producción por rutas explícitas.
Tras comprobarla, se agrega el export público y se compila la raíz real:
[ensayo de producción](../evidence/voice_mixer_chain_production01.json).
Las tres regresiones de circuito se repiten sobre esa biblioteca y se
añade un test aislado de heap. Son **cuatro tests nuevos cubiertos**;
las tres ejecuciones de laboratorio no se suman otra vez como cobertura.

| Magnitud | Máximo medido | Gate |
|---|---:|---:|
| Error de nodo | 1,012471884109800×10⁻⁹ V | 10⁻⁶ V |
| Error de corriente de puerto | 2,242667111588582×10⁻¹⁵ A | 10⁻⁹ A |
| Heap en cadena completa | 0 asignaciones, 32 pasos | 0 |

Se contrastan las 66 tensiones, BUS, 17 cargas y C10, corrientes del
puerto, J4/J5/J7 y balance C27 en cada paso. En cuatro estados no triviales
se verifican las 66 columnas del Jacobiano con historia fija; el test de
fallo conserva todo el estado. La preparación inicial falló por no crear
la carpeta de fragments de laboratorio: se conserva el
[snapshot y replay sin cambios](../evidence/voice_mixer_chain_preparation_rejection01.json),
anterior a compiler o SPICE. La corrección sólo crea esa carpeta.

La [QA](../evidence/voice_mixer_chain_tests01.json) cubre **182**: cuatro
tests de producción nuevos y 178 heredados por identidad. Conserva fuentes,
compiler, flags, raíces y binarios de ambos ensayos; no se retiran campañas
anteriores. No hubo nuevos solves SPICE por este bloque.

## Alcance y avance pendiente

Admitida localmente la cadena nominal con mezcla ON cargada y C27
dinámico, en las cuatro escenas fijadas. Los generadores siguen impuestos,
el contorno nativo no está integrado y no se admiten OFF, taper, parámetros
físicos, otras notas, audio nuevo o deadlines. Heap cero no mide RT.

La campaña monolítica SPICE sigue independiente. La primera escena se
detuvo a 136,630269 ms y se archivó completa como rechazo. El
[diagnóstico del prefijo](../evidence/voice_serial_prefix_nominal50001.json)
conserva reloj y 15 voltajes bit a bit frente al build anterior; las otras
tres columnas cambian hasta 4,2351647363×10⁻²² V. La
[auditoría decimal](../evidence/voice_serial_prefix_decimal01.json) confirma
que esas diferencias no provienen del parser. No hay equivalencia bit a
bit global, cobertura de los 350 ms ni causa identificada del aborto.
El primer error de ruta del diagnóstico se conserva con su
[snapshot/replay](../evidence/voice_serial_prefix_rejection01.json).

Próxima integración: cerrar fuentes VCO reales y sus cargas con esta
cadena, usando las referencias de oscilador existentes. El resultado de
las cuatro notas monolíticas se publicará al finalizar su auditoría.
