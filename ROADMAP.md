# Westminster roadmap

Westminster is at **0.5.1 public beta** with playable 1979 and 2024 starts. This roadmap records what has shipped,
what needs continued attention, and the next major features. Detailed design decisions belong in
[westminster/PLAN.md](westminster/PLAN.md).

## Shipped

### 0.4 — Localization, dark interface and landless politics

- Added French, German, Japanese, Korean, Polish, Russian, Simplified Chinese and Spanish localization.
- Reworked the interface for dark mode, with clearer alerts and modern political art for the HUD, lifestyles, perks
  and traits.
- Improved landless political work and added playable campaigners from Just Stop Oil, Extinction Rebellion and
  Amnesty International. They can build support, form a party and seek election.
- Corrected political spouse titles and restored political intrigue options while keeping murder, abduction and
  seduction disabled.

### 0.5 — Margaret Thatcher, 4 May 1979

- Added the 1979 Commons, Thatcher's first Cabinet, the opposition, Elizabeth II and an election baseline based on
  the 1979 result.
- Added recognisable CK3 character models for Thatcher, Callaghan, Steel, Foot, Howe and other significant figures.
- Added complete bookmark art and corrected the main-menu and new-game presentation.
- Kept every starting constituency within the United Kingdom while retaining independence gameplay.

### 0.5.1 — Polish and onboarding

- Added a one-time in-game recommendation and feedback prompt after a year of play.
- Refined the Workshop presentation, adaptive thumbnail, screenshots, tags, change notes and discussion guides.
- Made smaller presentation and usability improvements.

## Current priorities

### Stability and performance

- Investigate start-up crashes reported by players with different DLC combinations.
- Profile the weekly and monthly systems that scan all 650 constituencies, especially majority, poll, trust and
  devolution updates.
- Reduce large generated textures where that can be done without visible loss.
- Continue long-campaign balance testing and improve AI behaviour after several election cycles.

### Complete the modern presentation

- Replace remaining medieval clothing and less-used medieval screens.
- Review every map, holding and sidebar icon at normal play size against the dark interface.
- Keep the 1979 and 2024 bookmark screens visually consistent as the shared presentation evolves.

### Make the first campaign easier to understand

- Expand the opening guidance for MPs, party leaders, prime ministers and landless campaigners.
- Surface the State of the Parties panel, working majority, Party Standing and route to selection more clearly.
- Turn common questions from the Workshop discussions into concise in-game help.

## 0.6 — The press

- **Running stories:** adapt CK3 legends into political stories such as a scandal, comeback or landmark bill that
  spread between constituencies and affect Profile and public trust.
- **Papers with leanings:** add a small group of fictional national and regional newspapers that frame the same
  story differently.
- **Editors as characters:** create landless editors whom politicians can court, feud with or seek endorsements
  from.
- **Election front pages:** let the publication backing the player shape election-night coverage.

The first implementation should be a small playable slice: one running story, three fictional papers and one editor
relationship. It should reuse existing trust, scandal, election and landless-character systems before adding more
content.

## Later

- More historical starts using the 1979 pipeline, working backwards through post-1937 prime ministers.
- Fuller House of Lords, mayoral and council systems.
- More careers for backbenchers, ministers, party staff, journalists, union officials and campaigners.
- More party, parliamentary and election events across both eras.
- Additional fictional parties and pressure groups that can become electoral movements.

## Design decisions still open

1. Whether the optional light interface is worth maintaining alongside the dark theme.
2. How many fictional newspapers 0.6 needs and whether they are national, regional or both.
3. Whether editors should use CK3's ordinary landless characters or dedicated landless titles.
4. Which historical start should follow 1979.
