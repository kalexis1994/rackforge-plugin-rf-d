# Polifonía de RF-D

**Voices**, en la cabecera, arranca en **Mono**. **Poly 2** a **Poly 6**
habilitan el número indicado de notas simultáneas. El ajuste se guarda con la
sesión de RackForge. Un programa de fábrica selecciona **Mono** o **Poly 2**
según su banco. Los programas de usuario usan el modo seleccionado en el panel.
Al cambiar de modo se reinician las notas activas y los estados DSP.

## Referencias Moog

El Memorymoog de 1982 tenía seis voces, cada una con tres osciladores
y su propio filtro y contornos. Su teclado permitía asignar voces de forma
cíclica y recordar qué voz había tocado una nota. El Moog One documenta
la posibilidad de reasignar la nota más antigua al alcanzar el límite de
voces. [Catálogo Memorymoog de Moog](https://moogfoundation.org/wp-content/uploads/1982-Memorymoog-Catalog.pdf) ·
[Manual del Memorymoog, modos de teclado, pp. 23–24](https://device.report/m/8342e245905bf79022fec16310af977a3e07307e23b72e4688d1d1b812dff698.pdf) ·
[Manual del Moog One, p. 66](https://api.moogmusic.com/sites/default/files/2018-10/Moog_One_Manual_2.pdf).

RF-D comparte los controles de panel entre las voces y conserva por voz los
VCO, filtro, VCA, contornos y el lazo de realimentación LO. La asignación
reutiliza la voz que recibió la misma combinación de nota y canal MIDI si
sigue asociada a ella. Para notas nuevas recorre las voces libres en orden
cíclico. Si se agotan, reasigna primero una voz en release y después la
nota activa más antigua. El pedal de sustain actúa por canal. S-Trigger
controla la primera voz y A‑440 se genera una sola vez.
La mezcla reserva margen mediante una ganancia fija según el límite
seleccionado, con una curva suave por encima de 0,8 de escala completa.

## Raspberry Pi 4 a 128 frames

Prueba del 14 de noviembre de 2026 a 48 kHz, con bloques de 128 frames
(2,667 ms de plazo, 1,333 ms de margen objetivo). Se usaron Interval Drone,
Copper Sidebands y Feedback Bass. RackForge ejecutó su prueba de carga
offline con acordes sostenidos desde el primer bloque. El ensayo por bloque
usó WASM directo con cambios de notas y rueda en Copper Sidebands.
La sesión de audio de la Pi quedó activa en la Scarlett durante la medición.

| Voces | Peor media en RackForge, dos pases | Peor p99 WASM, primer pase |
|---:|---:|---:|
| 1 | 0,899 ms | 2,516 ms |
| 2 | 1,419 ms | 2,973 ms |
| 3 | 2,435 ms | 3,982 ms |
| 4 | 2,869 ms | 4,363 ms |
| 5 | 3,171 ms | 5,246 ms |
| 6 | 3,840 ms | 6,364 ms |

En este ensayo, Poly 2 quedó más cerca del objetivo. Poly 3 supera el
plazo en los picos y Poly 4–6 lo superan incluso en promedio en al menos
un escenario. El ensayo aislado en la salida auxiliar de la Pi quedó
bloqueado porque la salida admite S16_LE y el motor físico de RackForge
requiere S32_LE. Los tiempos WASM incluyen la planificación del sistema
y el segundo pase, fijado a un núcleo, muestra su sensibilidad a la
contención.
[Recibo y resultados por programa](../evidence/rf_d_voice_poly_pi01.json).

Con RF-D 0.8.4 instalado, se hicieron dos pruebas físicas cortas en la
Scarlett Solo a 48 kHz y 128 frames efectivos. Una nota con **Model D
Classic** dio un máximo de 1,059 ms. Un acorde de dos notas con
**Afterglow Strings** dio un máximo de 1,401 ms. RackForge registró cero
plazos perdidos y cero XRUNs durante estos pases. Queda pendiente la
medición sostenida de Poly con el resto del banco y más de dos voces.

Para repetir la prueba de carga con la carpeta del paquete de desarrollo
en la Pi, ejecutar lo siguiente con `COUNT` entre 1 y 6 y `PRESET`
en `interval_drone`, `copper_sidebands` o `feedback_bass`.

```sh
rackforge-core stress "$PACKAGE" --preset "$PRESET" --parameter "55=$((COUNT - 1))" \
    --voices "$COUNT" --blocks 1600 --frames 128
```

`python -B tools/check_rf_d_playable_voice.py` verifica acordes de hasta
seis notas, la reasignación, el sustain por canal y los cambios de modo
en posiciones exactas de muestra. En la Pi, tres renders mono del
candidato coincidieron bit a bit con el 0.8.3.
