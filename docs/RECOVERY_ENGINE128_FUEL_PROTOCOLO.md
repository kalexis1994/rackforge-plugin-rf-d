# Repetición de 128 frames tras corregir el medidor

2026-11-07. Repetir el banco de RF-D con RackForge recompilado en
Release con Rust 1.98.0 MSVC y Cargo.lock. La revisión de control
`7a14c68a` y la corregida difieren sólo en el registro de combustible
del runtime. Conservar las dos series y los artefactos identificados
por hash. La DLL de referencia, la excitación, el núcleo, el FIR,
la ABI, la optimización de Wasmtime y el reloj de ASIO siguen el
protocolo anterior.
[Protocolo base](RECOVERY_ENGINE128_PROTOCOLO.md)

La corrección debe llevar a cero las asignaciones del hilo que llama al
motor, desde el primer bloque. Las pruebas existentes del runtime deben
seguir confirmando el corte por combustible y la interrupción por época.
Exigir la misma captura f32 de 2048 frames bit a bit, incluidos los
48 frames de latencia. Exigir 128 frames efectivos a 48 kHz en cada
banco, preparación incluida en el primer plazo, ningún aviso del
controlador, ningún plazo perdido, ningún intervalo de más de 1.5
períodos y un máximo de 1.333 ms por callback. Repetir una vez
cada rechazo sin cambiar el binario.

Medir por separado el invitado compilado con `opt-level=3` en el
host corregido. Esta variante cambia la compilación de los tres
crates Wasm del banco. La DLL de referencia y el ejecutable ASIO
mantienen sus opciones. Comparar medianas, P99 y plazos, y aplicar
el mismo criterio de admisión. El VCO y los contornos se mantienen
fuera del banco hasta obtener margen reproducible.

Probar además SIMD explícito por pares de filas en cinco productos
matriz-vector del núcleo. Transponer sus tablas en compilación y
recorrer las columnas en el orden escalar de cada fila, sin fusionar
multiplicación y suma. Conservar las 18 cargas, las 12 leyes y el
solve de Newton. Medir esta variante con `opt-level=3` y exigir la
misma captura bit a bit antes de abrir el controlador. Este banco
cubre el punto nominal y la excitación congelada. Una promoción del
núcleo necesita volver a contrastar sus estados y puertos en las
reservas eléctricas.

Trabajar en el área temporal única. Reusar durante la campaña el
target de Cargo local a esa área. Retirar binarios y cachés una vez
guardados los recibos. Conservar las capturas y fuentes admitidas.
