"""Publish measured finite-scope results without rewriting historical bytes."""
import base64,json
from prepare_vco1_portable import ROOT,sha
from prepare_extended_release import START,SPAN
from joint_cycles_analysis import require,TICK
def main():
 names=['voice_extended_native01','voice_extended_reference01','voice_extended_listening01','voice_extended_cli01'];native,ref,listening,cli=[json.loads((ROOT/f'evidence/{n}.json').read_text(encoding='utf8')) for n in names];require(all(r['passed'] for r in [native,ref,listening,cli]),'measured results before documentation');a,b=ref['profiles'];flux=ref['flux_checks'];voltage=max(p['max_voltage_error_v'] for p in ref['same_clock_refinement']);ratio=max(p['gate_ratio'] for p in ref['same_clock_refinement']);reset=max(abs(float(x['interpolated_time_s'])-float(y['interpolated_time_s'])) for x,y in zip(a['resets'],b['resets']));budget=sum(o['bytes'] for o in native['outputs'])+sum(o['bytes'] for o in cli['outputs'])+sum(o['bytes'] for o in listening['files']);require(budget<=128*1024**2,'total private product budget');rows=[]
 for p,f in zip(ref['profiles'],flux):
  final=p['phases'][-1]['final_voltages_v'];component=f['independent_components'][-1];rows.append(f"| {p['maximum_half_ticks']} | {p['accepted_steps']} | {p['fine_steps']} | {len(p['resets'])} | {final['C2']:.12g} | {f['final_slope_v_per_s']:.12g} | {final['LOUDNESS']:.12g} | {final['J7']:.12g} |")
 report=f'''# Liberación extendida con la familia pública optimizada

## Resultado y dominio

32 ms adicionales propios desde 44,442 a 76,442 ms. Se une una trayectoria de 68,004 ms desde 8,438 ms; dos WAV nativos de 68 ms (3264 muestras a 48 kHz). Modelo documental vintage CA3046, receta eléctrica heredada KEY=0 V/S abierto/decay ON/R=1 kΩ, con OSC1, mezclador, escalera, VCA y J7 cargados. No hay nuevo evento de teclado ni de resistencia. Sigue siendo una historia sintética condicionada y una ventana finita.

La biblioteca pública es `references-local/voice-block-library02/librf_d_circuit.rlib`, SHA256 `{sha(ROOT/'references-local/voice-block-library02/librf_d_circuit.rlib')}`. No se recompila ni modifica el circuito. El llamador nuevo restaura los 3728 bytes propios completos; cuatro avances por perfil comparan todos los estados, incrementos, observables, ratios, iteraciones, trials, relojes y propuestas con el ensamblado original. Ocho avances coinciden por bits. La identidad previa de 4 ms del candidato permanece como evidencia histórica, separada de esta nueva duración.

| Semipaso máximo (ticks) | Accepted | Endpoints finos | Resets VCO | C2 final (V) | dC2/dt final (V/s) | Loudness final (V) | J7 final (V) |
| --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(rows)}

## Contraste eléctrico y memoria

{ref['independent_candidates']} candidatos / {ref['independent_nonlinear_rows']} ecuaciones seleccionadas nuevas se evalúan con la red original, diferencias finitas y carga Decimal100; las puertas eléctricas permanecen iguales. No se atribuye auditoría original independiente a todos los endpoints. Los 229 estados se comparan en 41 relojes comunes: error máximo de tensión {voltage:.12g} V, ratio máximo de puerta {ratio:.12g}; resets interpolados difieren como máximo {reset:.12g} s frente a la puerta 10 ns. Se conservan los nueve balances ΔQ orientados y su unión desde el primer estado real de 8,438 ms; la cuadratura de todos los estadios sigue siendo nativa.

{sum(f['records'] for f in flux)} registros de flujos C2; {sum(f['selected_independent_endpoints'] for f in flux)} endpoints de componentes se contrastan en Decimal100. Error máximo de balance de derivada {max(f['max_derivative_balance_error_v_per_s'] for f in flux):.12g} V/s, puerta 2 µV/s. La caída incluye corriente de ataque, rama eléctrica decay y seguidor cargado; no presupone una exponencial RC aislada. Eventos TURN/LATCH nuevos observados: {sum(len(f['events']) for f in flux)}. Esto no demuestra descarga completa ni silencio asintótico.

{ref['restores']} restauraciones reproducen {ref['replayed_accepted_steps']} Accepted completos por bits; máximo simultáneo de motores sombra: {ref['maximum_active_replay_probes']}, con workspace compartido. Ocho corrupciones se rechazan; dos destinos inválidos conservan el checkpoint por bytes. Fuentes, parámetros, reloj y propuesta de ambas uniones permanecen idénticos al final anterior.

## Escucha y reproducción

Dos derivaciones completas de audio coinciden; máximo error entre resoluciones {listening['native_resolution_max_error_v']:.12g} V / {listening['native_resolution_max_pcm_lsb']} LSB. Kernel heredado sinc 18 kHz/Blackman, escala 0,01 V/full scale, sin loop, normalización de pico, fade o eliminación de DC. La extensión constante se limita a los bordes del filtro; 4 µs del circuito quedan fuera del WAV por la rejilla de 48 kHz. El contenido nuevo procede de solves nativos.

WAV privados ignorados:

- `artifacts/extended-release01/rf-d-j7-release-68ms-1048576-nativo.wav`
- `artifacts/extended-release01/rf-d-j7-release-68ms-524288-nativo.wav`

CLI desde la raíz, con las trazas y checkpoints propios disponibles:

```powershell
python -B tools/extended_render_cli.py --held references-local/sustained-voice01/524288/selected.txt --release references-local/release-voice01/524288/selected.txt --controlled references-local/decay-voice02/524288/selected.txt --extended references-local/extended-release01/524288/selected.txt --output artifacts/escucha-68ms.wav
```

El destino debe existir y la salida debe ser nueva. El sidecar registra hashes de las siete entradas, renderer, kernel, CLI y WAV, eventos heredados, parámetros y duración. Cuatro checks de integración verifican WAV completo/sidecar, salida existente sin cambios, seam incompatible y traza incompleta rechazados antes de publicar. El esquema RFDCY001 coincide con el contrato del perfil, no identifica cualquier receta arbitraria.

## Evidencia y presupuesto

- [Protocolo fijado antes de ejecutar](VOZ_LIBERACION_EXTENDIDA_PROTOCOLO.md).
- [Entradas propias](../evidence/voice_extended_inputs01.json), [ejecución nativa](../evidence/voice_extended_native01.json).
- [Red original, refinamiento y cargas](../evidence/voice_extended_reference01.json), [audio derivado](../evidence/voice_extended_listening01.json), [CLI](../evidence/voice_extended_cli01.json).
- [QA integral](../evidence/voice_extended_tests01.json), [llamador portable](../crates/rf-d-circuit/examples/extended_release.rs).

Campaña nativa {native['wall_s']:.6f} s; auditor original {ref['wall_s']:.6f} s. Productos privados nuevos {budget} bytes, dentro de 128 MiB, reserva 1 GiB. Sin Cargo/cache nueva, nueva biblioteca, SPICE o modificación de productos heredados. Stack de laboratorio 32 MiB, IO y replay fuera del hilo de audio. 255 tests Rust y dos definiciones Python heredados, sin reejecución: se ejecutan las regresiones del recorrido y cuatro integraciones CLI de este bloque.

No se admite fidelidad contra hardware, voz completa desde silencio, periodicidad estable, heap nuevo medido o tiempo real. La mejora de costo anterior facilita esta extensión; no mide un deadline de audio. Siguiente: usar la observación cargada para avanzar duración útil y controlar el costo, conservando estados, eventos y cargas.
'''
 output=ROOT/'docs/VOZ_LIBERACION_EXTENDIDA_RESULTADOS.md';require(not output.exists(),'exclusive measured report');output.write_text(report,encoding='utf8',newline='\n')
 section=f'''\n\nLa [liberación extendida con el motor público](docs/VOZ_LIBERACION_EXTENDIDA_RESULTADOS.md)
añade32 ms reales: historia unida68.004 ms y dos WAV nativos68 ms, sin loop.
KEY/S/R heredados, unión completa3728 bytes;8 avances completos coinciden
con el ensamblado original. {ref['independent_nonlinear_rows']} ecuaciones nuevas,
41 relojes229, balances y replay acotado pasan. C2 final{flux[-1]['final_c2_v']:.6f} V,
no silencio completo admitido. CLI reproducible y cuatro checks.
Sin biblioteca/cache nuevas, fidelidad física, heap/deadline nuevos o RT.
'''.encode('utf8')
 before=json.loads((ROOT/'evidence/voice_extended_before01.json').read_text(encoding='utf8'));saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()};require((ROOT/'README.md').read_bytes()==saved['README.md'],'untouched README before append');(ROOT/'README.md').write_bytes(saved['README.md'].replace(b'voice_block_tests01.json',b'voice_extended_tests01.json')+section)
 for name in ['docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:
  require((ROOT/name).read_bytes()==saved[name],'untouched historical doc before append');(ROOT/name).write_bytes(saved[name]+section.replace(b'(docs/VOZ_LIBERACION_EXTENDIDA_RESULTADOS.md)',b'(VOZ_LIBERACION_EXTENDIDA_RESULTADOS.md)'))
 print('EXTENDED_MEASURED_DOCS',ref['accepted_steps'],ref['independent_nonlinear_rows'],budget)
if __name__=='__main__':main()
