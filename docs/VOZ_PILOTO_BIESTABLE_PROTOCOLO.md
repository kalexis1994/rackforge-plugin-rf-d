# Núcleo de carga del biestable de volumen

Separar Q25/Q15 y las dos placas de C4 de 10 nF
del contorno cargado. Las cinco incógnitas son
C4_LEFT y las bases y colectores de Q25/Q15.
Conservar BE/BC y la corriente de base de Q17.
CR6, CR8, R28 y R40 conservan sus terminales
de frontera. El oráculo usa la revisión nominal
CA3046 y sus tarjetas de laboratorio.
[Biestable de referencia](VOZ_BIESTABLE_CARGADO_RESULTADOS.md),
[contornos cargados](CONTORNOS_CADENA_PROTOCOLO.md)

Exportar del solver acoplado las dos etapas de
cada paso de 8 ticks. Comparar los stamps del
núcleo con los del oráculo dentro de 0,2 pA y
2e−20 C. El núcleo avanza con sus propias cinco
tensiones desde un solo estado inicial. La
historia de C4 y la de las junturas gobiernan el
cruce del diferencial de colectores. Exigir el
mismo intervalo y sentido del evento en 76–81
positiva y ausencia de cruces añadidos en los
bordes negativos de KEY. Aplicar 20 µV por nodo.

Mantener el mismo reloj fino en un segundo
contraste y sustituir sólo los voltajes externos
por su interpolación desde 192 kHz. Así se prueba
si la frontera puede actualizarse al reloj del
piloto sin resolver el resto del contorno en el
evento. Las tensiones finas se usan únicamente
como estímulos de laboratorio. La integración
en RackForge requiere un productor autónomo de
esos voltajes y que su reloj pase el contraste.

En la ventana positiva, repetir cada combinación
de las cinco fronteras con paso fino e
interpolación a 192 kHz. Usar los mismos
límites de estado y de calendario. Registrar
el conjunto mínimo de fronteras finas. Los
ensayos mixtos sólo localizan la dependencia
eléctrica y no se usarán como entradas del
motor de audio.

Eliminar el nodo sin almacenamiento entre R36 y CR8
con la ecuación escalar de corriente de ambas ramas.
Conservar la ley exponencial y usar su derivada
en serie en el Jacobiano. Contrastar primero con
el colector de Q20 (x18) a paso fino en lugar
del ánodo de CR8 (x24). Repetir con x18 y x4
interpolados a 192 kHz y mantener finas las tres
fronteras restantes. Aplicar los mismos límites
de stamps, estado y evento a ambas pruebas.
