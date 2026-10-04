# Protocolo adicional: escalas de tasa para el recinto post-KEY

Conservar íntegro el [primer protocolo](BIESTABLE_POST_KEY_PROTOCOLO.md) y
su medición. Ambas semillas convergieron, pero D_rate=1e-6 s no certificó
la caja de cargas DC: eta=3,7271e-5 V y q crece con el radio. Eso rechaza
esa prueba, no demuestra inexistencia del estado consistente.

Usar exactamente el candidato primario, cargas, Jacobiano y precondicionador
publicados, sin nuevas soluciones ni inversas. Fijar ahora un banco de pesos
de tasa 1e-9, 1e-12 y 1e-15 s, en ese orden, con D_voltage=1. Para cada peso
evaluar todos los radios 1e-9, 1e-8, 1e-7 y 1e-6 V del protocolo anterior.
No ajustar pesos después de medir. Seleccionar el primer par aceptado en
ese orden, conservando doce recintos y los rechazos.

La caja es anisótropa: radio r para potenciales y r/D_rate para tasas.
Las leyes no lineales sólo dependen de potenciales. Una caja amplia de
tasas no ensancha los exponentes; sí debe incluir todas las columnas de
masa exactas y el precondicionador aproximado en I-D*X*H*D^-1. Mantener
incertidumbre de las 25 cargas del DC y prueba exterior de todo el sistema.
El peso modifica la geometría de la prueba, no cargas, leyes o gates.

Al aceptar, separar error de potencial en V y error de tasas en V/s;
la cota de tasa es eta/(1-q)/D_rate. La norma no es una medida física
del crecimiento ni la norma de las ventanas temporales anteriores.
Registrar la identidad de la publicación de laboratorio ya congelada.
No afirmar certificado del estado high+low del integrador ni de una nueva
trayectoria. Las ocho restricciones de dominio, continuidad, reloj y
alcance del protocolo anterior siguen vigentes.

Validar replay de doce recintos, matriz escalada completa mediante un
Jacobiano de corrientes independiente, productos exteriores, monotonía,
incertidumbre de cargas, conversión de unidades, identidades y bytes.
Conservar intento de import fallido del primer helper con su versión Git.
El rechazo del gate backward binary64 permanece explícito. Gates global
1 mV, física, audio y deadline siguen abiertos.
