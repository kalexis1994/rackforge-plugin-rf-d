# Nota continua de 100 ms y costo temporal de voz

Variante experimental del circuito nominal SVC-9 pp.5/9/13/19, desde
`35bf843`. [Estimador](VOZ_PASO_OBSERVABLE_PROTOCOLO.md),
[alternativa por carga](VOZ_CARGA_OBSERVABLE_PROTOCOLO.md),
[escena de nota](VOZ_NOTA_OBSERVABLE_PROTOCOLO.md),
[QA](../evidence/observed_note_tests01.json).

## Reducción de costo observada

Se mantienen las 250 ecuaciones, ambos LM741 completos, memorias de
junturas/capacitores, Newton, solver, puertos y cargas. Cambia el estimador
temporal: observa los nodos físicos y deja los interiores 741 fuera de
ese estimador. Es una aproximación temporal, sin reducción espacial.
Las tensiones internas excluidas no tienen la precisión temporal anterior
acreditada. No cambian las tolerancias de Newton.

| Perfil, máximo completo | Referencia estricta de 24 ms | Paso observable de 24 ms |
|---|---:|---:|
| Estricto 4 µs / observable 64 µs | 26669 Accepted; 406.968 s | 5009 Accepted; 103.641 s |
| Estricto 2 µs / observable 32 µs | 31916 Accepted; 459.157 s | 5019 Accepted; 105.734 s |

Bancos separados en el mismo host/compiler: ratios de tiempo 0.255/0.230,
aproximadamente cuatro veces más rápido en esta escena. Comparación
exploratoria; no hubo repeticiones alternadas de costo total. No implica
el mismo ahorro en todas las escenas ni admisión de deadline.

[Contraste de 24 ms](../evidence/observed_voice_audit01.json): 193 clocks
incluido DC; error RMS J7 máximo 0.000970 %, máximo 0.001775 % y media
≤0.312 nV frente al perfil estricto fino. Tensión/corriente y 12550 filas
originales seleccionadas pasan los gates fijados previamente.

La [alternativa con piso de 2 pC](../evidence/charge_observed_voice_audit01.json)
también pasa: 4037/4050 Accepted y error RMS J7 ≤0.007864 % en 24 ms.
No acredita un ahorro adicional de tiempo; hubo concurrencia durante su
perfil fino. Se conserva como experimento y se usa la primera política
para la nota, que dispone de un contraste de costo más claro.

## Nota con gatillo sostenido y retirada

[Trayectorias](../evidence/observed_note_native01.json): KEY 0→10 V a
1 ms, 10→0 a 75 ms, fin 100 ms. Dos historiales nuevos y continuos;
21301/21344 Accepted, 555.234/553.343 s por perfil, ejecutados en paralelo.
Todos los HIGH/LOW pertenecen a la misma historia de cada perfil, sin
repetir ciclos, concatener notas o reinicializar en eventos. La historia
anterior de 164 ms permanece intacta.

[Auditoría](../evidence/observed_note_audit01.json): 801 relojes comunes,
12550 filas originales seleccionadas de 251 incógnitas y BUS <0.001 pA.
Error RMS J7 entre perfiles 0.0000310 %, máximo 0.0002396 %;
error máximo 32.211 nV. R59/R60, nodos observados y estados de la cadena
pasan. El prefijo compartido hasta 6 ms se contrasta con la referencia
estricta: 49 clocks por perfil. Los 94 ms restantes tienen refinamiento
y ecuaciones originales seleccionadas, sin trayectoria estricta propia.

| Tiempo | C2 volumen | C5 filtro |
|---|---:|---:|
| 6 ms | 2.077808103 V | 5.239186203 V |
| 75 ms | 5.025226826 V | 5.099594723 V |
| 100 ms | 4.166291275 V | 1.373496236 V |

La retirada de KEY inicia la evolución posterior con memoria; C2 sigue
por encima de 4 V al final. No se demuestra liberación completa ni una
nota de 500 ms. Condición inicial C1=0 impuesta sólo en DC; panel fijo,
C11/C12 OFF, S abierto y segunda VCA a 2 V según la escena heredada.

## Escucha local y alcance

[Exportación](../evidence/observed_note_listening01.json): dos WAV locales
de **100 ms reales**, 4800 frames mono PCM16 a 48 kHz. PCM idéntico por
SHA256. Fuente J7 a 8 kHz, sinc/Hann 64 taps y banda nominal 2.8 kHz;
ganancia fija 4 muestras/V, sin quitar DC ni normalizar picos, fades de
0.5 ms. Pico 0.054485 FS; RMS 0.016364 FS. La ventana corta termina con
memoria activa y su borde tiene fade; no representa una liberación completa.

Ubicación privada: `references-local/observed-note-listening01/`.
El audio y la evidencia eléctrica no identifican el parecido con hardware.
La simulación sigue costando unos nueve minutos por 100 ms. Es un oráculo
para reducción posterior de VCO/741 y cadena, con error de señal/puertos
medido; todavía no es un motor de plugin utilizable en tiempo real.

## Reproducibilidad y preservación

Fuentes/biblioteca/compiler congelados, sin Cargo, biblioteca ni cache
nuevos. Gzip de las dos trazas verifica restitución exacta y SHA256 antes
de retirar únicamente sus intermedios nuevos. Se conservan los estados
completos, propuestas continuas, DC y etapas seleccionadas.

Tres fallos del arnés (export del solver, ruta existente y literal Rust)
quedan preservados con fuentes y replay sin cambios antes de reparar.
No fueron rechazos eléctricos. [Guardas](../evidence/observed_voice_rollback02.json):
NaN y 41 V preservan el estado por bits; después, el mismo workspace
produce el candidato válido idéntico a uno nuevo. Cada trayectoria incluye
cuatro rechazos atómicos de intervalo/KEY. 255 tests anteriores se heredan
por identidad; no se atribuye una reejecución de esos tests a esta campaña.
