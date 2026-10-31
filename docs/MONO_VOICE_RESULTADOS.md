# Voz monofónica: API completa y coste medido

2026-10-31. [Protocolo](MONO_VOICE_PROTOCOLO.md),
[fuente](../crates/rf-d-circuit/src/monophonic_voice.rs),
[banco nativo](../evidence/mono_voice_native01.json),
[análisis](../evidence/mono_voice_analysis01.json) y
[QA](../evidence/mono_voice_tests01.json).

## Qué funciona

Una voz experimental por bloques, con DC propio, notas MIDI, prioridad
grave, legato, retorno a nota retenida, velocidad cero y AllNotesOff.
El KEY compartido gobierna los contornos físicos ya existentes de filtro
y volumen, ladder cargado, recuperación, dos VCA, J7 y FIR384/48 kHz.
Sin reemplazar contornos por una ADSR genérica o multiplicar la salida
por una envolvente independiente. Prioridad grave: SVC-204D PDF p.6;
orden de contactos/retención: p.16, como recoge HALLAZGOS. MIDI temperado,
velocidad ignorada y despacho por muestras son extensiones del host;
no se emulan aún los contactos físicos, glide o pitch bend.

Fuente: un VCO nominal transpuesto, dominio MIDI56..79 (207.65..783.99Hz),
fase continua. No es la familia calibrada H128 ni un Model D completo de
tres VCO. Patch fijo, 48 kHz, bloques1..128, hasta1000 s del reloj anterior;
estos límites de API no significan cobertura numérica de todo ese dominio.
El código es una entrada de ensamblaje de laboratorio, sin ABI/package de
RackForge y sin registro en la biblioteca congelada. No es un plugin RT.

La salida es causal, con48 muestras/1 ms de latencia y48 ceros iniciales.
Un Frame calculado justo al final se conserva para el bloque siguiente.
Eventos inválidos rechazan estado y audio completo, incluyendo ceros con
signo. El Workspace sólo es scratch; ninguna carga se reinicia al tocar.
Eventos por muestra se redondean hacia arriba <15.259 ps, con semipaso
>=MIN_DT físico del solver. No hay avance más allá del bloque conocido.

## Contraste y límites

Tres recorridos propios de10 ms: bloques64/.5 us,128/.5 us y64/.25 us;
otro recorrido con el productor anterior y el mismo programa de seis
eventos. Cada uno resuelve su DC. Coinciden los estados iniciales por bits.
Todos conservan Newton<=1 pA/2 nV y estimador<=1, sin heap medido.
Cuatro tests nuevos del controlador/reloj/fase;24 rechazos reales de API
en DC y al final de las tres trayectorias, con audio/estado intactos.
No se inyectó un fallo numérico interno: la atomicidad ante ese fallo
se apoya aquí en candidato local y publicación final, sin afirmar un
ensayo de agotamiento de Newton de la API nueva.

| Comparación | Error RMS relativo J7/FIR | Máximo nodal final | Gate nodal1 uV |
|---|---:|---:|---|
| Bloques64/128 | 2.6433e-6 | 6.029 uV | rechazado |
| Pasos .5/.25 us | 1.9384e-6 | 5.371 uV | rechazado |
| Productor anterior | 2.8570e-6 | .505 uV | pasa |

Audio pasa RMS .001, máximo/pico .003 y media1 uV, también por ventanas.
Aunque el pico de esta escena temprana es sólo .252 uV, se exigieron
las razones relativas en toda ventana posterior a KEY: el control de
audio cero es rechazado. Esta comprobación adicional es más estricta que
el fallback absoluto cercano a cero del protocolo. Antes de KEY se usa
absoluto1 uV. No normalización, WAV nuevo ni escucha promovida.

El gate nodal adicional de1 uV del analizador original falla en nodo76
(nodo21 en la numeración de circuit66). Fallo y replay sin cambios conservados:
no se relajó1 uV ni se admitió equivalencia estricta de todos los estados.
El análisis final informa por separado audio aceptado, estado estricto
rechazado y deadline rechazado. `passed` significa recibo/ensayo completo,
no admisión conjunta de esos tres resultados. Este bloque no sustituye
la voz activa anterior ni sus referencias eléctricas.

La escena comprueba despacho, dos gates y cambios legato; no contiene una
nota asentada o cola larga audible. La trayectoria anterior de300 ms y
su validación de contornos/FIR se heredan por identidad, sin contar otro
ensayo. Fuente nominal compartida: el productor no es otro oráculo VCO.

## Coste de toda la voz

Ryzen5 5600X, Windows11, seis núcleos/doce hilos, plan Alto rendimiento,
una voz en un hilo. rustc congelado, opt-level=2 genérico; rlib congelada,
stack32 MiB. Cronómetro fuera de render_block; sin IO en el intervalo.
Incluye candidato transaccional, circuito adaptativo, interpolación y FIR.
No se excluye el primer bloque ni se esconden cálculos en un prerender.

| Bloque / paso máximo | Tiempo para10 ms | Mediana bloque completo | Peor bloque | Presupuesto/bloque |
|---|---:|---:|---:|---:|
| 64 / .5 us | 47.0005 s | 6.4180 s | 6.6781 s | 1.3333 ms |
| 128 / .5 us | 44.5963 s | 12.3975 s | 12.4596 s | 2.6667 ms |
| 64 / .25 us | 92.6124 s | 12.7362 s | 13.5153 s | 1.3333 ms |

Todos los17 bloques completos medidos incumplen el deadline; parciales
se conservan aparte. La ruta .5 us tarda aproximadamente4460–4700 veces
la duración de audio. Con el objetivo de ocupar<=50% del presupuesto,
la mejora necesaria es aún mayor. Son observaciones cortas, no WCET,
benchmark estadístico independiente o garantía sobre otras máquinas.
El arranque DC separado tarda16.5–16.9 ms. Estado de voz11784 bytes,
Workspace279824 bytes, cero asignaciones en procesamiento.

La escena .5 us necesita20252–20580 avances, con una tentativa adaptativa
por avance. Las175707–177808 iteraciones contadas pertenecen a los tres
Radau aceptados (coarse y dos half), no a evaluaciones de line search.
El productor anterior también tarda46.281 s de proceso para10 ms, aunque
ese cronómetro incluye su IO; sirve como contraste de escala, no como
atribución precisa de overhead al wrapper MIDI.

## Proveniencia y decisión

Un chequeo de JSON falló porque ordenaba claves numéricas antes/después
de restaurarlas como strings. Se corrigió sólo la canonicalización.
El primer recibo fue sobrescrito accidentalmente por el segundo fallo:
se registra esa pérdida y se reconstruye su fuente por reversión exacta
del edit, sin fingir identidad histórica del recibo. El segundo fallo,
nodal, conserva fuente y replay originales. Ver
[incidencias](../evidence/mono_voice_corrections01.json).

Sin Cargo, biblioteca nueva, cache, SPICE, WAV o entradas privadas nuevas.
El único WAV anterior conserva su hash y tmp/lab-current queda vacío.

La API monofónica y el banco completo permiten medir el problema real.
**No admitir esta ruta en el hilo de audio.** El siguiente bloque debe
reducir el coste de la voz de producción con contraste contra este modelo
eléctrico; no dedicar otra serie a microoptimizaciones sin una expectativa
cuantificada. La familia H128 ya reduce el VCO; falta llevarla a la voz
con contornos y derivar un núcleo de filtro/VCA con sus puertos y memoria.
Conservar este circuito como referencia offline y mantener el rechazo
nodal1 uV abierto al contrastar nuevas representaciones.
