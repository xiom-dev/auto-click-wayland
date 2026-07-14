# Clicker-F9 — build modifié

Sauvegarde d'un **Clicker** (auto-clic natif Wayland via le portail `RemoteDesktop`)
modifié pour ajouter un raccourci global **F9** et améliorer le confort d'usage.

- **Bundle** : `Clicker-F9.flatpak` (≈ 199 Ko)
- **App ID** : `net.codelogistics.clicker` · version `0.1.8` · runtime `org.gnome.Platform 50`
- **Testé sur** : Debian Trixie, GNOME 48 (mutter 48.7 / xdg-desktop-portal-gnome 48), Wayland

## Installation

```bash
flatpak install --user Clicker-F9.flatpak
```

Le runtime GNOME 50 est récupéré automatiquement depuis Flathub (référence intégrée au bundle).

## Les deux versions comparées

| | Commit | Description |
|---|---|---|
| **Amont** (base) | `b11939c` | Clicker d'origine (dernier merge : traduction japonaise) |
| **F9** (ce build) | `28d39ff` | Version avec F9 + réutilisation de session |

Fichiers touchés entre les deux : `src/window.py` (l'essentiel) et `po/it.po` (correction).

## Changements (commits, du plus récent au plus ancien)

### `28d39ff` — Reuse the RemoteDesktop session across Start/Stop (2026-07-14)
Le prompt d'autorisation du portail n'apparaît plus qu'**une fois par ouverture de
l'appli**, au lieu de réapparaître à chaque Start (donc à chaque F9). La session
RemoteDesktop est gardée ouverte pendant toute la vie de la fenêtre ; seuls les
threads de clic démarrent/s'arrêtent. Fermeture propre à la fermeture de la fenêtre
(et si GNOME coupe la session). Suppression au passage d'une ligne morte
(`session.get_streams()[0][0]`) qui provoquait un **segfault** sur une session réutilisée.

### `33ab14c` — Revert « Persist RemoteDesktop permission… » (2026-07-14)
Annule la tentative ci-dessous : testée, **GNOME 48 refuse la persistance** des
sessions RemoteDesktop (`InvalidArgument: Remote desktop sessions cannot persist`),
ce qui cassait la création de session. Non applicable sur ce backend.

### `9628b3d` — Persist RemoteDesktop permission via a restore token (2026-07-14)
Tentative (révoquée) d'éviter le prompt à chaque **relancement complet** du flatpak
via `persist_mode=PERSISTENT` + `restore_token`. Conservée dans l'historique pour
documenter le cul-de-sac.

### `0587511` — Rework delay menu and make F9 honor the selected delay (2026-07-14)
- Menu **Délai** enrichi : ajout de `Instant (0 s)` et `1 second`, défaut à **1 s**.
- Lecture du délai **par index** (et non par libellé traduit) : corrige l'ancien bug
  « 15 seconds » → 10 s et rend le choix indépendant de la langue.
- **F9 respecte désormais le délai choisi** au lieu de forcer un démarrage instantané.
- Valeurs par défaut : intervalle **1 ms**, durée **600 min**.

### `2e7cb07` — Add F9 global shortcut and Start/Stop toggle for auto-click (2026-07-11)
- Le bouton **Start** bascule entre Start et Stop.
- Raccourci **global F9** : démarre/arrête l'automatisation instantanément, même quand
  Clicker n'a pas le focus.
- Threads de clic/frappe/motif interruptibles via `stop_event`.
- Correction d'une apostrophe manquante dans la traduction italienne (`it.po`).

## Limite connue

Un **redémarrage complet** du flatpak redemande l'autorisation du portail : c'est
incontournable sous GNOME, qui refuse la persistance RemoteDesktop (cf. `9628b3d`/`33ab14c`).
Tant que la fenêtre reste ouverte, une seule autorisation suffit.
