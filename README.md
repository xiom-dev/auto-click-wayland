# auto-click-wayland

Petite adaptation personnelle de l'application originale **Clicker**
(`net.codelogistics.clicker`, GTK4 / libadwaita, Wayland), avec un raccourci
**F9** global et un délai de lancement réglable. Un paquet **Flatpak prêt à
installer** est fourni.

Basé sur le projet d'eyekay (Codeberg : `eyekay/clicker`), licence GPL-3.0-or-later.

## Utilisation

- Lancer l'application
- Régler les paramètres à votre guise (délai, touche, intervalle, durée…)
- Appuyer sur **F9** pour lancer l'auto-click
  - confirmer l'écran : autoriser l'interaction à distance et le partage
- Placer la souris à l'endroit voulu (selon le délai choisi)
- Pour stopper l'auto-click, appuyer de nouveau sur **F9**

## Nouveautés de cette version

- **F9** lance **et** arrête l'auto-click, même quand une autre fenêtre est au
  premier plan. Le bouton **Start** fait aussi Start / Stop.
- **Délai de lancement réglable** (menu *Delay*) : `Instant (0 s)`, `1 s`, `5 s`,
  `15 s`, `30 s`, `1 min`, appliqué au bouton Start **comme** à F9.
  ✅ Le délai n'est **plus by-passé** : pour un départ immédiat, choisir `Instant`.
  *(Corrigé au passage : « 15 seconds » attendait en réalité 10 s.)*
- Valeurs par défaut d'usage : intervalle **1 ms** (cadence maximale), durée
  **600 minutes** (10 h).
- Runtime migré vers **GNOME 50** (l'original ciblait GNOME 46, en fin de vie
  depuis avril 2025).

## Installation

Télécharger `clicker-F9.flatpak` puis :

```bash
flatpak install clicker-F9.flatpak
flatpak run net.codelogistics.clicker
```

Si le runtime GNOME 50 manque, Flatpak propose de le télécharger automatiquement
(nécessite le dépôt Flathub).

## Contenu du dépôt

| Fichier | Rôle |
|---|---|
| `clicker-F9.flatpak` | 📦 L'application **prête à installer** (un seul fichier). |
| `window.py` | Le **code source** modifié (F9, délai, cadence/durée). |
| `clicker-local.json` | Le **manifeste de build** Flatpak (runtime GNOME 50, libportal 0.8.1 ; gtksourceview fourni par le runtime). |
| `clicker-f9-backup.patch` | Les modifs sous forme de **patch** git, réapplicables sur un clone propre. |
| `it.po` | Petit correctif de la traduction italienne. |

## Reconstruire depuis les sources

```bash
git clone https://codeberg.org/eyekay/clicker.git
cd clicker
git apply /chemin/vers/clicker-f9-backup.patch
flatpak run org.flatpak.Builder --user --install --force-clean build-dir clicker-local.json
```

> Le manifeste `clicker-local.json` référence le code par un chemin absolu
> (`"path"`). Adapte-le à l'emplacement de ton clone si besoin.

## Bon à savoir

- Sous **GNOME / Wayland**, l'autorisation « bureau à distance » est redemandée à
  **chaque** démarrage : c'est une limite volontaire de GNOME, non contournable.
- L'interface s'affiche en **anglais** (pas de traduction française fournie).
- Les réglages **ne persistent pas** entre deux ouvertures (l'app repart sur ses
  valeurs par défaut à chaque lancement).
