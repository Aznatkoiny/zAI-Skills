# Frontend & Design Optimization

Steer the visual output of the latest models, override their default house style, and improve vision tasks.

## Contents

- The Opus 4.8 design default (and why generic overrides fail)
- Strategy 1: specify a concrete alternative
- Strategy 2: propose options before building
- Frontend-aesthetics snippets
- Vision & the crop tool

## The Opus 4.8 design default

Opus 4.8 has a strong, persistent default house style: warm cream / off-white backgrounds (~`#F4F1EA`), serif display type (Georgia, Fraunces, Playfair), italic word-accents, terracotta/amber accents. Great for editorial, hospitality, and portfolio briefs; wrong for dashboards, dev tools, fintech, healthcare, or enterprise apps. It appears in slide decks too.

**Generic negative instructions don't work.** "Don't use cream" or "make it clean and minimal" just shift the model to a *different* fixed palette rather than producing variety. Two approaches work reliably.

## Strategy 1: specify a concrete alternative

The model follows explicit visual specs precisely. Give it a full tonal system, type direction, spacing, radius, motion, and an exact palette. Example skeleton:

```text
The visual direction should come from a cold monochrome atmosphere using pale silver-gray tones that gradually deepen into blue-gray and near-black, similar to a misted metallic surface. The page should feel sharp and controlled, with structure and restraint.

Use a square, angular sans-serif with wider letter spacing than usual in headings and navigation. Use 4px corner radius consistently across cards, buttons, inputs, and media frames. Margins should be generous.

Buttons should be flat and precise, with subtle hover changes using transition: all 160ms ease out.

Color palette should stay within this range:
#E9ECEC, #C9D2D4, #8C9A9E, #44545B, #11171B.
```

## Strategy 2: propose options before building

Breaks the default and gives the user control. Replaces the old `temperature`-for-variety trick and produces meaningfully different directions per run:

```text
Before building, propose 4 distinct visual directions tailored to this brief (each as: bg hex / accent hex / typeface — one-line rationale). Ask the user to pick one, then implement only that direction.
```

## Frontend-aesthetics snippets

Opus 4.8 needs **less** anti-"AI slop" prompting than earlier models. Minimal snippet (pairs well with the variety strategies above):

```text
<frontend_aesthetics>
NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white or dark backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character. Use unique fonts, cohesive colors and themes, and animations for effects and micro-interactions.
</frontend_aesthetics>
```

Fuller snippet for earlier 4.x models (Opus 4.5 / 4.6) or when more guidance is needed:

```text
<frontend_aesthetics>
You tend to converge toward generic, "on distribution" outputs. In frontend design, this creates what users call the "AI slop" aesthetic. Avoid this: make creative, distinctive frontends that surprise and delight.

Focus on:
- Typography: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics.
- Color & Theme: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes. Draw from IDE themes and cultural aesthetics for inspiration.
- Motion: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions.
- Backgrounds: Create atmosphere and depth rather than defaulting to solid colors. Layer CSS gradients, use geometric patterns, or add contextual effects that match the overall aesthetic.

Avoid generic AI-generated aesthetics:
- Overused font families (Inter, Roboto, Arial, system fonts)
- Clichéd color schemes (particularly purple gradients on white backgrounds)
- Predictable layouts and component patterns
- Cookie-cutter design that lacks context-specific character

Interpret creatively and make unexpected choices that feel genuinely designed for the context. Vary between light and dark themes, different fonts, different aesthetics. You still tend to converge on common choices (Space Grotesk, for example) across generations. Avoid this: it is critical that you think outside the box!
</frontend_aesthetics>
```

Also: request animations and interactive elements **explicitly** — they are not added by default.

## Vision & the crop tool

The latest models have improved vision and handle multiple images in context better, which carries over to computer use (screenshots, UI elements). Giving the model a **crop tool / skill** to "zoom" into relevant image regions produces consistent uplift on image evals. See Anthropic's crop-tool cookbook. For computer use resolution guidance, see model-tuning.md.
