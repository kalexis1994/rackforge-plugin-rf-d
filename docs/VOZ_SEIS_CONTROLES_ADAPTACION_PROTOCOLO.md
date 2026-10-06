# Materialización del banco corto de seis correcciones

2026-10-06. Complementa el [protocolo activo](VOZ_NOTA_LARGA_SEIS_ACTIVO_PROTOCOLO.md)
antes de ejecutar sus controles. No modifica gates o el circuito.

- Reutilizar el control original build06 de 40 ms del banco anterior,
  identificado por recibo, deck, export, ejecutable, runtime y fuentes.
  Exigir 218786 filas y los 31 vectores completos, con reloj estricto.
  Registrar una referencia heredada; no contar una ejecución nueva ni
  copiarla como si fuese un resultado producido por build11.
- Medir build11 desactivado y activo frente a esa referencia. Conservar
  todos los bytes eléctricos del deck; cambiar sólo export. Antes de cada
  proceso limpiar flags de observación, replay, reducción y shadow.
  Admitir sólo el anuncio explícito `six-corrections` al activarse.
- Sólo con identidad y control admitidos, medir los cuatro perfiles
  conjuntos cortos. Un perfil rechazado no impide observar los otros
  perfiles independientes, pero detiene la fase dependiente de nota larga.
- Registrar los recibos completados a medida que llegan y el estado
  pendiente del banco. No modificar helpers entre inicio y final. Medir
  balances/contrastes sólo con las escenas completas necesarias.
- Antes del lanzamiento estimar ambos exports nominales a partir del
  original y los cuatro exports conjuntos a partir del banco corto de
  tres correcciones. Verificar suma más 2 GiB disponibles; son estimaciones,
  no cotas. El presupuesto sigue siendo 900 s por proceso.

Los auditores reconstruyen el cálculo de recursos, la referencia heredada,
el diff exacto de build11 y cada decisión, incluso si un control rechaza.
La fase de 350 ms mantiene su preflight propio, derivado de los nuevos
recibos cortos. No se prepara audio hasta admitir esa fase completa.
