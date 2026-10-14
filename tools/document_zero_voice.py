"""Publish both rejected costs and the current nested profile, preserving prior docs."""
import base64,json
from prepare_vco1_portable import ROOT
from joint_cycles_analysis import require
def main():
 a,b,p=[json.loads((ROOT/f'evidence/voice_zero_{n}01.json').read_text(encoding='utf8')) for n in ['bench','scan','profile']];require(all(r['passed'] for r in [a,b,p]) and not a['cost_utility_passed'] and not b['cost_utility_passed'],'measured exact rejected candidates');phase={q['name']:q for q in p['phases']};total=phase['step']['time_ns'];rows='\n'.join(f"| {q['name']} | {q['calls']} | {q['time_ns']/1e6:.6f} | {100*q['time_ns']/total:.4f} % |" for q in p['phases'] if q['name']!='unused');extra=a['solver_scratch_bytes'][1]-a['solver_scratch_bytes'][0]
 text=f'''# Recorridos de ceros: identidad, memoria y costo rechazado

## Decisión

Dos variantes de laboratorio pasan números y fallan la utilidad fijada antes de medir. No se promueven. La voz pública, su biblioteca, los puertos, cargas, reloj y WAV de 68 ms siguen idénticos al bloque anterior. No hay duración ni audio nuevos.

| Variante | Ratio mediano | Peor ronda | Scratch solver referencia/candidato (bytes) | Gate ≤0,95 / ≤1,05 |
| --- | --- | --- | --- | --- |
| Soporte LU real + bloques nulos CSR | {a['median_ratio']:.12g} | {a['worst_round_ratio']:.12g} | {a['solver_scratch_bytes'][0]} / {a['solver_scratch_bytes'][1]} | rechazo de mediana |
| Solo CSR por OR de bits sin signo | {b['median_ratio']:.12g} | {b['worst_round_ratio']:.12g} | {b['solver_scratch_bytes'][0]} / {b['solver_scratch_bytes'][1]} | rechazo de mediana |

La primera añade {extra} bytes fijos y no mejora tiempo. La segunda reduce {(1-b['median_ratio'])*100:.6f} % del tiempo del banco, sin scratch adicional; el gate pide 5 %. No se reduce ese umbral después de observar el resultado. Cinco rondas alternadas por variante, mismo proceso, banco, flags y compiler congelado; la mediana es el cociente de medianas de tiempos agregados. Son resultados de este banco y equipo, no una garantía para cualquier escena ni un deadline.

## Identidad y alcance

Banco 168 pares: 78 anteriores y 90 coarse/mid/end seleccionados de las dos liberaciones extendidas propias. Se verifican 1834 f64 por par, counters de cada variante y {168*211138} campos completos de stamp por bits. Los 24 pares nominales conservan counters históricos conocidos; los 144 pares seleccionados no adquieren retrospectivamente iteraciones/trials históricos, aunque las ejecuciones actuales sí se comparan por completo.

1280 fixtures directos por variante contrastan LU frente a las sustituciones densas originales: ±0, subnormales, extremos y overflow. 260 rechazos por variante coinciden. El control con matriz identidad/RHS −0 demuestra que omitir ceros sin atender al signo cambia bits; ambas variantes preservan el resultado denso. Seis fixtures de solver completo conservan clases de rechazo. Los métodos del circuito y sus puertas eléctricas son los anteriores; no se presenta este banco como un nuevo solve independiente de la red original.

La variante LU recoge soporte del factor real, conserva columnas en orden y ejecuta huecos cuando el acumulador es ±0. Comprueba finitud por fila; una fila no finita no puede recuperarse al dividir por una diagonal finita no nula. CSR1 omite solo grupos comparados iguales a cero; CSR2 usa OR u64 y máscara del signo, sin eliminar mantisa/exponente. Ambos respetan no nulos, NaN/Inf, capacidad, floor, suma y dirección de las conexiones. No se reemplaza el patrón real por un preset. Los helpers de acceso a LU privado pertenecen solo al laboratorio.

## Perfil de la familia pública actual

Un tercer ejecutable instrumenta la aritmética actual con los wrappers de reloj ya existentes, adaptados a `block_decay_voice/solver`; 168 pares y todos sus 1834 campos/counters coinciden con la referencia. Los relojes son **anidados**: las columnas siguientes no se suman para calcular costo total. No se resta overhead; el perfil cambia compilación y añade clocks/atomics de laboratorio, por lo que su tiempo frente al ejecutable sin instrumentar no se promociona como ganancia.

| Fase | Llamadas | Tiempo acumulado (ms) | Respecto de step instrumentado |
| --- | --- | --- | --- |
{rows}

El ensamblado `initialize` ocupa {100*phase['initialize']['time_ns']/total:.4f} % del step e incluye `parts`; las leyes de `parts` ocupan {100*phase['parts']['time_ns']/total:.4f} %, incluyendo `joint_parts` {100*phase['joint_parts']['time_ns']/total:.4f} %. El solve ocupa {100*phase['solve']['time_ns']/total:.4f} %. El CSR/support ocupa {100*phase['support']['time_ns']/total:.4f} % y las cuatro sustituciones agregadas {100*sum(phase[n]['time_ns'] for n in ['rhs64','rhs58','rhs132','rhs140'])/total:.4f} %, con llamadas desde prepare y correction. No sumar esos hijos con sus padres. El siguiente experimento debe atacar el ensamblado/`parts` o sus copias reales antes de ampliar el mismo detector de ceros.

## Evidencia

- [Protocolo previo](VOZ_CEROS_PROTOCOLO.md), [variante CSR aislada](VOZ_CEROS_SCAN_PROTOCOLO.md), [entradas propias](../evidence/voice_zero_inputs01.json).
- [LU + CSR medidos](../evidence/voice_zero_bench01.json), [CSR aislado medido](../evidence/voice_zero_scan01.json), [perfil actual](../evidence/voice_zero_profile01.json).
- [QA](../evidence/voice_zero_tests01.json). Los ejecutables, banco binario y productos privados quedan ignorados y protegidos por hashes; ninguna fuente/binario de los candidatos se sobrescribe.

Sin Cargo, nueva biblioteca, SPICE ni caché de compilación. Reserva 1 GiB y presupuesto nuevo 96 MiB. 255 tests Rust y dos definiciones Python heredados sin reejecución; los fixtures ejecutados aquí se contabilizan separados de esos tests. No se mide heap o deadline y no se admite RT, nueva fidelidad física ni nueva trayectoria independiente. Sigue disponible la escucha real anterior de 68 ms.
'''
 out=ROOT/'docs/VOZ_CEROS_RESULTADOS.md';require(not out.exists(),'exclusive measured report');out.write_text(text,encoding='utf8',newline='\n');before=json.loads((ROOT/'evidence/voice_zero_before01.json').read_text(encoding='utf8'));saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()};append=f'''\n\nEl [banco ampliado y perfil actual](docs/VOZ_CEROS_RESULTADOS.md) contrasta
168 pares y35471184 campos de stamp. Dos recorridos de ceros conservan
bits,1280 fixtures LU y seis errores, pero fallan utilidad5 %:
ratio{a['median_ratio']:.9f} con104488 bytes extra y{b['median_ratio']:.9f} sin
scratch extra. No se promueven. Perfil actual exacto: initialize55.13 %
incluye parts42.37 %, solve37.09 %; relojes anidados, sin ganancia inferida.
La voz pública y audio68 ms permanecen idénticos. Siguiente: ensamblado y
parts/copia de estados, conservando puertos, cargas y contraste completo.
'''.encode('utf8')
 for n in ['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:
  require((ROOT/n).read_bytes()==saved[n],'historic doc untouched');prefix=saved[n].replace(b'voice_extended_tests01.json',b'voice_zero_tests01.json') if n=='README.md' else saved[n];tail=append if n=='README.md' else append.replace(b'(docs/VOZ_CEROS_RESULTADOS.md)',b'(VOZ_CEROS_RESULTADOS.md)');(ROOT/n).write_bytes(prefix+tail)
 print('ZERO_RESULTS_DOCUMENTED')
if __name__=='__main__':main()
