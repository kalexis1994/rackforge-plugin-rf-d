"""Publish measured direct assembly scope and append history by bytes."""
import base64,json
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
def main():
 lab,pub,native,ref=[json.loads((ROOT/f'evidence/{n}.json').read_text(encoding='utf8')) for n in ['voice_assembly_lab03','voice_assembly_public01','voice_assembly_paired01','voice_assembly_reference01']];require(all(x['passed'] for x in [lab,pub,native,ref]) and lab['cost_utility_passed'] and pub['cost_utility_passed'],'admitted measured blocks');ratio=sum(p['candidate_kernel_ns'] for p in ref['profiles'])/sum(p['baseline_kernel_ns'] for p in ref['profiles']);lib='references-local/voice-assembly-public01/librf_d_circuit.rlib'
 report=f'''# Ensamblado directo de la voz: familia pública

## Transformación y alcance

La familia `assembly_decay_voice/engine` evita crear un Parts200 intermedio y copiarlo a Parts229. El constructor de parámetros, validaciones, VCO134, cadena68, sus dispositivos, orden de sumas/restas, masa, puertos y contorno son los mismos. BUS12 pertenece a ambos bloques en el mismo solve. La comprobación de finitud del bloque200 precede al contorno. No se fusionan ni omiten operaciones con coeficientes nulos; no cambian parámetros audibles ni discretización. Las familias anteriores permanecen intactas.

Modelo documental vintage CA3046, escena propia condicionada OSC1→BUS→escalera/VCA/J7, KEY0/S abierto/decay ON/R1 kΩ, más los pares nominales R100 kΩ del banco. Revisión y cargas heredadas de `OBJETIVO.md` y `DECAY_CONTROL_PROTOCOLO.md`. Esta comparación no identifica una unidad física ni cubre todas las escenas posibles del Model D.

## Banco de laboratorio y biblioteca pública

168 pares propios. 336 Parts completos (35548128 f64) y168 stamps (35471184 f64) coinciden por bits: **71019312 campos** en total. Además1834 f64 por solve, iteraciones/trials actuales y los counters históricos de24 pares nominales. Doce entradas inválidas de Parts y seis fixtures de solver completo conservan sus rechazos. Se preservan tanto HIGH como LOW, cargas/h, DC, tangentes y candidatos.

| Ejecución | Ratio de medianas | Peor ronda | Utilidad ≤0,95 / ≤1,05 |
| --- | --- | --- | --- |
| Laboratorio | {lab['median_ratio']:.12g} | {lab['worst_round_ratio']:.12g} | admitida |
| Biblioteca pública | {pub['median_ratio']:.12g} | {pub['worst_round_ratio']:.12g} | admitida |

La API pública reduce el tiempo del banco {(1-pub['median_ratio'])*100:.6f} %. Cinco rondas alternadas por cada ejecución, mismos inputs/compiler/flags. Workspace de ambas versiones3378208 bytes, sin almacenamiento persistente añadido. El contenedor de200 nodos deja de aparecer en esta ruta; no se infiere de ello un pico de stack/RAM medido ni deadline. Los porcentajes corresponden a este banco y equipo.

Biblioteca `{lib}`, SHA256 `{sha(ROOT/lib)}`; compiler y comandos en [recibo público](../evidence/voice_assembly_public01.json). La primera preparación del laboratorio encontró dos restricciones de acceso a helpers privados. Cada rechazo y replay sin cambios queda conservado en lab01/lab02; reparaciones01/02 corrigen únicamente el binding de laboratorio y el selector de entradas. La copia local de `joint_vco_fine` difiere en dos rutas de importación/datos; su linearize físico no cambia. La familia pública llama al helper original privado de la crate. No se modifica la aritmética para reparar la compilación.

## Trayectoria pública pareada

Dos perfiles1/2 µs,4 ms cada uno:68,442→72,442 ms, desde sus checkpoints propios de la liberación extendida. {ref['accepted_steps']} Accepted completos y{ref['fine_endpoints']} endpoints coinciden por bits entre motores: coarse/mid/end, estados/incrementos, ratios, iteraciones/trials, LTE/intentos, observaciones, relojes y propuesta. Las doce rejillas con458 valores y los checkpoints finales coinciden por bytes. Los cuatro destinos inválidos se rechazan sin mutación (dos familias por perfil).

Todo STEP/OBS/GRID coincide también con el intervalo anterior admitido, no solo con el candidato. Nueve integrales orientadas pasan identidad de suma y ΔQ Decimal100 entre extremos propios. {ref['inherited_independent_nonlinear_rows']} ecuaciones seleccionadas independientes se heredan de ese intervalo por identidad; ninguna se reejecuta aquí contra el grafo original. No atribuir ese solve a todos los endpoints.

Ratio agregado del kernel pareado {ratio:.12g}: reducción{(1-ratio)*100:.6f} %, excluyendo IO, serialización y ledger. No es un deadline. La campaña completa dura{native['wall_s']:.6f} s, incluyendo sus comprobaciones. No suma duración de circuito y no produce un nuevo WAV68 ms entero del candidato. La escucha anterior sigue disponible e identificada como anterior.

## Evidencia y siguiente bloque

- [Protocolo previo](VOZ_ENSAMBLADO_PROTOCOLO.md), [entradas reparadas](../evidence/voice_assembly_inputs03.json).
- [Laboratorio](../evidence/voice_assembly_lab03.json), [preparación pública](../evidence/voice_assembly_promotion01.json), [banco público](../evidence/voice_assembly_public01.json).
- [Recorrido](../evidence/voice_assembly_paired01.json), [intervalo anterior y carga](../evidence/voice_assembly_reference01.json), [QA](../evidence/voice_assembly_tests01.json).
- Fallos/replays [lab01](../evidence/voice_assembly_lab01.json)/[lab02](../evidence/voice_assembly_lab02.json), [reparación01](../evidence/voice_assembly_repair01.json)/[reparación02](../evidence/voice_assembly_repair02.json).

Datos y binarios privados ignorados, con presupuesto96 MiB y reserva1 GiB. Sin Cargo/cache ni SPICE nuevos; solo una biblioteca nueva medida y callers de laboratorio. 255 tests Rust y dos definiciones Python heredados sin reejecución; los fixtures y campañas de este bloque tienen conteo propio. Sin heap/deadline nuevos, fidelidad física o RT admitidos.

Siguiente: ampliar la duración real con esta familia desde estados propios, conservando el contraste de cargas, eventos y contorno. No prolongar el WAV anterior por repetición ni cambiar parámetros eléctricos para acelerar el cálculo.
'''
 out=ROOT/'docs/VOZ_ENSAMBLADO_RESULTADOS.md';require(not out.exists(),'exclusive measured report');out.write_text(report,encoding='utf8',newline='\n');before=json.loads((ROOT/'evidence/voice_assembly_before01.json').read_text(encoding='utf8'));saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()};append=f'''\n\nEl [ensamblado directo público](docs/VOZ_ENSAMBLADO_RESULTADOS.md) evita
el contenedor200 y su copia a229, conservando constructor, validaciones,
sumas, masa, contorno y puertos.71019312 campos Parts/stamp por bits en168
pares; API pública ratio{pub['median_ratio']:.9f} y workspace3378208 igual.
{ref['accepted_steps']} Accepted completos/12 rejillas y nueve balances
coinciden en4 ms propios por resolución,68.442→72.442 ms; kernel ratio
{ratio:.9f}. {ref['inherited_independent_nonlinear_rows']} ecuaciones originales
heredadas por identidad,0 nuevas. Fallos de binding/replays conservados.
Sin duración/WAV nuevos, heap/deadline o RT. Siguiente duración útil propia.
'''.encode('utf8')
 for n in ['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:
  require((ROOT/n).read_bytes()==saved[n],'historic doc untouched');prefix=saved[n].replace(b'voice_zero_tests01.json',b'voice_assembly_tests01.json') if n=='README.md' else saved[n];tail=append if n=='README.md' else append.replace(b'(docs/VOZ_ENSAMBLADO_RESULTADOS.md)',b'(VOZ_ENSAMBLADO_RESULTADOS.md)');(ROOT/n).write_bytes(prefix+tail)
 print('ASSEMBLY_DOCUMENTED',ref['accepted_steps'],ratio)
if __name__=='__main__':main()
