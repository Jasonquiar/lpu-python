# lpu-python

Versión del curso *Backend con Python · EstudIA* de **Let's Play Ultimate (LPU)**: el núcleo backend para registrar partidos de Ultimate Frisbee. El planillero anota cada gol en el momento y capitanes y organizadores ven el marcador correcto.

> Todos los equipos y personas de este repositorio son **ficticios**.

## Ficha del proyecto

**Ámbito y quién usaría el servicio:** registro de partidos de Ultimate Frisbee. Lo usan el planillero (scorekeeper), que anota los goles, y los capitanes y organizadores, que consultan el marcador.

**Necesidad 1** (qué se registra, consulta o modifica): como planillero, necesito registrar cada gol en el momento en que ocurre, sin pasar después la planilla en papel a un Excel.

**Necesidad 2:** como capitán u organizador, necesito ver el marcador correcto y saber cuándo terminó el partido.

**Regla de negocio** (algo que el servicio nunca debe permitir o siempre debe cumplir): no se puede anotar un gol en un partido que ya terminó (un equipo llegó al máximo de goles, 15 por defecto), ni a un equipo que no está jugando ese partido.

| Caso | Entrada | Resultado esperado | Motivo |
|---|---|---|---|
| Aceptación | Partido 14-10, gol de "Equipo Rojo" | Queda 15-10 y el partido termina | El partido no había terminado y el equipo juega este partido |
| Rechazo por regla | Partido 15-10, otro gol | `GolRechazado` | El partido ya terminó |
| Rechazo por regla | Gol de "Equipo Verde" | `GolRechazado` | Ese equipo no juega este partido |
| Rechazo por dato inválido | Crear un partido "Equipo Rojo" vs "equipo rojo" | `ValueError` | Un equipo no puede jugar contra sí mismo |

**Qué dejo fuera por ahora:** torneo, categoría, jugadores, estadísticas (G, A, B, Callahan), tiempos, espíritu, W.O. y modo sin conexión. La lista completa está en el docstring de `src/modelo.py`.

## Cómo ejecutarlo

```bash
python3 src/modelo.py
```

## Estado

Distingue siempre qué está **ejecutado y comprobado**, qué está **simulado** y qué queda **pendiente**.

| Parte | Estado | Evidencia |
|---|---|---|
| Brief en el docstring de `src/modelo.py` | Escrito | Docstring de `src/modelo.py` |
| Modelo `Partido` con su regla | Pendiente | Aún tiene el código de la plantilla (`Recurso`) |
| Casos aceptado y rechazado | Pendiente | |

## Bitácora de decisiones

| Fecha | Decisión | Por qué |
|---|---|---|
| 2026-11-23 | La entidad es `Partido`, no `Torneo` | Es el corazón del sistema: lo que hace el planillero en la cancha |
| 2026-11-23 | `Partido` es una clase | Hay un estado que cambia (el marcador) y una regla que lo protege |
| 2026-11-23 | `goles_maximos` llega al crear el `Partido` y no cambia | En LPU lo define el líder de torneo al crear el torneo; `Torneo` queda pendiente |
