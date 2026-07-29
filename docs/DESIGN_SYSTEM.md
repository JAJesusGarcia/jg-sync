# JG Sync Design System

Version: 0.1

---

# Philosophy

JG Sync is not a BPM detector.

JG Sync is a professional synchronization engine built for live shows.

Every design decision must answer one question:

> Does this help an operator during a live performance?

If the answer is no,
it does not belong in the interface.

---

# Design Principles

## Zero distractions

The interface should never compete with the show.

No unnecessary animations.

No decorative graphics.

No visual noise.

Only essential information.

---

## Maximum confidence

The software should always communicate its confidence.

Users should never wonder:

- Is it detecting?
- Is it locked?
- Is it recalibrating?

The application must answer those questions visually.

---

## One glance UX

An operator should understand the application in less than one second.

Everything important must be visible immediately.

---

## Professional aesthetics

Inspired by:

- MA Lighting
- Blackmagic Design
- Resolume
- Linear
- Raycast
- Apple

Avoid consumer app aesthetics.

Avoid gaming aesthetics.

Avoid RGB overload.

---

# Color Palette

Background

#0B0D10

Surface

#15191F

Border

#262C36

Primary Text

#F5F7FA

Secondary Text

#8E98A8

Success

#22C55E

Warning

#F59E0B

Information

#60A5FA

Error

#EF4444

---

# Typography

Primary

Inter

Alternative

Geist

Numbers

JetBrains Mono

BPM should use tabular numbers.

Numbers must not jump horizontally.

---

# Window Structure

JG Sync contains two applications.

Monitor

Settings

Never mix both.

---

# Monitor

The monitor is always visible during the show.

It contains only runtime information.

Never configuration.

Never menus.

Never dialogs.

---

Layout

+------------------------------------+

JG Sync

● LOCKED

128.42 BPM

██████████████████████

Confidence

Audio Input

████████████░░░░░░░░░

Beat

● ● ● ● ● ● ● ●

+------------------------------------+

---

# Settings

Contains:

Audio

OSC

Ableton Link

MIDI

Advanced

Settings are not shown during live operation.

---

# States

CALIBRATING

Searching for a stable beat.

TRACKING

Following the rhythm.

LOCKED

Tempo is considered stable.

LOST

Tempo confidence has been lost.

---

# Motion

Animations should be subtle.

150–250ms.

No bouncing.

No exaggerated easing.

Everything should feel like professional equipment.

---

# Icons

Minimal.

Lucide Icons.

Outlined.

Never colorful.

---

# Spacing

Use multiples of 8px.

8

16

24

32

48

64

---

# Shadows

Very subtle.

Almost imperceptible.

No floating cards.

---

# Sound

No sounds.

Ever.

The application must remain silent.

---

# Future

OSC

Ableton Link

MIDI Clock

Beat Grid

Latency Monitor

Audio Monitor

Developer Tools

---

# Motto

Zero distractions.

Maximum confidence.

Built for live shows.