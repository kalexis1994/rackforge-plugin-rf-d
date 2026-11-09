# Base jugable de RF-D con el criterio de RF-5

Separar el solver acoplado nominal CA3046 como referencia
offline y el camino audible de producción por bloques.
Empezar con el piloto ya contrastado a 192/384 kHz.
Mantener la misma sierra H128, el ladder, los VCA, J7,
el FIR y la conversión fija de 125 µV por escala completa.
La base tiene una sola sierra, cutoff y polarización fijos
y una rampa de laboratorio. La entrada MIDI selecciona
una nota monofónica grave en el rango 36–72.
[Derivación y contraste del piloto](VOZ_REDUCIDA_PILOTO_RESULTADOS.md).

Empaquetar el adaptador portable con una entrada MIDI y
una salida estéreo. Instalar el paquete en un almacén
temporal y enviar la partitura de ocho eventos por el
enrutador real de RackForge. Confirmar el hash de las
48.128 muestras estéreo contra el piloto archivado.
Medir dos instancias nuevas a 48 kHz con 128 frames,
cero eventos descartados, cero fallos de slot y un máximo
de 1,333 ms por bloque. Conservar fallos y repeticiones.
Publicar un único paquete local de audición al pasar
el contraste y el presupuesto offline.

Las incorporaciones siguientes deben conservar un
contrato de circuito por bloque. El primer acople usa
el piloto de retornos como referencia de puertos.
Los estados de C2/C5, las corrientes R59/R60 y el
evento del biestable se contrastan con el solver
antes de integrar sus modelos de tiempo real.
[Retornos](VOZ_PILOTO_RETORNOS_PROTOCOLO.md),
[gatillo y biestable](VOZ_PILOTO_GATILLO_PROTOCOLO.md).
