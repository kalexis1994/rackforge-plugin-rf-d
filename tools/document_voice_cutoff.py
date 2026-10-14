"""Record the measured loaded cutoff control without rewriting previous evidence."""
import base64,json
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
def main():
 native,ref,audio,cli=[json.loads((ROOT/f'evidence/voice_cutoff_{n}01.json').read_text(encoding='utf8')) for n in ['native','reference','listening','cli']];require(all(r['passed'] for r in [native,ref,audio,cli]),'measured gates before report');size=sum(o['bytes'] for o in native['outputs']+cli['outputs']+audio['files']);require(size<=96*1024**2,'finite outputs');rows=[];control_rows=[]
 for p in ref['profiles']:
  for phase in p['phases']:
   v=phase['final_voltages_v'];rows.append(f"| {p['maximum_half_ticks']} | {phase['phase']} | {[1.,.5,1.][phase['phase']]} | {phase['accepted_steps']} | {v['C2']:.12g} | {v['LOUDNESS']:.12g} | {v['J7']:.12g} |")
   state=phase['final_high_low'];voltage=lambda k:state[k]+state[k+229];control_rows.append(f"| {p['maximum_half_ticks']} | {phase['phase']} | {voltage(195):.12g} | {voltage(198):.12g} | {(voltage(138)-voltage(198))/680:.12g} |")
 report=f'''# Cutoff del panel en la voz cargada

## Escena y control

Desde cada final propio del retrigger a 156,446 ms: 4 µs de continuidad con α=1, 8 ms con α=0,5 y 8 ms de reapertura a α=1. Final 172,450 ms; 16,004 ms nuevos y 164,012 ms de historia propia desde 8,438 ms. KEY 0 V/S abierto, decay ON/R16 1 kΩ y CV de VCO fijos. Sin gatillo nuevo ni sustitución de la onda por una fuente grabada.

α es la fracción eléctrica desde −10 V del potenciómetro R11 de 5 kΩ: Vth=−10+20α V y Rth=5000α(1−α) Ω en serie con R55 de 200 kΩ. Se conservan todas las ramas del panel, Q26/Q28/C18 y su carga sobre la escalera. [Fuentes, dominio e incertidumbres](CUTOFF_NATIVO_Q26_Q28.md), [receta](RECETA_CONDICIONADA_PROTOCOLO.md). Estas posiciones no son frecuencias Hz o una curva angular calibrada. Pin16 del contorno de filtro sigue impuesto a 0 V; el generador de ese contorno permanece pendiente.

Se reutiliza `references-local/voice-assembly-public01/librf_d_circuit.rlib`, SHA256 `{sha(ROOT/'references-local/voice-assembly-public01/librf_d_circuit.rlib')}`. El llamador reconstruye la misma receta nominal cambiando sólo α; no modifica la biblioteca ni el solver. La historia sigue condicionada. El contorno de volumen evoluciona durante el experimento: no se atribuye a cutoff toda diferencia entre ventanas temporales de J7 ni se declara un A/B desde el mismo estado.

## Checkpoints y eventos

RFCTF001 extiende RFDCY001 con f64 α: 3736 bytes, HIGH/LOW desde offset72. La conversión inicial cambia magic/phase e inserta α=1; conserva exactamente reloj, propuesta, fuentes, resistencia y 458 valores de estado. Dos eventos por resolución cambian únicamente α/fase; checkpoints antes/después verifican preservación de lo demás.

Ocho Accepted completos en la unión y 16 después de los eventos coinciden por bits con la familia block anterior usando la misma posición de cutoff. El codec contiene ahora el control realmente usado al restaurar, además de la memoria del circuito.

| Semipaso máximo (ticks) | Fase | α | Accepted | C2 final (V) | Loudness final (V) | J7 final (V) |
| --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(rows)}

Observables del puerto de control al final de cada fase, derivados de los estados HIGH/LOW auditados: base Q26=índice195, colector Q28=198, TAIL=138. El mapa `chain_index(k)=133+k` y la rama R60 `(TAIL−Q28C)/680 Ω` proceden de `assembly_decay_voice.rs` y `circuit66.rs`; el signo positivo indica corriente desde TAIL hacia Q28C. Son puntos de la trayectoria, no una medición de frecuencia de corte o un equilibrio DC nuevo.

| Semipaso máximo (ticks) | Fase | Base Q26 (V) | Colector Q28 (V) | Corriente TAIL→Q28C (A) |
| --- | --- | --- | --- | --- |
{chr(10).join(control_rows)}

## Red original y memoria

{ref['accepted_steps']} Accepted/{ref['fine_steps']} endpoints finos; {ref['independent_candidates']} candidatos y {ref['independent_nonlinear_rows']} ecuaciones seleccionadas nuevas. El auditor reconstruye la red original de panel a α de cada fase, FD y cargas Decimal100; conserva KCL 20 pA, restricciones 200 pA y correcciones 1 µV/1 nA. Se seleccionan coarse/mid/end de bordes, resets y TURN/LATCH; no se atribuye solve original al resto de endpoints.

22 relojes de 229 estados: error máximo {max(p['max_voltage_error_v'] for p in ref['same_clock_refinement']):.12g} V, ratio de puerta {max(p['gate_ratio'] for p in ref['same_clock_refinement']):.12g}. {sum(len(p['resets']) for p in ref['profiles'])} resets refinados ≤10 ns. Nueve balances ΔQ orientados pasan por fase/total y unión desde 8,438 ms, puerta 1 pA×duración; incluyen C18, C27/BUS, contorno y junturas. La cuadratura de todos los estadios es nativa. {sum(p['records'] for p in ref['flux_checks'])} flujos C2 completos; componentes seleccionados Decimal100 y balance de derivada ≤2 µV/s. {ref['restores']} restores/{ref['replayed_accepted_steps']} Accepted reproducidos por bits, máximo {ref['maximum_active_replay_probes']} motores sombra; corrupciones y destinos inválidos rechazados atómicamente.

## Audio y CLI

Dos WAV mono PCM16 de 164 ms, 7872 muestras a 48 kHz; historia eléctrica 164,012 ms, truncamiento 12 µs. Siete tramos con familias originales identificadas. Uniones de estado completo/receta/endpoint único, sin loop, fades o normalización; DC y escala 0,01 V/FS conservados. Sinc 18 kHz/Blackman, extensión constante sólo en bordes del filtro. Dos derivaciones completas idénticas; diferencia entre resoluciones {audio['native_resolution_max_error_v']:.12g} V/{audio['native_resolution_max_pcm_lsb']} LSB, puertas 2 µV/7 LSB.

- `artifacts/voice-cutoff01/rf-d-j7-cutoff-164ms-1048576-nativo.wav`
- `artifacts/voice-cutoff01/rf-d-j7-cutoff-164ms-524288-nativo.wav`

CLI con entradas propias y salida nueva desde la raíz:

```powershell
python -B tools/cutoff_render_cli.py --held references-local/sustained-voice01/524288/selected.txt --release references-local/release-voice01/524288/selected.txt --controlled references-local/decay-voice02/524288/selected.txt --extended references-local/extended-release01/524288/selected.txt --tail references-local/long-tail01/524288/selected.txt --retrigger references-local/voice-retrigger01/524288/selected.txt --cutoff references-local/voice-cutoff01/524288/selected.txt --output artifacts/escucha-cutoff.wav
```

Sidecar con 24 entradas reales, código importado, clocks, familias y eventos de cutoff. Cuatro integraciones pasan: WAV/sidecar completos, protección de salida existente y rechazos específicos antes de publicación de unión incompatible/traza incompleta. Los fixtures incluyen todos los checkpoints requeridos.

## Evidencia y alcance

[Protocolo](VOZ_CUTOFF_PROTOCOLO.md), [entradas](../evidence/voice_cutoff_inputs01.json), [nativo](../evidence/voice_cutoff_native01.json), [red original/refinamiento/carga](../evidence/voice_cutoff_reference01.json), [audio](../evidence/voice_cutoff_listening01.json), [CLI](../evidence/voice_cutoff_cli01.json), [QA](../evidence/voice_cutoff_tests01.json).

Campaña {native['wall_s']:.6f} s, auditor {ref['wall_s']:.6f} s; privados nuevos {size} bytes dentro de 96 MiB, reserva 1 GiB. Sin Cargo/cache/SPICE o biblioteca nuevos. Stack offline 32 MiB. 255 tests Rust y dos definiciones Python heredados sin reejecución; campañas/integraciones nuevas separadas. Sin fidelidad física, voz desde silencio, periodicidad, heap/deadline, RT o calibración musical admitidos.

Siguiente: controles útiles de la voz y sus fronteras pendientes, manteniendo cargas y receta completa; contrastar una respuesta A/B desde el mismo estado cuando se quiera atribuir diferencias sonoras sólo al cutoff.
'''
 p=ROOT/'docs/VOZ_CUTOFF_RESULTADOS.md';require(not p.exists(),'exclusive report');p.write_text(report,encoding='utf8',newline='\n');before=json.loads((ROOT/'evidence/voice_cutoff_before01.json').read_text(encoding='utf8'));saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
 append=f'''\n\nEl [cutoff cargado de panel](docs/VOZ_CUTOFF_RESULTADOS.md) añade 16,004 ms:
α1→0,5→1 sin modificar KEY/CV ni borrar cargas. Codec completo RFCTF001 de
3736 bytes; 16 Accepted tras eventos y ocho de unión coinciden con block.
{ref['independent_nonlinear_rows']} ecuaciones seleccionadas nuevas con el panel
de cada fase, 22 relojes de 229 estados y nueve balances por fase/total/unión.
Dos WAV reales de 164 ms, 24 entradas identificadas y cuatro checks CLI.
Contorno de filtro pin16 sigue impuesto; sin Hz calibrados, fidelidad física o RT.
[QA](evidence/voice_cutoff_tests01.json).
'''.encode('utf8')
 for n in ['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:
  require((ROOT/n).read_bytes()==saved[n],'historic bytes');prefix=saved[n].replace(b'voice_retrigger_tests01.json',b'voice_cutoff_tests01.json') if n=='README.md' else saved[n];tail=append if n=='README.md' else append.replace(b'(docs/VOZ_CUTOFF_RESULTADOS.md)',b'(VOZ_CUTOFF_RESULTADOS.md)').replace(b'(evidence/voice_cutoff_tests01.json)',b'(../evidence/voice_cutoff_tests01.json)');(ROOT/n).write_bytes(prefix+tail)
 print('CUTOFF_DOCUMENTED',size)
if __name__=='__main__':main()
