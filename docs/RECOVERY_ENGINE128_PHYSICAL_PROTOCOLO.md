# Recuperación de HD Audio y confirmación física

2026-11-07. Consultar ASIO4ALL con el nombre y la ruta del
ejecutable del banco. Si reaparece el par `HD Audio output 1/2`
con formato de cuatro bytes, conservar la configuración encontrada.
Si falta, limitar cualquier prueba de habilitación al perfil del
banco y a una salida HD Audio visible en Windows. Conservar el
estado previo de ese perfil y los recibos de los intentos.
[Configuración por aplicación](https://asio4all.org/about/developer-resources/user-registry-settings/)

Conservar los bytes del invitado O2 con LTO, el FIR contiguo
y el host RackForge `37e5f803`. Vincular el núcleo a las
tres reservas y a los 9288 frames del banco del FIR. Exigir
la misma captura de 2048 frames antes de medir y el mismo
par HD Audio al abrir cada stream. El driver recibe silencio.

Repetir la afinidad fija con la condición previa de cuatro
ventanas de 250 ms. Exigir al menos 70 % de inactividad global
y 90 % de ciclos ociosos relativos en ambos hermanos del
núcleo elegido. Confirmar con un control silencioso y dos
pases nuevos de 4800 callbacks a 48 kHz. Verificar la CPU
elegida y el avance de 128 muestras con alternancia de búfer.
El presupuesto es la mitad del período y cubre todos los
callbacks, incluida la preparación del primero. Exigir cero
plazos perdidos, avisos, asignaciones de render y fallos de
slot. Conservar ambos pases aunque uno sea rechazado.

Si la pareja física anterior queda fuera de margen, probar
una captura de afinidad fija con menos trabajo de diagnóstico.
Excluir las lecturas de CPU por hilo que fallaron la calibración
de resolución y omitir el sondeo de inactividad durante el
stream. Mantener los contadores de ciclos, la pared completa,
la verificación de CPU y el reloj físico. Antes de cada banco,
exigir cuatro ventanas con al menos 85 % de inactividad global
y el mismo 90 % relativo en ambos hermanos. Repetir el control
silencioso y dos pases nuevos, sin combinar parejas entre
variantes.

Contrastar la misma captura ligera con el paquete O3 con LTO
del banco anterior. Verificar su propio hash, sus reservas y
el FIR asociado. La política, el reloj, el dispositivo y los
umbrales de admisión permanecen iguales.

Restaurar el búfer y la frecuencia del perfil de ASIO y
retirar artefactos del área temporal. Mantener el VCO y
los contornos fuera de la prueba.
[Banco anterior](RECOVERY_ENGINE128_SMT_RESULTADOS.md)

Si la salida digital del monitor NVIDIA se habilita en el
perfil del banco y se enumeran dos veces exactamente
`High Definition Audio 1/2` con formato de cuatro bytes,
confirmar esa ruta por separado. Exigir el mismo par en
el control silencioso y en cada pase largo. Repetir las
pruebas de reloj, 128 frames efectivos y presupuesto de
pared íntegro. Registrar la selección de dispositivo y
conservar la configuración de los demás perfiles.

Si el banco NVIDIA tiene avisos del driver o excede el
presupuesto, repetir una sola vez la campaña completa sin
cambiar el paquete, el perfil, la política ni los umbrales.
Conservar las dos campañas completas y evaluar cada pareja
junto con su propio control.
