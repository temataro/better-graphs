# Witness fonts

Witness vendors static IBM Plex faces so figures render reproducibly without a
system font installation and accessible SVG/HTML can embed the matching webfont
files.

| Figure role | Family and face | Files |
|---|---|---|
| claim | IBM Plex Serif SemiBold 600 | `IBMPlexSerif-SemiBold.{ttf,woff2}` |
| working text | IBM Plex Sans Regular 400 | `IBMPlexSans-Regular.{ttf,woff2}` |
| emphasis | IBM Plex Sans SemiBold 600 | `IBMPlexSans-SemiBold.{ttf,woff2}` |
| boundary | IBM Plex Sans Italic 400 | `IBMPlexSans-Italic.{ttf,woff2}` |
| numeric ledger | IBM Plex Mono Medium 500 | `IBMPlexMono-Medium.{ttf,woff2}` |

The files are unmodified static builds from the official
[IBM Plex repository](https://github.com/IBM/plex). IBM Plex is licensed under
the SIL Open Font License 1.1; the repository's license text is preserved as
`IBM-Plex-OFL.txt` in this directory.

Matplotlib uses the TTF files registered by `witness.py`. `witness_export.py`
embeds the corresponding WOFF2 faces as data URLs, keeping SVG text selectable
while preventing browser-dependent font substitution.
