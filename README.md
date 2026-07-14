# Clicker-F9

Un auto-clic natif pour **Wayland/GNOME**, basé sur [Clicker](https://codeberg.org/eyekay/clicker),
avec quelques ajouts pour le rendre plus pratique — dont un **raccourci global F9**.

- **Fichier** : `Clicker-F9.flatpak`
- **Installer** : `flatpak install --user Clicker-F9.flatpak`
  (le runtime GNOME est récupéré automatiquement depuis Flathub)

## Ce qui a été ajouté

- **⌨️ Raccourci global F9** — démarre et arrête l'auto-clic depuis n'importe où,
  même quand la fenêtre n'a pas le focus (idéal en jeu ou en plein écran).

- **▶️⏹️ Bouton Start/Stop** — un seul bouton pour lancer puis arrêter (il bascule).

- **⏱️ Menu Délai amélioré** — nouveaux choix **`Instant (0 s)`** et **`1 seconde`**.
  Le F9 respecte le délai que tu as choisi.

- **🔓 Moins de demandes d'autorisation** — tant que la fenêtre reste ouverte,
  l'autorisation « contrôle à distance » n'est demandée **qu'une seule fois**,
  au lieu de réapparaître à chaque démarrage.

- **🎨 Nouveau logo.**

## Bon à savoir

Si tu **fermes puis relances** l'appli, GNOME redemande l'autorisation une fois :
c'est une sécurité de Wayland qu'on ne peut pas contourner. Tant que la fenêtre
reste ouverte, tu n'as rien à re-confirmer.
