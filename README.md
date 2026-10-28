# DeepSpace Articles

A bilingual collection of two long-form engineering essays from the DeepSpace project.

## 1. From Expansion to Convergence

**Chinese:** [zh/从展开到收束.md](zh/从展开到收束.md)
**English:** [en/from-expansion-to-convergence.md](en/from-expansion-to-convergence.md)

How a general-purpose agent runtime evolved from capability expansion to system convergence:
thin UI, thick capability; single source of truth; five-layer compression; evidence-based
verification; one agent level by default and at most two.

## 2. Development as a Verifiable System

**Chinese:** [zh/把开发做成一个可验证的系统.md](zh/把开发做成一个可验证的系统.md)
**English:** [en/development-as-a-verifiable-system.md](en/development-as-a-verifiable-system.md)

A cross-project engineering method: four loops (intent, evidence, convergence, memory),
six costs, five working principles, small commits, short-branch validation, and reusable
templates.

## Layout

```
DeepSpace-Articles/
  README.md
  zh/       Chinese originals
  en/       English translations
  assets/   Figures used by the articles (PNG)
  assets/svg/  Editable SVG sources
```

## Figures

The second article uses four figures:

| Figure | PNG | SVG source |
|---|---|---|
| Fig. 1 — Two readings of MVP | `assets/fig1-mvp-two-readings.png` | `assets/svg/fig1-mvp-two-readings.svg` |
| Fig. 2 — Module boundaries | `assets/fig2-module-boundaries.png` | `assets/svg/fig2-module-boundaries.svg` |
| Fig. 3 — Commit strategy | `assets/fig3-commit-strategy.png` | `assets/svg/fig3-commit-strategy.svg` |
| Fig. 4 — Branch validation | `assets/fig4-branch-validation.png` | `assets/svg/fig4-branch-validation.svg` |

Both language versions reference the same `../assets/` paths, so the folder is portable as a
whole. When publishing on a blog or an image-hosted platform, upload the PNGs first and replace
the relative links with the hosted URLs.

## Notes

- The Chinese files are the originals; the English files are full translations, not summaries.
- Company names, client names, device identifiers, and internal addresses have been removed.
- The articles are written for engineers; the numbers and mechanisms are backed by the source
  repository, the local session database, or archived design records. Claims that are
  experience-based (for example, the 14B local-model threshold) are labeled as such.
