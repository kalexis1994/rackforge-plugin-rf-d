# Refinamiento temporal del circuito global

## Alcance y método

El [circuito de 66 nodos](SOLVER_GLOBAL_66_NODOS.md) conserva la topología de SVC-9 Fig. 9-11, 9-8 y 9-17, los semiconductores nominales impuestos y Euler implícito. Se estudia cómo cambia su solución al partir `dt`; no se altera el motor ni se admite oversampling en el plugin.

El banco `circuit66_admission --temporal` usa 48/96/192 kHz, ambos R61 y dos fronteras BUS: senoide 100 Hz/100 mV; y suma de 100 Hz/80 mV, 1600 Hz/15 mV y 4163 Hz/5 mV. El contorno impuesto es 2 Hz/20 mV. Cutoff=0,5, RANGE=0,1, R14=25 kΩ, loudness1/2=2 V, R20/R21=2,5/2 kΩ, HI/LO=10/100 kΩ y tip/ring=32 Ω. Las amplitudes/frecuencias son estímulos sintéticos en unidades eléctricas.

Cada traza dura los mismos **20 ms**, con 960/1920/3840 pasos. Las tres integraciones arrancan de un único DC copiado bit a bit, con sus 18 historiales capacitivos. Las fronteras se evalúan al extremo derecho `t=n/rate`, desde n=1; el punto fino `2n` se compara con el grueso `n` sin interpolación. Así se conserva tanto el instante físico como el inicio de la integración.

Se registran máximos y RMS de los 66 nodos, 18 voltajes capacitivos, corriente de cola y HI/LO. Antes de medir se fija: KCL <10 pA y descenso de máximos **y** RMS para J7, C2_RIGHT y cursor R21 al pasar de 48→96 a 96→192 kHz. Los cocientes informan sobre el error de primer orden de Euler. No son una cota de error absoluto contra una solución continua.

## Resultado

Las cuatro escenas y **26880 pasos** pasan. Máximos de diferencia entre tasas:

| BUS / R61 | J7 48→96 | J7 96→192 | Cociente máximo J7 |
| --- | --- | --- | --- |
| Seno / 200 Ω | 162,067 µV | 81,817 µV | 1,98084 |
| Seno / 200 kΩ | 28,715 µV | 14,455 µV | 1,98650 |
| Suma / 200 Ω | 148,670 µV | 75,074 µV | 1,98032 |
| Suma / 200 kΩ | 27,667 µV | 13,948 µV | 1,98351 |

Los cocientes máximos de C2/R21 están entre 1,9843 y 1,9913; los RMS también disminuyen. Es consistente con primer orden en estas fronteras suaves. El resultado explica una diferencia de discretización medible a tasas de audio, aunque Rust y Python a igual `dt` coincidan a escala de nanovoltios. Elegir discretización requiere su propio gate.

`evidence/circuit66_temporal_convergence.json` registra todas las métricas y metadatos. El banco termina con error si falta convergencia o falla el descenso. La extracción de parámetros nominales a una función compartida evita duplicarlos entre benchmarks; la ruta global de costo sigue pasando y dio 2,233 ms/bloque en la comprobación posterior.

No se midieron plazos de 96/192 kHz ni se caracterizaron discontinuidades, autooscilación o aliasing del VCO. C6 y C7 siguen abiertos. El [refinamiento previo de 62 nodos](CONVERGENCIA_TEMPORAL_AURICULARES.md) se conserva como evidencia de otro alcance.

```powershell
cargo build --release -p rf-d-circuit --example circuit66_admission
./tools/run_circuit66_admission.ps1 -Mode temporal -Output evidence/circuit66_temporal_convergence.json
```
