# Corrección del adaptador de laboratorio

2026-10-08. El intento 01 no compiló: solve_linear_sparse es pub(crate) y no puede importarse desde un ejecutable ajeno al crate. El fallo y su compilación repetida sin cambios están preservados; no se ejecutó física.

El intento 02 copia literalmente max_abs, solve_linear_sparse y solve_linear_internal desde output_conversion.rs a un módulo privado del ejecutable. Conserva tipos de error y algoritmos; sólo corrige la visibilidad del adaptador. El publicador verifica los bytes de las tres funciones y las únicas sustituciones declaradas del núcleo/controlador. No modifica archivos Rust de producción ni el protocolo eléctrico. Fuentes del intento 01 archivadas antes de corregir el adaptador.
