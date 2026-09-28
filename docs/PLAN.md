# Plan de investigación RACE para RF-D

## Fase A — Identidad y evidencia

1. Conseguir manual técnico íntegro y esquemas legibles; registrar hash, páginas y revisión.
2. Inventariar la unidad objetivo, placas, modificaciones y ajustes existentes.
3. Congelar la ruta de salida y el estado de calibración antes de usar audio como referencia.

**Salida:** `OBJETIVO.md` congelado, `FUENTES.md` completo y mapa de nodos por placa. Sin esta salida, no se promueven constantes al motor.

## Fase B — Capturas y oráculo

1. Preparar escenas secas por fuente, barridos de filtro, contornos, teclas y performance.
2. Capturar repetidamente la unidad con identidad de configuración y niveles.
3. Derivar un oráculo por bloque en unidades eléctricas; primero circuito nominal y luego variación observada.

**Salida:** resultados reproducibles y decisiones de aceptación predefinidas, siguiendo [CAPTURAS.md](CAPTURAS.md).

## Fase C — Motor portable

1. Implementar módulos separados para contrato/estado, control, osciladores, mezcla, filtro, contornos/VCA, salida y adaptador RackForge.
2. Comparar cada bloque con el oráculo y el equipo, incluyendo notas y controles reservados.
3. Optimizar WebAssembly/tiempo real sólo con errores medidos; conservar una ruta de referencia fuera de tiempo real.

**Salida:** pruebas de circuito y audio, matriz por bloque, perfil de CPU y plugin `.rfplugin` sin recursos privados.

## Fase D — Uso en vivo

Probar Note On/Off, retrigger, legato, glide, ruedas, cambios de preset del host y recuperación de estado. Mantener la voz mono y describir las comodidades de RackForge como extensiones de workflow. Validar transiciones sin discontinuidades accidentales ni asignaciones en el hilo de audio.

## Prioridad de la primera campaña

Comenzar por identidad de placas y captura limpia de **un oscilador aislado → mezclador → filtro abierto → VCA/salida**, y luego filtro autooscilante y contornos. Esa secuencia permite atribuir diferencias antes de ajustar el sonido completo.
