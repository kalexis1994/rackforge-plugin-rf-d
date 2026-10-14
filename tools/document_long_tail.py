"""Record the measured finite 132 ms join while preserving historical document bytes."""
import base64,json
from prepare_vco1_portable import ROOT,sha
from prepare_long_tail import START,SPAN
from joint_cycles_analysis import require,TICK
def main():
 native,ref,audio,cli=[json.loads((ROOT/f'evidence/voice_tail_{n}01.json').read_text(encoding='utf8')) for n in ['native','reference','listening','cli']];require(all(r['passed'] for r in [native,ref,audio,cli]),'all measured gates before documentation');voltage=max(p['max_voltage_error_v'] for p in ref['same_clock_refinement']);ratio=max(p['gate_ratio'] for p in ref['same_clock_refinement']);resets=max(abs(float(x['interpolated_time_s'])-float(y['interpolated_time_s'])) for x,y in zip(ref['profiles'][0]['resets'],ref['profiles'][1]['resets']));budget=sum(o['bytes'] for o in native['outputs'])+sum(o['bytes'] for o in cli['outputs'])+sum(o['bytes'] for o in audio['files']);require(budget<=192*1024**2,'private output budget');lib='references-local/voice-assembly-public01/librf_d_circuit.rlib';rows=[]
 for p,f in zip(ref['profiles'],ref['flux_checks']):
  v=p['phases'][-1]['final_voltages_v'];rows.append(f"| {p['maximum_half_ticks']} | {p['accepted_steps']} | {p['fine_steps']} | {len(p['resets'])} | {v['C2']:.12g} | {f['final_slope_v_per_s']:.12g} | {v['LOUDNESS']:.12g} | {v['J7']:.12g} |")
 report=f'''# Cola cargada y escucha real de 132 ms

## Dominio y resultado

64 ms eléctricos adicionales desde 76,442 a 140,442 ms. Historia unida 132,004 ms desde 8,438 ms; dos WAV reales de 132 ms, 6336 muestras a 48 kHz. Modelo vintage CA3046 documental y escena condicionada OSC1→BUS→escalera/VCA/J7. KEY 0 V/S abierto/decay ON/PANEL_R16=1000 Ω se heredan; no hay nuevo evento ni cambio de controles. El contorno aún parte de la historia sintética anterior, no de un encendido físico desde silencio.

La cola nueva usa `assembly_decay_voice/engine` y la biblioteca `{lib}`, SHA256 `{sha(ROOT/lib)}`. Se reutiliza sin recompilarla. Los cuatro tramos anteriores proceden de sus propias familias ya admitidas; el WAV unido identifica esos orígenes y la cola nueva. No se atribuye retrospectivamente toda la historia al ensamblado nuevo. La unión conserva 3728 bytes completos, 458 HIGH/LOW, reloj, propuesta y receta; cuatro avances por resolución coinciden por bits con `block_decay_voice/engine` en esta unión.

| Semipaso máximo (ticks) | Accepted | Endpoints finos | Resets VCO | C2 final (V) | dC2/dt final (V/s) | Loudness final (V) | J7 final (V) |
| --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(rows)}

## Contraste original y memoria

{ref['independent_candidates']} candidatos/{ref['independent_nonlinear_rows']} ecuaciones seleccionadas nuevas pasan frente a la red original, diferencias finitas y cargas Decimal100. Las puertas de KCL, restricciones y correcciones son las anteriores. Se comparan 229 estados en 81 relojes comunes: error máximo de tensión {voltage:.12g} V y ratio de puerta {ratio:.12g}; resets interpolados difieren como máximo {resets:.12g} s, puerta de 10 ns. No se atribuye solve original independiente a los demás endpoints.

{sum(p['records'] for p in ref['flux_checks'])} registros completos de flujos C2 y {sum(p['selected_independent_endpoints'] for p in ref['flux_checks'])} endpoints de componentes Decimal100. Error máximo de balance de derivada {max(p['max_derivative_balance_error_v_per_s'] for p in ref['flux_checks']):.12g} V/s frente a 2 µV/s. Se incluyen ataque, decay, seguidor y cargas conectadas. TURN/LATCH nuevos observados: {sum(len(p['events']) for p in ref['flux_checks'])}. El voltaje y pendiente finales describen esta ventana; no definen una descarga completa ni un silencio asintótico.

Nueve balances ΔQ orientados y su composición desde 8,438 ms pasan la puerta de 1 pA×duración. La cuadratura de todos los estadios sigue siendo nativa. {ref['restores']} restores reproducen {ref['replayed_accepted_steps']} Accepted completos por bits; concurrencia máxima de motores sombra: {ref['maximum_active_replay_probes']}. Ocho corrupciones y dos destinos inválidos se rechazan sin publicar cambios.

## Audio y CLI

Dos derivaciones completas idénticas; error máximo entre resoluciones {audio['native_resolution_max_error_v']:.12g} V/{audio['native_resolution_max_pcm_lsb']} LSB. Se conserva sinc de 18 kHz/Blackman, 0,01 V/full scale, nivel y DC. Sin loop, normalización de pico, fade o repetición; extensión constante solo en bordes del filtro. Cuatro µs finales del circuito quedan fuera del WAV por la rejilla de 48 kHz. Cada unión comprueba estado completo, receta y una muestra compartida única.

WAV privados ignorados:

- `artifacts/long-tail01/rf-d-j7-tail-132ms-1048576-nativo.wav`
- `artifacts/long-tail01/rf-d-j7-tail-132ms-524288-nativo.wav`

Reproducción desde la raíz con las entradas propias disponibles y salida nueva:

```powershell
python -B tools/tail_render_cli.py --held references-local/sustained-voice01/524288/selected.txt --release references-local/release-voice01/524288/selected.txt --controlled references-local/decay-voice02/524288/selected.txt --extended references-local/extended-release01/524288/selected.txt --tail references-local/long-tail01/524288/selected.txt --output artifacts/escucha-132ms.wav
```

Sidecar con hashes de las diez entradas y del código de render, kernel y dependencias, clocks enteros, evento de resistencia heredado y ausencia de eventos nuevos. Cuatro integraciones verifican identidad completa del WAV/sidecar, protección de salida existente, unión incompatible y traza incompleta rechazadas antes de publicación.

## Evidencia y recursos

- [Protocolo](VOZ_COLA_LARGA_PROTOCOLO.md), [entradas propias](../evidence/voice_tail_inputs01.json), [native](../evidence/voice_tail_native01.json).
- [Red original/refinamiento/ΔQ](../evidence/voice_tail_reference01.json), [escucha](../evidence/voice_tail_listening01.json), [CLI](../evidence/voice_tail_cli01.json), [QA](../evidence/voice_tail_tests01.json).

Campaña nativa {native['wall_s']:.6f} s, auditor {ref['wall_s']:.6f} s. Productos privados nuevos {budget} bytes dentro de 192 MiB, reserva de 1 GiB. Sin Cargo/cache/SPICE o biblioteca nueva. Stack de laboratorio de 32 MiB; IO, replay y serialización fuera del hilo de audio. 255 tests Rust y dos definiciones Python heredados sin reejecución; las nuevas campañas y cuatro integraciones se contabilizan separadamente.

Sin fidelidad física, voz completa desde silencio, periodicidad, heap/deadline nuevos o RT admitidos. Siguiente: avanzar el comportamiento de la voz y una escucha musical útil con controles y cargas explícitos; esta cola finita no sustituye esa escena.
'''
 p=ROOT/'docs/VOZ_COLA_LARGA_RESULTADOS.md';require(not p.exists(),'exclusive measured report');p.write_text(report,encoding='utf8',newline='\n');before=json.loads((ROOT/'evidence/voice_tail_before01.json').read_text(encoding='utf8'));saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()};append=f'''\n\nLa [cola propia con ensamblado directo](docs/VOZ_COLA_LARGA_RESULTADOS.md)
añade 64 ms eléctricos: historia de 132.004 ms y dos WAV de 132 ms, 6336 muestras.
Receta y 3728 bytes de unión idénticos; ocho avances comparados por bits.
{ref['independent_nonlinear_rows']} ecuaciones originales seleccionadas nuevas,
81 relojes de 229 estados, balances de carga y replay acotado pasan. C2 final
{ref['flux_checks'][-1]['final_c2_v']:.9f} V; no silencio asintótico inferido.
CLI con diez entradas/código identificados y cuatro integraciones.
Sin biblioteca/cache nuevas, fidelidad física o RT. Siguiente escena útil de voz.
'''.encode('utf8')
 for n in ['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:
  require((ROOT/n).read_bytes()==saved[n],'historical bytes before append');prefix=saved[n].replace(b'voice_assembly_tests01.json',b'voice_tail_tests01.json') if n=='README.md' else saved[n];tail=append if n=='README.md' else append.replace(b'(docs/VOZ_COLA_LARGA_RESULTADOS.md)',b'(VOZ_COLA_LARGA_RESULTADOS.md)');(ROOT/n).write_bytes(prefix+tail)
 print('TAIL_DOCUMENTED',ref['accepted_steps'],ref['independent_nonlinear_rows'],budget)
if __name__=='__main__':main()
