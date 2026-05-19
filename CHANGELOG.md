# Changelog

## 9.6.0 - 2026-05-19

- corregido el flujo demo-owner para que frases mixtas como `Ah vale. El nombre de mi negocio se llama...` entren al bind real del negocio y no caigan otra vez en onboarding o en modo paciente
- eliminado el escape que permitía rescatar respuestas inválidas del LLM en el quality chain del demo
- sincronizado el `business_name` del send guard en la ruta real de `_send`, evitando rescates genéricos como `Hola! Soy Conny` o pedidos repetidos del nombre del negocio
- endurecido el clasificador demo para no tomar `mi nombre es...` como nombre de negocio ni usar señales demasiado genéricas como `vale` o `tengo` para saltar al flujo de cliente
- ajustado el send guard para no marcar respuestas de memoria directas como `Te llamas Santiago` como si estuvieran cortadas
- añadidas regresiones para bind con prefijo conversacional, rescate de fragmentos severos y memoria corta del nombre del dueño

## 8.2.0 - 2026-05-11

- añadido soporte multilenguaje real en el runtime público y liberado en npm
- reforzada la regla de idioma en demo y binding para que Conny espeje el idioma del dueño aunque no esté en la tabla de locales
- corregido el empaquetado npm para incluir `conny_i18n.py`, que antes quedaba fuera del tarball

## 8.1.1 - 2026-05-10

- corregido el flujo demo-owner en inglés para no tomar frases como `Just English sorry` o `I don't talk Spanish` como nombre de negocio
- endurecida la detección de idioma para mantener el inglés durante confirmaciones, correcciones y preguntas meta del dueño
- localizado el binding del negocio, confirmaciones de URL, correcciones y resets para que respeten el idioma activo del dueño
- afinados los heurísticos de nombre de negocio para distinguir mejor entre lenguaje/meta y nombres reales
- añadidas pruebas para onboarding demo en inglés, corrección de match equivocado y preservación del idioma en sesión

## 8.1.0 - 2026-05-09

- corrigido el filtro de frases robóticas para que deje de truncar salidas válidas del LLM
- invertida la prioridad de respuesta en demo/chat: el LLM decide primero y los fallbacks quedan como último recurso real
- endurecido el flujo demo para no rebinder confirmaciones como si fueran nuevos negocios y para mantener modo owner/admin sin secuestros
- productizado `smart_handoff.py` con persistencia completa de contexto, ack inmediato, timeout de 10 minutos y reanudación limpia
- añadido `conny_bridge.py` con memoria SQLite, `/history`, `/clear`, `/export` y prueba automatizada de continuidad
- añadido modo `conny_cli.py --non-interactive` para validación scripted del runtime
- reducidos `bare except` en `conny.py` y cubiertos con pruebas nuevas de bridge, handoff y filtros
- incluido el nuevo runtime auxiliar en el paquete npm
