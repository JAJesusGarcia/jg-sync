# JG Sync Architecture

## Objective

JG Sync is a real-time BPM detection and show synchronization application for live visuals, lighting and events.

## Initial architecture

The first prototype will be divided into independent modules:

```text
Audio input
    ↓
Audio capture engine
    ↓
Beat and onset detection
    ↓
BPM calculation
    ↓
Tempo stabilization
    ↓
Application interface
    ↓
Synchronization outputs