"""Record measured same-origin cutoff differences with explicit inherited scope."""
import base64,json,math
from prepare_vco1_portable import ROOT
from joint_cycles_analysis import require
def main():
 native,ref,audio,cli=[json.loads((ROOT/f'evidence/cutoff_ab_{n}01.json').read_text(encoding='utf8')) for n in ['native','reference','listening','cli']];require(all(r['passed'] for r in [native,ref,audio,cli]),'measured gates before report');rows=[]
 for x in audio['ab_metrics']:rows.append(f"| {x['maximum_half_ticks']} | {x['mean_open_v']:.12g} | {x['mean_closed_v']:.12g} | {x['rms_open_v']:.12g} | {x['rms_closed_v']:.12g} | {x['rms_difference_v']:.12g} | {x['max_difference_v']:.12g} |")
 size=sum(o['bytes'] for o in native['outputs']+cli['outputs']+audio['files']);inherited=1374*sum(f['closed_selected_accepted_count'] for f in ref['forks']);fine=audio['ab_metrics'][1];ratio=fine['rms_closed_v']/fine['rms_open_v'];db=20*math.log10(ratio);ac_ratio=fine['rms_about_mean_closed_v']/fine['rms_about_mean_open_v'];ac_db=20*math.log10(ac_ratio)
 report=f'''# Cutoff A/B desde un origen común

## Diseño y alcance

Se bifurca el checkpoint propio antes del cierre de panel a 156,450 ms: 458 HIGH/LOW, clock y propuesta, KEY0/S abierto, decay ON/R16 1 kΩ, CV y cargas idénticos. La rama cerrada ya admitida cambia α1→0,5; la nueva mantiene α1 durante los mismos 8 ms, hasta 164,450 ms. Se reutiliza la biblioteca assembly. El estado posterior evoluciona libremente en ambas redes: no se impone igualdad del contorno de volumen o de la onda del VCO tras el evento.

α es fracción eléctrica, no Hz o curva de panel calibrada. La generación del contorno de filtro permanece impuesta a pin16=0 V. [Derivación y fuentes](CUTOFF_NATIVO_Q26_Q28.md), [receta](RECETA_CONDICIONADA_PROTOCOLO.md). Historia condicionada, sin unidad física.

Se calcula una rama alternativa de 8 ms en una ventana ya existente. No se concatenan ambas ni se amplían retrospectivamente la historia continua/WAV anterior de 164 ms. RFCTF001 y todos los campos de receta inicial coinciden por bytes; el cierre difiere sólo en fase/α. Ocho Accepted de la rama nueva coinciden completos por bits con block.

## Validación numérica y memoria

Rama abierta: {ref['accepted_steps']} Accepted/{ref['fine_steps']} endpoints; {ref['independent_nonlinear_rows']} ecuaciones seleccionadas nuevas, original/FD/Decimal100, puertas KCL20 pA, restricciones200 pA, correcciones1 µV/1 nA. Once relojes de 229 estados por resolución; peor ratio de puerta {max(x['gate_ratio'] for x in ref['same_clock_refinement']):.12g}. Resets≤10 ns, transiciones≤100 ns, flujos C2/componentes seleccionados y nueve balances ΔQ≤1 pA×duración pasan. {ref['restores']} restores/{ref['replayed_accepted_steps']} Accepted por bits, máximo {ref['maximum_active_replay_probes']} motores sombra; corrupciones y destinos inválidos rechazados atómicamente.

Rama cerrada: {inherited} ecuaciones seleccionadas heredadas por identidad de [la campaña anterior](../evidence/voice_cutoff_reference01.json), sin reejecución ni contabilizarlas como nuevas. Comparación A/B en once clocks comunes conserva la igualdad inicial y registra diferencias posteriores de C2, loudness, J7, base Q26 y corriente TAIL→Q28C. No hay puerta de cercanía entre α diferentes: la diferencia es el objeto de estudio.

## Voltios y escucha

Métricas de las 384 muestras filtradas sobre la misma ventana, con DC incluido y escala idéntica:

| Semipaso máximo (ticks) | Media abierto (V) | Media cerrado (V) | RMS abierto (V) | RMS cerrado (V) | RMS diferencia (V) | Máxima diferencia (V) |
| --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(rows)}

En resolución 1 µs, RMS cerrado/abierto={ratio:.12g}, {db:.9g} dB. Este cociente describe J7 con transitorio y DC de esta ventana; no es frecuencia de corte, respuesta estacionaria o un nivel perceptual calibrado. Las diferencias incluyen toda la respuesta de la voz cargada a α, incluida la realimentación sobre vecinos.

Como estadística adicional, RMS respecto de la media de cada ventana: abierto={fine['rms_about_mean_open_v']:.12g} V, cerrado={fine['rms_about_mean_closed_v']:.12g} V; cociente={ac_ratio:.12g}, {ac_db:.9g} dB. Se calcula sobre los mismos voltios filtrados, conservando DC en los WAV. No se ajusta el audio ni se interpreta este estadístico como transferencia estacionaria.

Cuatro WAV mono PCM16 de 8 ms, 384 muestras a 48 kHz. Dos derivaciones completas idénticas; refinamiento entre resoluciones de cada rama ≤2 µV/7 LSB. Sinc18 kHz/Blackman, 0,01 V/FS y DC conservados, sin normalización, fades, loop o repetición. Extensión constante sólo en bordes del filtro; todos los clocks de circuito de la ventana están presentes.

- `artifacts/cutoff-ab01/rf-d-cutoff-ab-open-8ms-524288.wav`
- `artifacts/cutoff-ab01/rf-d-cutoff-ab-closed-8ms-524288.wav`
- Las dos versiones de 2 µs están en la misma carpeta con sufijo `1048576`.

CLI desde la raíz, con entradas propias y salida nueva:

```powershell
python -B tools/cutoff_ab_cli.py --open references-local/cutoff-ab01/524288/selected.txt --closed references-local/voice-cutoff01/524288/selected.txt --output artifacts/cutoff-ab-pair.json
```

Publica `cutoff-ab-pair-open.wav`, `cutoff-ab-pair-closed.wav` y el sidecar con siete entradas, código importado, clocks/α y métricas. Cuatro checks: identidad de ambos WAV/sidecar, protección de los tres archivos existentes y rechazos específicos previos de estado inicial incompatible y ventana incompleta. Fixtures completos.

## Evidencia, recursos y límites

[Protocolo](VOZ_CUTOFF_AB_PROTOCOLO.md), [entradas](../evidence/cutoff_ab_inputs01.json), [nativo](../evidence/cutoff_ab_native01.json), [red original y origen A/B](../evidence/cutoff_ab_reference01.json), [audio/métricas](../evidence/cutoff_ab_listening01.json), [CLI](../evidence/cutoff_ab_cli01.json), [QA](../evidence/cutoff_ab_tests01.json).

Preparación: una sustitución amplia reescribía un `for` y producía SyntaxError. [Fallo y repetición sin cambios](../evidence/cutoff_ab_preflight_failure01.json); [reparación acotada](../evidence/cutoff_ab_preflight_repair01.json) antes de medir, conservando snapshot previo y caller. No se cambiaron gates ni circuito.

Campaña nativa {native['wall_s']:.6f} s, auditor {ref['wall_s']:.6f} s; privados nuevos {size} bytes dentro de 64 MiB, reserva1 GiB. Sin Cargo/cache/SPICE o biblioteca nuevos, stack offline32 MiB. 255 tests Rust y dos definiciones Python heredados sin reejecución. Sin fidelidad física, voz desde silencio, periodicidad, calibración, heap/deadline o RT nuevos.

Siguiente: controles pendientes de la voz y su contorno de filtro, con comparaciones desde el mismo estado cuando se quiera aislar el efecto de un parámetro.
'''
 p=ROOT/'docs/VOZ_CUTOFF_AB_RESULTADOS.md';require(not p.exists(),'exclusive measured report');p.write_text(report,encoding='utf8',newline='\n');before=json.loads((ROOT/'evidence/cutoff_ab_before01.json').read_text(encoding='utf8'));saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()};append=f'''\n\nEl [A/B de cutoff desde el mismo estado](docs/VOZ_CUTOFF_AB_RESULTADOS.md)
compara α1/0,5 durante 8 ms con 458 HIGH/LOW, clock/propuesta y controles comunes.
Rama abierta nueva: {ref['independent_nonlinear_rows']} ecuaciones seleccionadas;
cerrada: {inherited} heredadas, sin reejecución. Once clocks229, balances/replay
pasan; cuatro WAV de 8 ms sin concatenación o normalización. RMS cerrado/abierto
{ratio:.9g} ({db:.6g} dB), ventana con DC/transitorios. Siete entradas/código y
cuatro checks CLI. La historia/WAV continuo de 164 ms sigue sin prolongarse.
Sin Hz calibrados, contorno de filtro completo, fidelidad física o RT.
[QA](evidence/cutoff_ab_tests01.json).
'''.encode('utf8')
 for n in ['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:
  require((ROOT/n).read_bytes()==saved[n],'historic bytes');prefix=saved[n].replace(b'voice_cutoff_tests01.json',b'cutoff_ab_tests01.json') if n=='README.md' else saved[n];tail=append if n=='README.md' else append.replace(b'(docs/VOZ_CUTOFF_AB_RESULTADOS.md)',b'(VOZ_CUTOFF_AB_RESULTADOS.md)').replace(b'(evidence/cutoff_ab_tests01.json)',b'(../evidence/cutoff_ab_tests01.json)');(ROOT/n).write_bytes(prefix+tail)
 print('CUTOFF_AB_DOCUMENTED',size)
if __name__=='__main__':main()
