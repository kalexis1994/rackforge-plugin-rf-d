# Corpus de junturas RMS

El corpus amplía la reconstrucción a **57 informes y 335 entradas**:
**332 blobs idénticos** y las tres excepciones históricas LF→CRLF.
Conserva ocho versiones fallidas anteriores de tests. La referencia de
reconstrucción es `bf1f0fd211197c77538d7ce5694dd99c0ebf1ae4`; helpers, pruebas y
validador se commitearon antes de generar la versión válida.
Los atributos Git, datos anteriores y gates no cambian.

Se añade el informe RMS y su recibo. La identidad del experimento
incluye parte simétrica firmada, raíces isqrt y todas las conversiones
de norma. Las medidas mu2/mu_infinito no se intersectan y las cotas
anteriores se preservan. El anclaje conserva una referencia común explícita.
La comparación incluye el prefijo desfavorable, sin seleccionar otra norma
por ventana ni descartar resultados.

[Datos](../evidence/loudness_latch_bdf_static_precision_junction_inputs.json.gz):
**357113 bytes**, SHA comprimido
`3b269f04272b149a251548c5756f9132eaf756dc3db2d2e0b9e48c685dc1067f`,
SHA canónico `a26a6b3b9df2475605784ce8df3080f2435c098f413dd874fab19c5b0f3c4727`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_junction_inputs_summary.json).

La [suite](../tests/test_loudness_latch_bdf_static_precision_junction_inputs.py)
pasa **2/2 al primer intento**, 78.7095339 s. Recupera cada entrada
desde blobs, reconstruye excepciones, identifica versiones, fuentes,
esquemas y destinos propios y verifica almacenamiento canónico. Rechaza
bytes o identidades alterados. También verifica el archivo rechazado
de un bloque anterior y la restauración exacta de su resumen histórico.
El [recibo](../evidence/loudness_latch_bdf_static_precision_junction_inputs_validation.json)
conserva SHA antes/después idénticos.

El bloque suma **siete regresiones nuevas**, todas pasan al primer intento:
cinco de RMS y dos del corpus. No hubo pruebas fallidas, archivos rechazados
ni solves nuevos en este bloque. Recuperar bytes y conservar cancelaciones
no cierra anclaje, restos no lineales, recorrido completo, física, audio
o deadline. **1 mV global sigue abierto.**

```powershell
python tools/loudness_latch_bdf_static_precision_junction_inputs.py
python tools/validate_bdf_static_precision_junction_inputs.py
```
