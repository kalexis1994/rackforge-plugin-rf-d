# Escucha del VCO nativo nominal

Ejecutar sólo después del banco30 ms Radau250/125 y conformidad nominal
contra referencias archivadas admitidos. VCO aislado, C4=10 pF, sin
calibración de trims; controles y carga de mixer impuestos. No voz completa.

Usar el último ciclo real del perfil125, entre sus cruces crecientes
C1=−2 V; conservar knots no uniformes y puntos interpolados de frontera.
No construir ondas analíticas. Reusar `coefficients`/`synthesize`/`save`
del renderer anterior por identidad: integrales Fourier exactas del
interpolante lineal por tramos, omitir DC y armónicos por encima0,45 Fs.
48 kHz, PCM16 mono, 8 V/full scale fijo, fades10 ms, sin normalización
individual o clipping. Cada onda0,75 s; montaje saw/tri/pulse con pausas
0,15 s, total2,55 s. No simular2,55 s de circuito: repetir un ciclo derivado
de la trayectoria nativa completa30 ms, conservando esa distinción.

Recibo identifica fuentes, segmentos, ventana, coeficientes, escala,
DC retirado, hashes de WAV y formato recuperado. Recalcular coeficientes
al publicar, comprobar payload PCM por bytes y amplitud sin clipping.
WAV únicamente en artifacts ignorado. No SPICE nuevo ni VCO conectado
a filtro/VCA/host. No sonoridad física o coste RT admitidos.
