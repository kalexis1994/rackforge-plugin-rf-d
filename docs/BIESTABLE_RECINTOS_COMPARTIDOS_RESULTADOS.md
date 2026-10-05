# Una inversa uniforme para ocho soportes conocidos

El [protocolo](BIESTABLE_RECINTOS_COMPARTIDOS_PROTOCOLO.md) y productor
se congelan en `beaf917` antes de medir. Fuente: los ocho archivos completos
del [prefijo curvo](BIESTABLE_PREFIJO_CURVO_RESULTADOS.md), índices 8–15,
con referencias y RHS intactos. Cada alternativa empieza con el resultado
real original del octavo soporte, sus 22 memorias y P fija.

## Selección y alcance

La primera variante declarada, ancho **8**, cierra todo el banco en radio
**1 µV**. Las particiones 4, 2 y 1 no se miden: el protocolo detiene el banco
en la primera alternativa completa. El control de 0,1 µV rechaza en cada
soporte por la cota nodal entrante, sin construir otro recinto.

Se vuelve a certificar el mismo prefijo de **16 intervalos hasta ≈125 µs**,
extremo exacto `4611686018427389/36893488147419103232` s. Pico acumulado
**≤0,793 µV**, heredado del tramo siete. No se amplía el tiempo certificado:
se prueba una alternativa de certificación sobre las mismas referencias.
`first_gap_index=null`, `stop_reason=declared_limit`.

X se elige en el soporte **11**, u=1/2, por la regla ordinal central inferior
prefijada; descriptor Decimal100 e inversa candidata binary64. Se prueba
la identidad de constante y stamps analíticos sobre las ocho referencias.
El ledger conserva **704 rangos Bernstein completos**: 88 leyes por ocho
curvas. Su unión se infla por el tubo completo de 1 µV. La codificación
afín de cada rango escalar no cambia las curvas físicas del control.

El recinto del descriptor medio completo 119×119 cumple **q≈0,0582118261<1**.
Se obtiene una inversa intervalar y tres certificados de tasa, independientes
del forzamiento, sobre todo ese dominio. Cada macrocelda recalcula acciones
firmadas con esa X, defecto y cola nuevos; conserva todos los restos
constitutivos y uniformes independientes. Ninguna acción antigua se reutiliza.

## Transporte y comparación

| Índice | Pico local, µV | Error final real C7, µV |
| --- | --- | --- |
| 8 | 0.331495871 | 0.331444205 |
| 9 | 0.336985970 | 0.336933350 |
| 10 | 0.342705085 | 0.342651397 |
| 11 | 0.348490619 | 0.348435743 |
| 12 | 0.354288419 | 0.354232183 |
| 13 | 0.360080523 | 0.360022658 |
| 14 | 0.365861080 | 0.365801161 |
| 15 | 0.371628349 | 0.371565702 |

Los picos locales siguen en nodo 81, celda [7/8,1]. El último aumenta
≈4,67 pV frente al control con recintos individuales; ambos permanecen
≤0,372 µV local y ≤0,793 µV acumulado. Las 22 memorias se transportan con
cada duración real, sin reset. Los endpoints y restricciones RC/Q se conservan.

| Coste de certificación de los ocho soportes | Control | Compartido |
| --- | --- | --- |
| Candidatos nuevos de precondicionador | 72 | 1 |
| Recintos de inversa nuevos | 64 | 1 |
| Consultas LDL de tasa nuevas | 6336 | 99 |
| Acciones de subcelda nuevas | 512 | 512 |
| Solves no lineales / sistemas nuevos de métrica | 0 / 0 | 0 / 0 |

Las pruebas de inversa y consultas de tasa disminuyen **98,4375%** en este
banco. El coste de construir las burbujas, referencias y RHS originales ya
se pagó en el control y se amortiza por identidad; no forma parte del único
candidato nuevo. Las acciones y todos los cierres se recalculan. Estos
conteos no son una medida de velocidad o deadline del motor de audio.

## Evidencia y continuación

[Archivo completo](../evidence/loudness_latch_bdf_static_precision_shared_covers.json.gz):
87573101 bytes comprimidos, SHA
`e7bdf4fe337c70cbefb473f0504fb4b2b326818c298bd8a2ef310c63692d933b`,
canónico `6a0b8ef5e21a8a99b01ecc180fd3094b90b3aeb2271539e8b3aeac092c0250e3`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_shared_covers_summary.json).
Datos, seis tests y validator se congelan en `9f88fd1` antes de validar.
[Corpus y recibos](BIESTABLE_RECINTOS_COMPARTIDOS_ENTRADAS.md).

El archivo adicional equivale a ≈66,96% del tamaño de los ocho archivos
del control (130783176 bytes), pero los contenidos y organización difieren:
referencias/RHS originales se enlazan por identidad. Ambos conjuntos se
conservan; el corpus total crece. No se suprimen certificados nuevos.

Modelo CA3046 nominal con parámetros sintéticos; circuito, integrador y
gates intactos. 1 mV global, identificación física, voz, audio y deadline
siguen abiertos. Próximo: [continuación sobre referencias nuevas](BIESTABLE_CONTINUACION_COMPARTIDA_PLAN.md).
