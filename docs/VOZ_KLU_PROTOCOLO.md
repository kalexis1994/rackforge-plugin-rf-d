# Voz acoplada: backend KLU y banco de admisión

Fecha: 2026-10-05. El diagnóstico 89e999f completa 10 ms de unión con
KLU, pero el caso desacoplado todavía falla. Esto acredita una opción
de cálculo, no una explicación completa de precisión/condicionamiento.
Se conservan todos los controles negativos de Sparse, BE y newtrunc.

Mismas ecuaciones, tarjetas, valores, fuentes y tolerancias Newton que
[la unión anterior](VOZ_CIRCUITO_PROTOCOLO.md); ningún capacitor retirado,
ninguna resistencia serie o carga de dispositivo agregada. Cambia sólo
la factorización lineal a KLU, documentada en NG-46 p. 316 y confirmada
por log. Se conserva gmin=1e-12; no se interpreta como fuga identificada.

Antes de medir se declaran **11 escenas de 40 ms**, observación desde
20 ms: nominal Gear2 500/250/125 ns, Trap2 125 ns, cutoff 0.2/0.8,
contorno 0 V, base Q21 0 V, triángulo, pulso angosto y salida a 10 kohm.
Los controles y trims restantes siguen el protocolo anterior.

Gates: tres contrastes de frecuencia <=1 cent, extremos BUS/recuperación/
salida <=5 mV, RMS <=1% + 10 microvolt; balance C2 <=0.1 nC en todas
las escenas. La integridad y reloj completo se comprueban por corrida.
La frecuencia puede variar físicamente por cargas; el gate compara
métodos/refinamientos de la misma escena y no exige pitch idéntico al
VCO aislado. No se heredan los gates de la placa 4 con entrada impuesta.

Periodos, DC, mute y cambios de forma se reportan. Una repetición de ciclo
para escuchar exige comparación de dos ciclos finales <=5 mV y tratamiento
de banda/DC/nivel declarado. El banco no incluye envolventes ni VCO2/3,
no identifica una unidad vintage y no admite todavía el motor portable.
