# Puerto R2/C6 hacia el recuperador del filtro

El [primer VCA nativo](../crates/rf-d-circuit/src/vca1_output.rs) expone ahora `solve_input_port` en RECOVER_COLLECTOR. Según **SVC-9 Fig. 9-11, PDF p. 13** y **tabla 7-8, pp. 30–31**, ese colector alimenta R2 `82 kΩ` y C6 `0,33 µF` antes de la base de Q16. **SVC-204D §2.9, PDF p. 12** confirma el acoplamiento AC desde el filtro. El [grafo transcrito](../evidence/vca1_input_boundary.json) y la [frontera](FRONTERA_ENTRADA_VCA1.md) registran el sentido de la conexión.

Para tensión impuesta `u=V_RECOVER_COLLECTOR`, el puerto devuelve `i=(u−V_C6LEFT)/82 kΩ`, positiva **desde el recuperador hacia el primer VCA**, en amperios. La derivada `Y=di/du` se evalúa con los estados anteriores de C6, C15 y todos los capacitores posteriores fijos: tras el paso conjunto, se resuelve `J·(dx/du)=e_C6LEFT/82 kΩ` con el Jacobiano analítico local `10×10`, ya cargado por la matriz exacta `4×4` del [segundo VCA](PUERTO_NATIVO_HACIA_VCA1.md). Entonces `Y=(1−dV_C6LEFT/du)/82 kΩ`, en siemens. La matriz posterior aceptada se conserva en el resultado del paso y evita volver a resolverla al calcular la tangente. Cada evaluación es provisional: el futuro solver del recuperador debe confirmar únicamente el `next_state` de la solución conjunta.

El [oráculo Python de 25 incógnitas](../tools/vca1_output_vectors.py) congela `i` en los 12 pasos del [fixture](../evidence/vca1_output_vectors.json); la [regresión Rust](../crates/rf-d-circuit/tests/vca1_output.rs) exige `<1 nA` y compara `Y` por diferencias simétricas de `±1 mV` en los pasos 0, 6 y 10 con tolerancia `2×10⁻⁸ S+10⁻³·|Y_fd|`. La [prueba sin heap](../crates/rf-d-circuit/tests/no_alloc.rs) añade 20 evaluaciones del puerto. Esto permite conectar la carga dinámica en el colector de recuperación documentado; todavía no mide el filtro ni demuestra que la ruta cumpla tiempo real. R2/C6 conservan sus tolerancias de documento y todos los parámetros BJT/diodos siguen siendo hipótesis de laboratorio, como se detalla en [VCA1→J7](VCA1_SALIDA_NATIVA.md).

```powershell
python -m unittest discover -s tests -p test_vca1_output_vectors.py -q
cargo test --workspace
```
