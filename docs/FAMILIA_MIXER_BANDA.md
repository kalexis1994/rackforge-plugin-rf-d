# Refinar la banda sin cambiar reserva o corriente de aceptación

El candidato H64 completa sus pasos con cero heap/KCL/carga, pero rechaza
BUS DC en -2.6/L0: 11.44948 uV frente a 10 uV. El replay confirma el
rechazo. Error armónico BUS 0.0423 uV; ondas y corrientes pasan. Conservar
ese candidato y sus estados: no declarar admitido el acoplamiento H64.

El seguimiento de C27 depende de la integral del reset, además de los
primeros armónicos. Probar H128 a partir de las mismas ocho ventanas
densas entrenadas; sin otras curvas, trims o ajustes de puntos reservados.
Los primeros 65 coeficientes por canal deben coincidir por bits con H64.
Conservar la generación H64 y su API activa por bytes; crear datos/kernel
separados para el candidato H128. Cambiar sólo el número de armónicos
en las dos sumas y el enlace de datos. Frecuencia/interpolación iguales.

Mantener todos los límites, en particular BUS 10 uV y corrientes 2 nA,
además de los perfiles 500/250 ns y balance de carga. Si H128 falla,
registrar fallo/replay antes de otra decisión. No convertir los picos
de la serie en fidelidad vintage ni modificar la escucha actual.
