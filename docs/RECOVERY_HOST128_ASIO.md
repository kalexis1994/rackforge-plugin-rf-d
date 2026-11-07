# Alternativa ASIO para 128 frames

2026-11-07. WASAPI compartido informó 480 frames a 48 kHz y exclusivo
informó mínimo de 3 ms. Consultar el rango, tamaño preferido, granularidad
y frecuencia de los cuatro controladores ASIO instalados. Usar la
biblioteca ya compilada de RackForge y un proceso por consulta, con dos
intentos acotados. La consulta no crea búferes, no abre el panel del
controlador y no solicita cambios de frecuencia ni de configuración.

Un rango que incluya 128 sólo acredita una opción para intentar abrir.
Para admitir la ruta, el banco debe crear búferes de 128, confirmar
48 kHz y observar avances consecutivos de 128 en el reloj de muestras
del controlador. Los bancos y gates siguen el protocolo principal.

ASIO4ALL v2 informó 64–2048, paso 8 y preferido 512. Es el único
candidato de los cuatro consultados. Abrir dos canales de salida en
silencio con 128 y cambiar la frecuencia para el banco. Leer la
frecuencia efectiva y restaurar la original al cerrar cada stream.
Verificarla con otra consulta al terminar la campaña. Conservar los
mensajes de cambio de frecuencia, reset, resincronización o sobrecarga.
Rechazar avisos durante la campaña, posiciones sin validez y cualquier
avance distinto de 128. Conservar todos los eventos, incluidos los
primeros. La entrega y el reloj medidos corresponden al controlador.

La consulta posterior de la primera campaña devolvió 44.1 kHz y un
tamaño preferido de 128. El controlador guardó el tamaño solicitado.
Restaurar el preferido original de 512 con creación y liberación de
búferes sin iniciar el reloj. Confirmar frecuencia y preferido con
una nueva carga del controlador. Conservar la consulta anterior y
la posterior.

Crear y liberar 512 sin iniciar el reloj no restauró la preferencia.
El intento y su replay quedan en el recibo. El controlador instalado
guardó DefaultBufferSize=128 en el perfil calculado a partir de la
ruta del ejecutable temporal. Quitar el override de ese perfil con
el valor 0 y confirmar 512 y 44.1 kHz en otro proceso. El banco
reutilizable guarda y restaura el valor previo de ese único campo.
[Perfiles por aplicación de ASIO4ALL](https://asio4all.org/about/developer-resources/user-registry-settings/).
