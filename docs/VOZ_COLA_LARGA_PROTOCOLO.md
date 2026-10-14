# Cola cargada de 76,442 a 140,442 ms

Base `51ce79eb409d6e13d5e208c91e884a36d59fb171`, QA `voice_assembly_tests01.json`. Modelo vintage CA3046 documental y receta OSC1→BUS→escalera/VCA/J7 de las campañas anteriores; sin unidad física. Biblioteca `assembly_decay_voice/engine` ya admitida, sin recompilarla.

## Experimento fijado antes de medir

Continuar64 ms desde cada final propio de `extended-release01`:40077623296 ticks (76,442 ms) hasta73632055296 ticks (140,442 ms), tick125 ns/65536. Cortes cada419430400 ticks (0,8 ms),80 cortes y81 estados de rejilla por perfil. KEY0 V, S abierto, decay ON, PANEL_R16=1000 Ω. Todos los parámetros/cargas y458 HIGH/LOW se heredan. Sin nuevo evento. Cuatro avances completos de la unión por perfil se cotejan por bits con la familia block anterior; los3728 bytes del checkpoint deben conservarse.

Dos máximos de semipaso2/1 µs. Las puertas permanecen: LTE2 µV/2 nA, veinte intentos; red original KCL20 pA/restricciones200 pA, correcciones1 µV/1 nA; refinamiento de229 estados2 µV/2 nA, tiempos interpolados de reset≤10 ns y transiciones≤100 ns. Se exportan coarse/mid/end del primer/último Accepted y de cada reset o TURN/LATCH; restores reproducen hasta16 Accepted por bits, con máximo tres motores sombra activos.

Observar toda la corriente/derivada de C2 (balance≤2 µV/s), componentes seleccionados Decimal100≤10 fA y nueve filas de ΔQ≤1 pA×duración. Conservar puertos, seguidores, cargas de juntura y retornos. Componer ledger desde8,438 ms. La cuadratura de todos los estadios sigue siendo nativa; los endpoints sin solve original seleccionado no adquieren esa cobertura.

## Audio completo y publicación

Unir las cinco trazas reales: sostenido, liberación, control de resistencia, extensión anterior y cola nueva. Verificar cada unión por estado completo, fuente/receta y una muestra compartida única. Historia132,004 ms; WAV48 kHz de6336 muestras (132 ms), sinc18 kHz/Blackman,0,01 V/full scale. Sin loop, fades, normalización de pico o retiro de DC. Extensión constante solo para bordes del filtro; cuatroµs finales fuera del WAV por su rejilla. Refinamiento entre resoluciones≤2 µV/7 LSB; dos derivaciones completas idénticas. CLI con sidecar; rechazo previo de salida existente, estado incompatible y traza incompleta.

## Recursos y alcance

Productos privados nuevos≤192 MiB, reserva1 GiB; sin Cargo/cache/SPICE o nueva biblioteca. Stack de laboratorio32 MiB; cada perfil≤1800 s nativos/proceso≤1900 s, campaña≤4000 s y auditor≤600 s. Un fallo conserva fuente/recibo y replay sin cambios antes de reparar. Estos presupuestos son límites de laboratorio, no deadlines de audio. No se admite fidelidad física, voz completa desde silencio, periodicidad, descarga asintótica, heap nuevo medido o RT. La señal mayor sigue siendo una observación finita propia.
