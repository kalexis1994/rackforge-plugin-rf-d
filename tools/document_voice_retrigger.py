"""Append measured retrigger results without rewriting historic document bytes."""
import base64,json
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require,TICK
from prepare_voice_retrigger import START,BOUNDARIES
def main():
 native,ref,audio,cli=[json.loads((ROOT/f'evidence/voice_retrigger_{n}{2 if n=="cli" else 1:02d}.json').read_text(encoding='utf8')) for n in ['native','reference','listening','cli']];require(all(r['passed'] for r in [native,ref,audio,cli]),'measured gates before documentation');rows=[]
 for p in ref['profiles']:
  for phase in p['phases']:
   v=phase['final_voltages_v'];rows.append(f"| {p['maximum_half_ticks']} | {phase['phase']} | {phase['accepted_steps']} | {v['C2']:.12g} | {v['LOUDNESS']:.12g} | {v['J7']:.12g} |")
 failed=json.loads((ROOT/'evidence/voice_retrigger_cli01.json').read_text(encoding='utf8'));size=sum(o['bytes'] for o in native['outputs']+cli['outputs']+audio['files']+failed['outputs']);require(size<=96*1024**2,'finite output budget')
 voltage=max(p['max_voltage_error_v'] for p in ref['same_clock_refinement']);ratio=max(p['gate_ratio'] for p in ref['same_clock_refinement'])
 fine=ref['flux_checks'][1];turn=next(e for e in fine['events'] if e['kind']=='TURN');off=START+BOUNDARIES[2];turn_delay_ms=(float(turn['interpolated_time_s'])-off*TICK)*1000
 report=f'''# Retrigger cargado: segunda pulsación con memoria

## Escena y procedencia

Continuación de cada final propio a 140,442 ms, biblioteca assembly congelada SHA256 `{sha(ROOT/'references-local/voice-assembly-public01/librf_d_circuit.rlib')}`. Se conserva decay ON/R16 1 kΩ, oscilador CA3046 y las cargas del BUS, escalera, VCA y J7. No se recompila la biblioteca. Se aplican 4 µs de continuidad, KEY 10 V/S cerrado durante 8 ms y KEY 0 V/S abierto durante 8 ms. Final 156,446 ms: 16,004 ms nuevos, historia unida 148,008 ms desde 8,438 ms.

Gatillo de contorno, con CV de oscilador fijo; niveles/contactos y parámetros heredados de [la receta](RECETA_CONDICIONADA_PROTOCOLO.md). Duraciones elegidas como estímulo de laboratorio. Es una segunda pulsación con memoria de una historia condicionada, sin arranque desde silencio ni control MIDI calibrado.

Los dos eventos por resolución conservan 458 HIGH/LOW, resistencia, reloj y propuesta por bits. Cuatro avances después de cada evento coinciden íntegramente con la familia block anterior: 16 Accepted pareados, además de ocho en la unión inicial. Los checkpoints antes/después permiten verificar la operación separadamente de su respuesta eléctrica posterior.

| Semipaso máximo (ticks) | Fase (0 reposo, 1 gate, 2 release) | Accepted | C2 final (V) | Loudness final (V) | J7 final (V) |
| --- | --- | --- | --- | --- | --- |
{chr(10).join(rows)}

C2 continúa creciendo después de soltar KEY antes de iniciar su descenso: máximo muestreado {fine['sampled_c2_max_v']:.12g} V; cambio de signo interpolado {turn_delay_ms:.12g} ms después del evento OFF. Se observan dos conmutaciones del biestable en cada resolución. Esta respuesta pertenece al modelo y a la historia cargada declarados; no se identifica como tiempo de panel o medición de un instrumento físico.

## Validación propia

{ref['accepted_steps']} Accepted y {ref['fine_steps']} endpoints finos; {ref['independent_candidates']} candidatos y {ref['independent_nonlinear_rows']} ecuaciones seleccionadas nuevas frente al grafo original, diferencias finitas y cargas Decimal100. Se mantienen KCL 20 pA, restricciones 200 pA, correcciones 1 µV/1 nA. Cobertura seleccionada en coarse/mid/end de los bordes, resets y transiciones; los demás endpoints no reciben solve independiente original por herencia.

22 relojes comunes de 229 estados, error máximo {voltage:.12g} V, ratio de puerta {ratio:.12g}. {sum(len(p['resets']) for p in ref['profiles'])} resets y {sum(len(p['events']) for p in ref['flux_checks'])} TURN/LATCH observados pasan las puertas interpoladas de 10/100 ns. {sum(p['records'] for p in ref['flux_checks'])} flujos C2 completos; balance máximo de derivada {max(p['max_derivative_balance_error_v_per_s'] for p in ref['flux_checks']):.12g} V/s. Cada corriente conectada, seguidor y retorno permanece en el balance.

Nueve filas ΔQ orientadas pasan por fase, total y unión desde 8,438 ms, puerta 1 pA×duración. La cuadratura de todos los estadios sigue siendo nativa; componentes seleccionados se contrastan en Decimal100. {ref['restores']} restores reproducen {ref['replayed_accepted_steps']} Accepted completos por bits, máximo {ref['maximum_active_replay_probes']} motores sombra. Ocho corrupciones y dos destinos inválidos rechazados atómicamente.

## Escucha y reproducción

Dos WAV mono PCM16, 7104 muestras a 48 kHz: 148 ms reales. Se unen seis trazas, con las primeras cuatro familias originales y los dos tramos assembly atribuidos explícitamente. Uniones por estado completo, receta y endpoint único; eventos con clocks enteros y checkpoints antes/después. Sinc 18 kHz/Blackman, escala 0,01 V/FS y DC conservados. Sin loop, fades o normalización; ocho µs finales fuera del WAV por su rejilla, extensión constante sólo en bordes del filtro.

Dos derivaciones completas idénticas. Diferencia entre resoluciones {audio['native_resolution_max_error_v']:.12g} V y {audio['native_resolution_max_pcm_lsb']} LSB, puertas 2 µV/7 LSB.

- `artifacts/voice-retrigger01/rf-d-j7-retrigger-148ms-1048576-nativo.wav`
- `artifacts/voice-retrigger01/rf-d-j7-retrigger-148ms-524288-nativo.wav`

CLI desde la raíz, con entradas propias presentes y salida nueva:

```powershell
python -B tools/retrigger_render_cli.py --held references-local/sustained-voice01/524288/selected.txt --release references-local/release-voice01/524288/selected.txt --controlled references-local/decay-voice02/524288/selected.txt --extended references-local/extended-release01/524288/selected.txt --tail references-local/long-tail01/524288/selected.txt --retrigger references-local/voice-retrigger01/524288/selected.txt --output artifacts/escucha-retrigger.wav
```

Sidecar con las 17 entradas realmente leídas, código importado, clocks, familias y dos eventos. Cuatro integraciones pasan: WAV/sidecar completos idénticos, protección de salida existente y rechazo previo de unión incompatible/traza incompleta.

La primera campaña CLI produjo el WAV correcto pero su fixture de unión incompatible omitió los cuatro checkpoints de eventos. La CLI rechazó primero la entrada faltante, por lo que no alcanzó el rechazo específico esperado. Se conservan [fuente y fallo](../evidence/voice_retrigger_cli01.json), [replay exacto sin cambios](../evidence/voice_retrigger_cli_replay01.json) y [reparación del fixture](../evidence/voice_retrigger_cli_repair01.json). El segundo intento completa esos checkpoints en un directorio nuevo y reejecuta las cuatro puertas idénticas; circuito, render y datos nativos permanecen sin cambios.

## Evidencia y siguiente bloque

[Protocolo](VOZ_RETRIGGER_PROTOCOLO.md), [entradas](../evidence/voice_retrigger_inputs01.json), [nativo](../evidence/voice_retrigger_native01.json), [grafo original y memoria](../evidence/voice_retrigger_reference01.json), [audio](../evidence/voice_retrigger_listening01.json), [CLI](../evidence/voice_retrigger_cli02.json), [QA](../evidence/voice_retrigger_tests01.json).

Campaña nativa {native['wall_s']:.6f} s, auditor {ref['wall_s']:.6f} s; privados nuevos {size} bytes dentro de 96 MiB. Sin Cargo/cache, SPICE o biblioteca nuevos. Stack offline 32 MiB, IO y replay de laboratorio. 255 tests Rust y dos definiciones Python heredados sin reejecución; campañas e integraciones nuevas se contabilizan aparte. Sin fidelidad física, voz completa desde silencio, periodicidad, heap/deadline o RT admitidos.

Siguiente: ampliar la escena de control y su duración con una pregunta musical concreta, manteniendo historia propia y contraste del contorno cargado. No usar una onda impuesta ni reiniciar capacitores para facilitar el gatillo.
'''
 p=ROOT/'docs/VOZ_RETRIGGER_RESULTADOS.md';require(not p.exists(),'exclusive measured report');p.write_text(report,encoding='utf8',newline='\n');before=json.loads((ROOT/'evidence/voice_retrigger_before01.json').read_text(encoding='utf8'));saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
 append=f'''\n\nEl [retrigger con memoria propia](docs/VOZ_RETRIGGER_RESULTADOS.md)
añade 16,004 ms: segundo gatillo de 8 ms y liberación de 8 ms sin borrar cargas.
Dos eventos por resolución conservan 458 HIGH/LOW, resistencia, clock y propuesta;
16 Accepted posteriores pareados por bits con block, además de ocho de unión.
{ref['independent_nonlinear_rows']} ecuaciones seleccionadas nuevas, 22 relojes de
229 estados y nueve balances por fase/total/unión pasan. Dos WAV reales de 148 ms,
17 entradas/código identificados y cuatro integraciones CLI. Sin fidelidad física
o RT; la historia inicial sigue condicionada. [QA](evidence/voice_retrigger_tests01.json).
'''.encode('utf8')
 for n in ['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:
  require((ROOT/n).read_bytes()==saved[n],'historical bytes before append');prefix=saved[n].replace(b'voice_tail_tests01.json',b'voice_retrigger_tests01.json') if n=='README.md' else saved[n];tail=append if n=='README.md' else append.replace(b'(docs/VOZ_RETRIGGER_RESULTADOS.md)',b'(VOZ_RETRIGGER_RESULTADOS.md)').replace(b'(evidence/voice_retrigger_tests01.json)',b'(../evidence/voice_retrigger_tests01.json)');(ROOT/n).write_bytes(prefix+tail)
 print('RETRIGGER_DOCUMENTED',size)
if __name__=='__main__':main()
