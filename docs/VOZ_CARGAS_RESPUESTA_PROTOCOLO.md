# Respuesta conjunta de las cargas iniciales

2026-10-09. Model D clásico CA3046, misma escena del
[banco de ciclos](VOZ_CICLOS_SEMILLAS_PROTOCOLO.md). Fuentes físicas y
controles permanecen en ese banco: SVC-9 p.5, p.19/p.13/p.10.
Experimento de laboratorio para decidir cómo corregir la memoria.

## Pregunta y formulación

En cada una de las dos raíces anteriores, con C1 retenido a 0 V,
el condicionador resuelve `f(x)+E·i=0`, `Eᵀx=t`, 18 restricciones.
La tangente aumentada es `A=[[J,E],[Eᵀ,0]]`. Resolver
`A·[dx/dt;di/dt]=[0;I18]` y reportar todas las 218×18 entradas.
`S=di/dt` tiene unidades A/V y expresa respuesta estática con fase retenida.
No es la derivada del mapa periódico ni una matriz de Floquet.

Orientación: i positivo de a hacia b, igual a `C·dv/dt` en una
liberación sin corrientes de retención. Las referencias físicas fijas
se restan para Q absoluto; se cancelan en cambios bajo el mismo riel.
Reutilizar las 18 ramas y [semántica de rieles](VOZ_CARGAS_RIELES_NOTA.md).

## Medición fijada antes de ejecutar

- Dos raíces base, reconstruidas con el condicionador anterior sin cambios.
  Su estado y corrientes deben reproducirse por bytes.
- Cada una de las 18 restricciones se perturba ±1 mV y ±0,5 mV,
  conservando las otras 17 y la fase. 144 raíces perturbadas y dos bases.
- Newton y dominio permanecen iguales: 64 iteraciones, 24 halvings;
  residuo 1e-13 A/1e-11 V, corrección 2e-9 V/2e-12 A.
- Evaluador independiente anterior: 218 ecuaciones por raíz,
  residuo 2e-11 A/2e-10 A para estados de corriente/1e-11 V en restricciones;
  corrección 1e-6 V/1e-9 A. No buscar raíces independientes.
- Tangente: comparar con solve NumPy de J independiente. También comparar
  todas las columnas con diferencias centrales a ambas perturbaciones.
  Error permitido `1e-6 V/V + 3e-4·|respuesta|` para x de tensión,
  `1e-10 A/V + 3e-4·|respuesta|` para x de corriente e i.
  Reportar refinamiento central; no asumir orden observado si domina redondeo.
- SVD de S sin alterar unidades ni regularizar: publicar 18 valores
  singulares, rango (`s > s_max·1e-10`), condición y vectores extremos.
  Solo admitir inversión directa si rango=18 y condición≤1e10.

## Hipótesis de corrección, condicionada a la inversión

Para cada historia, inferir `m_k=C_k·Δv_k/Δt` a partir de estados
interpolados a fase rampa=-2 V entre dos resets. Comparar ambas resoluciones,
gate 1e-10 A por componente. Es una observación de deriva de carga;
no llamarla cuadratura Radau de las 18 corrientes.

Si S es invertible bajo el gate, calcular `δt=-S⁻¹m`. Residuo del solve
≤1e-12 A. Limitar el paso por `α=min(1,0,1 V/max|δt|)`.
Registrar δt, α, predicción lineal `m+S·αδt` y objetivos nuevos high/low.
Este límite es una política de exploración de memoria, no una constante
audible o tolerancia de parecido físico. No cambiar capacitancias o sesgos.

Si falla el rango o condicionamiento, conservar S y sus direcciones sin
invertir ni reemplazarla por una pseudoinversa. El rechazo también responde
la pregunta. Una predicción admitida sigue siendo una hipótesis pendiente
de cierre no lineal, liberación y ciclos propios a dos resoluciones.

## Recursos, identidad y alcance

Compilar solo un caller contra la biblioteca física congelada.
Stack 32 MiB; compilación 180 s, medición 180 s, campaña 600 s;
reserva 1 GiB más 12 MiB estimados de outputs. Preservar fuente, stdout,
stderr, outputs y replay de fallos antes de reparar.
QA conserva toda la evidencia anterior y bytes de documentos mutables.
Sin nuevas trayectorias, audio, SPICE, tests Rust, encendido físico,
periodicidad, fidelidad vintage o RT admitidos en este bloque.
