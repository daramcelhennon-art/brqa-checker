# Bond Radar deal-message checklist

For each detected stage, verify the Bond Radar `message` body contains every listed item, in roughly the canonical field order. Flag each item that is genuinely absent — do NOT flag items marked TBD / N/A / "tomorrow's business" and do NOT flag `type` mismatches (see [[feedback-bondradar-type-field]]).

## Canonical field order (most formats)

Issuer → Guarantors → Type of notes → Reg S/144A → COC → CUC → MWC → par call → Listing → Denoms → Law → UoP → Ratings → Bookrunners → ISIN → Timing.

## House-style ordering rules (do NOT copy source term-sheet order blindly)

Bond Radar has its own canonical phrasing. When the source term sheet orders fields differently, the BR message MUST rewrite them into house style. Watch especially for:

- **`MWC` precedes `par call`**, always — never `1-month par call, MWC`. Correct: `MWC, 1-month par call.` (Applies even when the term sheet writes it the other way round.)
- Follow the full canonical field order above rather than the source's bullet-order.
- More house-style rules live in the `anthropic-skills:bond-radar-deal-messages` skill — invoke it whenever a house-style flag is being evaluated so the ruleset stays authoritative.

## Do NOT flag (things the BR message intentionally omits)

- **Fixed-to-Floating coupon structure** on SNP / callable MREL notes. The Fxd-to-FRN switch after the first call is intentionally NOT stated in the BR message — `coupon 3.875%` with `callable from [date]` is complete. Never flag "coupon structure incomplete" or "fxd-to-frn missing".
- **CUSIP**. BR messages use ISIN as the primary identifier; CUSIP is not required and should not be flagged as missing, even for SEC-registered US corporate deals that only have a CUSIP in the term sheet. If the ISIN is missing at a stage that requires it (Priced / Final Terms), flag the ISIN — never the CUSIP.
- Interest payment schedules, day-count fractions, business-day conventions, waiver-of-set-off, statutory loss-absorption verbiage — regulatory boilerplate belongs in the prospectus, not the BR message. Do not flag missing.
- Target market / MiFID / PRIIPs KID language — also boilerplate; not required in BR.
- **`Sale into Canada`** language ("Sale into Canada Yes", "Sale into Canada Yes, via exemption", etc.) — NOT needed in BR messages. If it appears in a BR message, flag it as something to REMOVE. If it appears only in the source term sheet, ignore.
- **Quotes (`"..."`) around the BR message body** — do NOT flag by default. Quotes are the correct convention when we received a mandate direct from a bank (the body is a verbatim quote of the mandate wording). Only flag quotes if you have clear evidence the source was NOT a direct mandate quote (e.g. the message is a reformatted term-sheet, not a mandate).
- **Clearing** language ("Clearing: Euroclear/Clearstream", "CMU with linkage to…", "Fedwire, Euroclear, Clearstream", etc.) — NOT required in BR messages. Do not flag as missing at any stage. This applies to single-tranche BR bodies and to Common terms sections of multi-tranche messages.

## Stage detection heuristics

Detect stage by the opening line pattern in the Bond Radar `headline` + `message`:

- **IPTs**: opens `"IPTs are [level] for [Issuer] ..."`
- **Guidance**: opens `"Guidance is [level] for [Issuer] ..."`
- **Book update**: opens `"IPTs / Guidance / spread remains [level] for [Issuer] ..."` AND contains `"Book update: Books over ..."`
- **Final books**: contains `"Book update: Final books"` or `"Books closed over"` — typically appended to allocations
- **Final terms**: opens `"[Spread or yield] set at [level] for [Issuer] ..."`
- **Launched**: opens `"Launched: Size set at [size] and [spread/yield] is set at [level] for [Issuer] ..."`
- **Priced**: opens `"Priced: [Size], coupon [coupon], [maturity]. Reoffer [price], spread [spread]. Yield [yield]."`
- **Priced tap / add-on**: opens `"Price increased: [size] takes outstanding to [new nominal] ..."`
- **Multi-tranche**: contains a "Common terms:" paragraph and per-tranche `"Tranche A:"`, `"Tranche B:"`, etc.

## IPTs — required items

- [ ] Opening line matches: `"IPTs are [level] for [Issuer] [size] [tenor] [note]"`
- [ ] `Due [maturity date]`; if callable, add `"(optional redemption / first call date [date])"`
- [ ] Settle date
- [ ] Issuer name (full)
- [ ] Guarantors (if any)
- [ ] Type of notes (Senior Unsecured, Bail-inable FRN, Covered, etc.)
- [ ] Reg S / 144A / SEC Registered
- [ ] COC / CUC / MWC / par call (state each that applies, e.g. "3-month par call")
- [ ] `List [venue], denoms [e.g. 100kx1k]`
- [ ] Governing law
- [ ] UoP
- [ ] Ratings (issuer / expected issue)
- [ ] Bookrunners (flag B&D)
- [ ] ISIN (may be `TBD` at this stage — fine)
- [ ] Timing (e.g. "Today's business")

## Guidance — required items

Same as IPTs, except the opening line must be `"Guidance is [level] for [Issuer] ..."`.
Books/bookrunners and timing may have moved on from the IPTs version — that's fine; only flag missing items, not changed ones.

## Book updates — required items

- [ ] Opening line matches: `"IPTs / Guidance / spread remains [level] for [Issuer] ..."` (choose based on current status)
- [ ] Full deal-terms block, as per IPTs (all fields listed above)
- [ ] `Book update: Books over [amount]  _(or "Books above [amount]" — treat as equivalent, don't flag)_

**Book-line wording** — the prefix rule depends on the stage.

- **Pre-pricing (any stage up to AND including Allocations Out):** `Book update:` or `Books update:` prefix is FINE. IPTs, Guidance, Book Update, Spread Set, Final Terms, Launched, Allocations Out — all can carry the prefix. Do NOT flag the prefix at any pre-Priced stage.
- **At Allocations Out — always `Final books over` or `Books closed over`, never plain `Books over`.** Books are implicitly final at Allocations even if source doesn't say "final" or "closed" outright. Default = `Final books over [amount]` (with JLM breakdown if source discloses one); flip to `Books closed over [amount]` if source explicitly says "closed" (or "closed at reoffer" / equivalent). Plain `Books over` at Allocations is wrong — flag it.
- **At all other pre-Allocations stages** (IPTs / Guidance / Book Update / Spread Set / Final Terms / Launched): plain `Books over` is fine when source just says `Books >`; upgrade to `Final books over` / `Books closed over` only when the source uses those words. The content after the prefix should reflect what the source said (e.g. `Book update: IOIs over $9bn (incl. $350m JLM).` at Guidance).
- **At Priced, Allocations Out, or any late-stage post-Final-Terms update where the source itself explicitly says "final" or "closed":** no `Book update:` / `Books update:` prefix. **The wording is driven by what the source term sheet AT THIS STAGE says, not by anything disclosed in an earlier update, AND not by whether the deal has technically hit "Priced" yet.** If the source Slack for a Final Terms / Allocations Out / Priced update explicitly says "Final books" or "Books closed" — apply the same wording rules as at Priced. Most Priced term sheets are silent on books (the book figure was last given at Final Terms / Spread Set) — in that case the default is `Books last heard over [amount].`, even if a JLM breakdown was disclosed at the earlier stage. Order of precedence:
  1. **Priced-stage source says "books closed" / "global books closed" / "orderbook closed" → `Books closed over [amount] (incl. [Y] JLM interest).`** Beats `Final books over` even when a JLM breakdown is also present.
  2. **Deal's timeline includes a source stating "final books" OR "books closed" AND a JLM interest breakdown was disclosed somewhere along the way (Launched, Allocations, or any earlier stage) → `Final books over [amount] (incl. [Y] JLM interest).`** The JLM figure must appear in the outgoing BR body. It does NOT need to be disclosed by the source AT the Priced update specifically — an earlier "closed" / "final books" language + JLM breakdown together are enough. Only fall back to `Books last heard over` when the deal NEVER received closed/final language at ANY stage (like DBJ).
  3. **Priced-stage source silent on books / JLM breakdown** — the body treatment depends on the deal's *history*:
     - **A. Deal received `Final books` / `Books closed` at any earlier stage** (typically Allocations Out): body book line is OPTIONAL; the priced-deal form's `finalBooks` carries the figure and body can be silent.
     - **B. Deal had book updates but NEVER received `Final books` / `Books closed`**: body MUST carry `Books last heard over [amount].` (last recorded figure), AND priced-deal `additionalInfo` should carry the same `Books last heard over [amount].` — populate both. Example: Chiba Bank Priced (id 14620638) — books progressed `>USD2bn → >USD2.5bn → >USD3.1bn` but no source ever said "final" or "closed", so body should end `… ISIN [X]. Books last heard over USD3.1bn.` and `additionalInfo: 'Books last heard over USD3.1bn.'`.
     - **C. Deal never had any book figure**: body and `additionalInfo` can both be silent.
     The distinguishing question during QA: did the deal *ever* receive a Final Books or Books Closed figure? If yes → optional; if no but there were updates → `Books last heard over` required in body AND `additionalInfo`.
- `Books above` and `Books over` are equivalent — either is acceptable.
- **`over` (or `above`) must be spelled out — a trailing `+` on the amount is NOT a substitute.** Correct: `Final books over EUR900m (incl. EUR50m JLM).`. Wrong: `Final books EUR900m+ (incl EUR50m JLM).`. This applies to every variant (`Books over`, `Final books over`, `Books closed over`, `Books last heard over`) — never write `EUR900m+`.`
- [ ] Timing

## Final books — required items

- [ ] `Book update: Final books` OR `Books closed over [amount]`
- [ ] Hedge deadline (if applicable — flag only if the equivalent term-sheet Slack message mentions a hedge deadline)
- [ ] Timing
- Note: typically appended to the allocation message rather than standalone.

## Final terms — required items

- [ ] Opening line: `"[Spread or yield] set at [level] for [Issuer] [size] [tenor] ..."`
- [ ] Full deal-terms block: Settle, Issuer, Guarantors, Type, Reg S/144A, COC, CUC, MWC, par call, List, denoms, Law, UoP, Ratings, Bookrunners, ISIN, Timing
- [ ] Book update line: books level, close time

## Launched — required items

Same as Final Terms, plus the size is now confirmed (no `bmk`/benchmark placeholders).

- [ ] Opening line: `"Launched: Size set at [size] and [spread/yield] is set at [level] for [Issuer] ..."`
- [ ] Full deal-terms block (as Final terms)
- [ ] Book update line: books level, then `"Book subject, allocations and pricing to follow…"`

## Priced — required items

- [ ] Opening line: `"Priced: [Size], coupon [coupon], [maturity]. Reoffer [price], spread [spread]. Yield [yield]."`
- **Benchmark date format**: month + full year spelled out inside the spread field, e.g. `spread MS+16bp / DBR 2.60% 15 August 2033+24.8bp` — never `MM/YY` shorthand like `08/33` or `04/29`. Preserve the day when the source gives it (`15 August 2033`); omit only when source omits.
- [ ] Settle, Issuer, Guarantors, Type, Reg S/144A, COC, CUC, MWC, par call, List, denoms, Law, UoP, Ratings, Bookrunners, ISIN
- [ ] Final books line — unless source explicitly says "final books only" with no JLM-interest breakdown, in which case omission is intentional.

## Priced tap / add-on — required items

- [ ] Opening line: `"Price increased: [size] takes outstanding to [new nominal], coupon [coupon], [maturity]. Reoffer, spread. Yield."`
- [ ] Full deal-terms block (as Priced)
- [ ] `New outstanding = existing outstanding + new tap size` — sanity-check the arithmetic if the previous nominal is discoverable via the same borrower + maturity in `bondradar_api.py list`.

## Headline QA (always check, every tick)

The headline is a first-class QA target — not an afterthought. On every finding, walk each element of the headline against the source term sheet AND the BR body:

0. **`** ` prefix (required)** — every BR headline must open with exactly `** ` (double asterisk + trailing space). No priority tiers. Flag any deviation: missing prefix, single `*`, or `***`.
1. **Issuer / ticker shorthand** — abbreviation must match the borrower record (e.g. `CA Home Loan SFH` vs `Credit Agricole HL SFH`); flag inconsistent abbreviations across tranches or updates.
2. **Currency + size** — must match the tranche form and the body (`EUR500m`, `USD1bn`, `CHF100m+` for min-size, `HKD bmk` if still unset).
3. **Tenor / structure** — must match tranche `structure` and body maturity (`5-year`, `L-4y`, `8NC3`, `PerpNC5`, `11.5NC10`, `WNG` where source says WNG).
4. **Format flags in the title** — every applicable descriptor must appear in the headline shorthand: `Grn` (green), `Soc` (social), `Sus` (sustainability), `SLB`, `EuGB`, `CB` / `MC` (covered), `T2`, `AT1`, `RT1`, `Sub`, `Sr Pref`, `SNP`, `HoldCo` / `OpCo`, `Sukuk`, `Kangaroo`, `Samurai`, `144A/RegS`, `SEC`, `RegS`.
5. **Stage word** — must match the body's opening line (see table below). This is the most-flagged headline error.
6. **Level** — the level printed after the stage word must equal the level in the body's opening line and the latest `tranche.details.priceEvolution` (`IPTs SARON+45bp area` ↔ body `IPTs are SARON+45bp area` ↔ tranche `SARON+45a`).
7. **Multi-tranche marker** — 2 tranches → `dual-tranche`; 3+ → `multi-tranche` (see below).
8. **Tap / increase marker** — if the deal is a tap, headline must include `tap` or `add-on`; if an increase, `Increase Priced` in the body must be reflected in the title.

If any element is wrong or missing, flag the specific element and quote a corrected headline. Never mark a finding clean without having walked all eight items.

### Stage word ↔ body opener

The stage word at the end of the headline must match the stage in the body's opening line. Common pairs:

- Body opens `Launched: Size set at …` → headline ends `… : Launched at [level]` (NOT `Final Terms`).
- Body opens `Spread set at …` → the headline word depends on whether size is set:
  - **Spread set, size NOT yet set** (body reads `Spread set at MS+X for [Issuer]'s USD benchmark …` — still `bmk` or unset size) → headline ends `Spread set MS+X` or similar.
  - **BOTH spread and size set** (body reads `Spread set at MS+X and size set at USDXbn` or `Spread set at MS+X for [Issuer]'s USDXbn …`) → headline ends `Final terms` (lowercase `t` — house-style casing, do NOT capitalise `Terms`), NOT `Spread set`. Once size is confirmed, the stage has advanced past pure Spread Set into Final Terms. Correct headline form: `[Issuer] USDXbn N-year at MS+X: Final terms`.
  - Example correction (Macquarie GBP500m L-4y): headline `Macquarie Group GBP500m long 4y: Spread set at G+85bp` — body opened `Spread set at UKT+85 and size set at GBP500m`, so headline should have been `Macquarie Group GBP500m long 4y at G+85bp: Final terms`.
- Body opens `Priced: …` (final coupon/reoffer/yield known) → headline ends `Priced at [level]`. `Allocations` is NOT a valid substitute — if body opens `Priced:`, headline must say `Priced at [level]` even when BR's workflow state has advanced to Allocations.
- Body opens `Guidance is …` (first-time guidance) → headline ends `Guidance [level]` or `Guidance is`.
- Body opens `Guidance remains …` or `IPTs remain …` (book update reiterating level) → headline ends `Book update` (or `Book Update`).

If the headline says one stage but the body opens with another, flag the mismatch and suggest a headline that matches the body opener.

## Timing statement position

The timing statement (`Books open, today's business.`, `As early as today's business.`, `Allocation and pricing shortly.`, etc.) always sits at the end of the LATEST live line — never appended to a carried-forward earlier paragraph.

- **IPTs / Guidance / Spread set (no book line yet)** — timing at end of main paragraph.
- **Book update (has a `Book update:` line)** — timing at end of the `Book update:` line, e.g.
  ```
  Guidance remains MS+27bp area for [...]. ISIN XYZ.
  Book update: Books over 2bn (Incl. 280m JLMs). Books open, today's business.
  ```
- **Allocations Out** — timing at end of Allocations line.
- **Final Terms / Launched** — usually `Allocation and pricing shortly.` at end of update line.
- **Priced** — no forward-looking timing.

If the body has a book-line but the timing is still attached to the guidance/IPT paragraph, flag it and quote the corrected ordering.

## Multi-tranche vs dual-tranche (naming)

- **2 tranches → `dual-tranche`** in the headline and body descriptors. Never call a 2-tranche deal `multi-tranche`.
- **3 or more tranches → `multi-tranche`**.
- If BR labels a 2-tranche deal as `multi-tranche`, flag it and suggest `dual-tranche`.

## Multi-tranche — required items

Each tranche is written separately:

- [ ] `"Tranche A: [size] [tenor] [note], [maturity]. IPTs are / Guidance is / Spread set at [level]. Type. MWC, par call. Ratings. Bookrunners. ISIN."` — repeat for B, C, D…
- [ ] One dense paragraph beginning **exactly** with the literal string `"Common terms:"`
- [ ] Under `Common terms:` include ONLY items genuinely shared across tranches: Settle, Issuer, Guarantors, Type (if shared), Reg S/144A, COC, CUC, MWC, par call, List, denoms, Law, UoP, Ratings, Bookrunners
- [ ] Tranche-specific items MUST stay in each tranche's line (do NOT roll them into Common terms)

## Per-tranche form data (the admin panel behind the message)

Every deal in the BR API carries a `tranches[]` array — the structured per-tranche form the desk fills in the admin UI. Even single-tranche deals have one `tranches[0]` entry. QA these fields against the source term sheet AS WELL AS the outgoing message body (they should be internally consistent). Fields live under `tranches[i].details[-1]` (the last entry in the details array is the current version; earlier entries are the edit history) and under `tranches[i].banks`.

For each tranche in `tranches[]`, check:

- **`name`** — `A` / `B` / `C` / etc. For a single-tranche deal there is only `A`. Tranche count in the API must match the source term sheet's tranche count and the outgoing message body's tranche count.
- **`currency`** — must match source currency for that tranche. e.g. source `GBP Benchmark` → `currency: GBP`. On multi-tranche deals with different currencies per tranche (e.g. USD + CNH), each tranche row must carry its own currency.
- **`volume`** — the size code. `bmk` for `[CCY] Benchmark`, else the numeric size (e.g. `500`, `1000`, `100+` for a minimum). Must match the source's per-tranche size.
- **`structure`** — the tenor + product code. Examples: `3y CB` (3-year covered bond), `10y` (plain 10-year), `PNC5 AT1`, `4NC3 SNP`, `30NC5.75 Hybrid`, `Perp NC5`. Must match source tenor for that tranche. **The field is capped at 9 characters** — long tenor descriptors like `11.5NC10.5` (10 chars) get truncated to `11.5NC10` (or `11.5NC10.`) because the `.5` doesn't fit. This is by design; the outgoing message body still renders the full descriptor. Cross-check against the body before flagging an apparent typo — if body has `11.5NC10.5 fixed-to-FRN` and form has `11.5NC10`, that's the field-length truncation, not a bug. Only flag when the form value disagrees with the body in a way length can't explain (e.g. `4NC5` vs body `4NC3` — different digit).
- **`priceEvolution`** — the current level in Bond Radar shorthand. Examples: `SONIA+53a` (SONIA+53bps area), `T+108`, `MS+37`, `6.60% (the number)`, `TBA` (level not yet set). Must match the current-stage source level, in BR shorthand format (`a` for `area`, `+Nbp` written without `bps`, `the number` spelled out for final/level-set stages). If the source has moved to a tighter level but the tranche row still shows the earlier level, flag it.
- **`bookOrRating`** — a dual-purpose field whose meaning depends on **which market pipeline the deal is in**, not the stage. Check `hgDetails` vs `emDetails` to decide:
  - **IG / HG deals (`hgDetails` populated)**: field is labelled **"Books"** in the admin UI. Value depends on bookrunner count:
    - **> 3 bookrunners → `JT-LEADS`** (standard shorthand — books collectively with joint leads, no per-bank IOI itemising).
    - **≤ 3 bookrunners → EITHER a bank-ticker summary slash-separated (e.g. `WF/BOA` for 2-book, `BOFA/TD/WFC` for 3-book), OR the expected issue ratings triple (e.g. `A2/A-/A`).** Both are valid — the desk picks based on habit. Don't flag either form.
    - Do NOT flag `JT-LEADS` OR bank-ticker summaries OR ratings triples on IG deals — all three are legitimate values for the field, regardless of stage.
  - **EM deals (`emDetails` populated)**: field is labelled **"Ratings"** in the admin UI. Value is the expected issue ratings in slash-separated `Moody's/S&P/Fitch` order (empty slot allowed with double slash, e.g. `Aaa//AAA` when there's no S&P; `A1/A-/A` when all three; `Aaa//` when only Moody's). Must match the source's expected issue ratings for that tranche; the ordering must be M/S/F (never F/M/S or any other order).
  - Flag `bookOrRating` only on **EM** deals if it looks wrong (missing agency the source has, wrong order, empty when source gave ratings). Never flag `JT-LEADS` on an IG deal.
- **`timing`** — free-text stage/timing marker. Common values: `today` / `this week` / `next week` / `tomorrow's business` / `T+7 window` (pre-launch); `launched` / `priced` (post-launch stage tags). Must match what the source says about timing for that tranche AND the deal's actual stage — e.g. if the outgoing message body says `Launched:` but `timing` still says `today`, flag it as stale.
- **`banks.active[]`** — array of bank IDs that acted as JLMs on this tranche. The count must equal the count of banks in the source's JLM list for that tranche (subtract any Passive JLMs — those go in `banks.passive[]`). We can't resolve IDs to names via the API, so compare *by count* here and rely on the outgoing message body's rendered bookrunner list to check names.
- **`banks.passive[]`** — Passive bookrunners only. Usually empty. If the source explicitly names Passive JLMs and BR's Passive list is empty (or vice versa), flag.
- **`figi`** — **must be populated from the deal's very first stage** (whichever of Mandate / IPTs / Guidance comes first for that deal) **onward, not just once priced** — flag a hard miss (`BBG024FVQ7C7` etc. expected), not a soft "should be." Keep flagging it at every later pre-priced stage (Book Update / Final Terms / Launched / Allocations Out) as long as it's still null — this isn't a one-time check, it re-fires every run until fixed. Once `type: PRICED`, this tranche-level check stops (the priced-deal-record `figi` rule below takes over). When flagging a missing tranche-level `figi`, tag both `<@U09GENPJNQ5>` (Bloomberg - IG Europe) and `<@U09GGGDB286>` (Bloomberg - EM) on their own mention line at the top of the post, same convention as the reactor mention, so the Bloomberg feed accounts can action it directly. This is mechanically enforced in `pre_check.py` (`check_deal()`'s tranche-FIGI loop, gated on `stage != "priced"`) — this note exists so the AI pass follows the same behavior as a backstop for anything `pre_check.py` doesn't catch.
- **`shouldBePriced`** / **`shouldBeIncreased`** — workflow flags. `shouldBePriced: true` means the tranche is queued for pricing; `shouldBeIncreased: true` means it's a tap in progress. These should reflect the stage: if the outgoing message says `Priced` but `shouldBePriced` is false (or vice-versa), the workflow state has drifted from what the desk published.
- **`increased`** — set once a tap has been executed. Should be `true` only for actual tap increases, otherwise `false`.

For each tranche row, also cross-check against the outgoing message body:

- The `currency` + `volume` + `structure` + `priceEvolution` + `bookOrRating` in the form MUST match what the corresponding `Tranche A:` / `Tranche B:` line in the body actually says. Any drift between the form and the body is a real flag — the outgoing message is generated from the form, so they should never disagree.
- The count of JLMs in the body's bookrunner list for that tranche must equal `len(banks.active) + len(banks.passive)`.

### Region + activation flags (deal-level, not per-tranche)

These sit on the deal object itself, not inside `tranches[]`. When they're wrong they change who sees the message:

- **`activeWeb`** / **`activeBloomberg`** — must both be `true` for a live deal. If a deal is live in the outgoing feed but one of these is false, flag it: the deal is only publishing to half the audience.
- **`hgDetails.regionAmericas`** — this is the **Americas region flag**, driven by deal currency, not issuer domicile:
  - **USD-denominated deals → must be `true`**. Any tranche in USD (single-currency USD deals, USD+other multi-currency deals, USD taps) needs Americas ticked so the deal shows in the US pipeline.
  - **Non-USD deals → must be `false`**. EUR/GBP/AUD/CHF/CNH etc. deals must have Americas unticked, even if the issuer is a US company (e.g. Alphabet's AUD Kangaroo — issuer is US but currency is AUD, so `regionAmericas: false`).
  - Multi-currency deals with any USD tranche → still `true`. Check every tranche's `currency` in `tranches[i].details[-1].currency`.
  - This is the single most common flag on the deal — always check.
- **`emDetails.regionAsia`** / **`emDetails.regionCeemea`** / **`emDetails.regionLatam`** — for EM deals, must match the issuer's region (Singapore/HK/Japan → Asia; Slovakia/Poland/Estonia → CEEMEA; Brazil/Mexico/Chile → Latam). If the region flag is wrong the deal filters out of the right EM pipeline.
- **`hgDetails.highYield`** — true only for HY deals. IG deals must have it false.
- **`hgDetails.coveredBonds`** — the **Sector: COVERED BONDS** checkbox. Must be `true` whenever the deal is a covered bond. Signals:
  - Body / headline mentions `covered bond` / `CB` / `Covered Bond Programme` / `Obligations de Financement de l'Habitat` / `Pfandbriefe` / `Cédulas` / `SDO` / `EuGB Covered` / `Mortgage Covered Bond`.
  - Tranche `structure` field ends in `CB` (e.g. `3y CB`, `5y CB`).
  - If any of the above is present and `coveredBonds: false`, flag it. If the deal is NOT a covered bond and `coveredBonds: true`, flag that too.
- **`hgDetails.hyExpectedPageId`** — the HY-specific Expected Bloomberg page (e.g. `HYRE3`). Must be populated whenever `hgDetails.highYield: true` and the deal is pre-Priced (`type != PRICED`) — covers both HY-only and HY dual-feed deals. Not applicable (don't flag) when `highYield` is not `true`. Also mechanically checked by `pre_check.py`.
- **`expectedPageId`** — the **Expected Bloomberg page** dropdown, for the generic IG/HG pipeline. Must be populated (non-null, non-empty) for any **pre-Priced** live deal that actually feeds that pipeline. e.g. `IGRB17`, `IGRB42`, `EMRH40`, `EMRH37`. **Once a deal moves to `type: PRICED`, `expectedPageId` gets cleared automatically — do NOT flag `null` on a PRICED deal, that's the normal post-pricing state.** A pure-HY deal (`hgDetails.highYield: true` and `hgDetails.feedIgrd` not true) does NOT feed this pipeline and must NOT be flagged for a null/empty `expectedPageId` — it only needs `hyExpectedPageId` (see below). Only flag `expectedPageId` when `activeBloomberg: true` AND `type != PRICED` AND `expectedPageId` is null/empty AND the deal feeds the IG/HG pipeline (i.e. `hgDetails.highYield` is not `true`, OR it's `true` together with `hgDetails.feedIgrd: true` for a HY dual-feed deal, which needs both page fields populated).
- **`expectedPageCount`** — the **Bloomberg total number of pages** field. **Pre-Priced only** — check this only when `type != PRICED`. Once the deal moves to `type: PRICED`, do NOT flag `expectedPageCount` (it's a pre-pricing routing field). Rules (pre-Priced):
  - Single-tranche deal → `expectedPageCount: 1`.
  - Dual-tranche deal → `expectedPageCount: 2`.
  - Multi-tranche deal → `expectedPageCount: N` where N = `len(tranches)`.
  - Alphabet (6 tranches) needs `expectedPageCount: 6`. If it's still `1`, flag it — BBG won't reserve enough pages.
- **`notifyMobile`** — usually true. Flag if false without an obvious reason (mobile-notify off suppresses the push to the app).

## Priced-deal form (per-tranche pricing record)

Once a tranche is priced, a **priced-deal record** is created and linked to the tranche via `tranches[i].pricedDealId`. The admin URL is `bondradar.com/admin/#/{cat}/priced-deals/{id}`; the API endpoint is `/priced-deals/{cat}/{id}` (cat=`hg`|`em`) — use `bondradar_api.py priced <cat> <id>` on the CLI or `br.get_priced_deal(cat, id)` from Python. **Do NOT trust the `pricedDeals[]` summary on the parent news JSON** — its `cpn` field is unreliable (sometimes carries the spread, not the coupon; e.g. it reported `cpn: "BBSW+180"` for Alphabet's 20yr Fixed where the true `cpn` on the full record is `"6.90"`). Always fetch the full priced-deal form via `/priced-deals/{cat}/{id}` for QA.

The full priced-deal record has these fields (all should be populated post-pricing unless noted). QA each against the source term sheet AND the outgoing `message` body AND the parent deal's tranche form. **This means checking the actual VALUE is correct, not just that the field is non-null** - a populated-but-wrong value (e.g. `fpr: 100` when the source said `99.858`, or a `isin`/`figi` that doesn't match the source's) is exactly as much a defect as a missing one, and is easy to miss if you only scan for nulls. On a multi-tranche deal, QA every tranche's own priced-deal record against that SAME tranche's source line independently - finding one tranche's issue (e.g. a ratings mismatch on Tranche A) does not mean the other tranches are clean; keep checking all of them.

### Identity + basics

- **`pricingDate`** (`"2026-08-19"`) — ISO date. Must be populated and match source pricing date.
- **`pricingTime`** (`"10:47:00"`) — HH:MM:SS.
- **`borrowerName`** / **`borrowerId`** — must match parent deal's borrower.
- **`currency`** — must match parent tranche's `currency` AND source per-tranche currency.
- **`nominal`** — size in millions of currency. Must match source per-tranche size AND parent tranche's `volume`.
- **`retained`** / **`retainedTotal`** — usually `null` / `0`. Populated only when a portion is retained.
- **`nominalTotal`** — `nominal` + `retained` (sanity: should equal `nominal` when retained is 0).
- **`increaseNominal`** / **`increaseExchange`** / **`increaseRetained`** / **`nominalSecond`** — populated ONLY when this priced record is a tap (`increase: true`); otherwise all null.
- **`increase`** / **`lastIncrease`** — `increase: true` on taps. Must be consistent with the tap flag on the parent tranche (`shouldBeIncreased`).

### Coupon + call terms

- **`cpn`** — coupon string. Format depends on coupon type:
  - **Fixed** → decimal percentage, e.g. `"5.20"` / `"6.90"` / `"1.3775"`. Never a spread.
  - **Floating (FRN)** → base+spread, e.g. `"BBSW+65"` / `"SOFR+40"` / `"SONIA+53"`. Never a fixed percentage.
  - Cross-check `cpn` against the source's coupon column AND the parent tranche's `structure` (fixed vs FRN). If shape doesn't match structure, flag.
- **`perpetual`** (`false` / `true`) — must be true only for perp structures (`PNC5 AT1`, `PerpNC5`, etc.).
- **`nonBullet`** (`"N"` / `"Y"`) — `Y` only for non-bullet structures (amortising, sinking-fund).
- **`firstCallDate`** — ISO date; populated for callable structures.

### Pricing outputs

- **`fpr`** — Final Priced Reoffer as a number, e.g. `99.144` / `100.0`. `100.0` for par-priced FRNs and FRN-format deals; must match the outgoing body's `Reoffer` value **AND the source term sheet's reoffer price for that specific tranche** - a value that's merely non-null/populated is not enough, it must be numerically correct. On a multi-tranche deal, check every tranche's `fpr` against that SAME tranche's source line independently - don't assume later tranches are right just because the first one checked out.
- **`spread`** — reoffer spread string, e.g. `"ASW+180"` / `"T+22.1"` / `"SARON+85"` / `"SOFR+40"`. Must match the outgoing body's `spread` AND the source's benchmark spread for that tranche - check correctness, not just presence.
- **`yield`** — yield string with `%`, e.g. `"6.980%"`. FRNs may leave this blank or populated with the reference rate. When populated, must match the source's yield/YTM for that tranche.
- **`oldSpread`** — previous spread value (from Guidance stage); typically populated automatically.
- **`fxRate`** — FX rate at pricing (required; e.g. `0.70738` for AUD/USD). Must be populated for non-USD deals.
- **`hgDetails.hgNip`** / **`emDetails.emPremiumNip`** — new issue premium (bps); optional.

### Ratings

- **`moodysRating`** / **`snpRating`** / **`fitchRating`** — coded strings like `"AA3"` / `"AA_PLUS"` / `"NR"`. `"NR"` for missing agencies; if the source omits an agency, expect `NR` (or `null`). Must match source expected issue ratings for this tranche.

### Identifiers

- **`isin`** — must match source per-tranche ISIN AND the outgoing body's ISIN for this tranche.
- **`figi`** — BBG FIGI (e.g. `"BBG024F8HZF3"`); must match `tranches[i].figi` on the parent tranche. If null, tag `<@U09GENPJNQ5>` (Bloomberg - IG Europe) and `<@U09GGGDB286>` (Bloomberg - EM) on the flag per the tranche-level `figi` rule above.
- **`bloombergCode`** — BBG ticker code (e.g. `"DO6481950"`).
- **`bloombergNsnCode`** — optional.

### Format flags (booleans — exactly one Format flag should be `true` per Reg-S/144A structure)

- **`dealRegsOnly`** — `true` for RegS-only deals. Mutually exclusive with the others below.
- **`deal144aOnly`** — `true` for 144A-only deals.
- **`deal144aRegs`** — `true` for 144A/RegS deals (most common for USD).
- **`secRegistered`** — `true` for SEC-registered deals.
- **`hgDetails.hg3a2`** — `true` for 3a2 (SSA carve-out).
- **`hgDetails.hgSecExempt`** — `true` for SEC-exempt (e.g. SSA global-only).

Rule: exactly one of these should be `true`. Cross-check against source's Format section: e.g. source `Reg S (Category 2), Bearer` → `dealRegsOnly: true`. If none is true, flag — the deal won't route to the right SEC filter.

### Additional-info flags (booleans matching the "Additional Information" checkbox column)

- **`covered`** — for Covered bond structures. Must match deal-level `hgDetails.coveredBonds` and source structure keywords.
- **`ggb`** — GGB (Government-guaranteed bond).
- **`green`** — Green bond.
- **`sustainable`** — Sustainability bond.
- **`sustainabilityLinked`** — Sustainability-Linked bond (SLB).
- **`social`** — Social bond.
- **`seniorPreferred`** / **`seniorNonPreferred`** — bank capital ranking. Exactly one is true for a bank Sr Pref / SNP; both false for plain corporate senior or for AT1/T2/Sub.
- **`holdCo`** / **`opCo`** — **bank OpCo/HoldCo capital-structure flag.** Neither is a general "operating company" / "holding company" label — both are only ticked when the issuer is actually using the OpCo/HoldCo debt structure. Rules:
  - **Which issuers use OpCo/HoldCo:** UK banks (HSBC, NatWest, Barclays, StanChart, Lloyds, Nationwide, …), Swiss banks (UBS, Credit Suisse), US banks (JPM, BofA, Citi, WFC, GS, MS), **Japanese *megabanks only* (MUFG, SMBC, Mizuho)** — regional Japanese banks (Chiba, Shizuoka, etc.) sell senior directly and neither flag ticks — plus ING (Dutch). Occasional non-bank exceptions: Softbank; sometimes bank-adjacent finance vehicles like Credit Agricole Auto Bank.
  - **How to tell HoldCo from OpCo:** OpCo shares the parent's ratings (higher); HoldCo is one notch or more lower rated. Structurally, HoldCo notes typically carry a **1-year call prior to maturity** (e.g. `5NC4`, `9NC8`, `11NC10`) — this is a strong signal. OpCo notes are bullet or have no call. HoldCo issuance is done to maintain NSFR eligibility.
  - **When neither is ticked:** most Continental European banks (French, German, Italian, Spanish) sell **senior preferred** or **senior non-preferred** instead — neither `holdCo` nor `opCo` gets ticked. Smaller banks selling plain senior or subordinated debt — neither gets ticked. Non-bank corporates — neither gets ticked, even if the issuer is technically an operating subsidiary or a parent holding company.
  - **Concrete example (NatWest Sep-2026):** `Tranche A: NatWest Markets Plc, 5-year bullet MS+70, A1/A/AA-` → `opCo: true`. `Tranche B: NatWest Group Plc, 9NC8 MS+110, A3/BBB+/A+` → `holdCo: true` (different entity, one-year call, lower ratings).
  - **Common false-positive to avoid:** an Australian bank T2 (like CBA), a Canadian bank senior, a corporate deal from an operating subsidiary — none of these should have `opCo: true` even if the issuer is an operating entity. Both flags stay `false`.
  - **How to apply during QA:** If the issuer isn't in the list of OpCo/HoldCo issuers, both flags must be `false`. If it is: check the ratings vs parent (OpCo higher, HoldCo lower) and the call structure (HoldCo typically 1-year-call-to-maturity) to determine which is set. Flag either (a) a non-OpCo/HoldCo issuer with either flag ticked, or (b) an OpCo/HoldCo issuer with the wrong one ticked (e.g. HoldCo entity marked `opCo`).
- **`coc`** / **`mwc`** / **`cuc`** — Change of Control put / Make-Whole call / Change of Use call. Set when the deal has that feature (source term sheet mentions them). Cross-check against the outgoing body's `MWC, 1-month par call` / `COC 101` / `CUC 75` phrasing.
- **`subordinated`** — `true` for any subordinated structure (T2, AT1, hybrid).
- **`perpetual`** — already listed above; also acts as a hybrid/AT1 indicator.
- **`hgDetails.hgPref`** — the "Prefered US" checkbox from the admin.

Rule: booleans must match source labels. Common misses: `green` unchecked on a labelled Green bond; `covered` unchecked on a covered bond; `mwc` unchecked when body has `MWC`; `seniorNonPreferred` unchecked on a SNP tranche.

### Tier (for bank capital only)

- **`tier`** — `"AT1"` / `"RT1"` / `"T1"` / `"T2"` / `null`. Must be non-null for bank Additional Tier 1, Restricted Tier 1, Tier 1, or Tier 2 tranches. For plain senior corporate / SSA / covered / AT1-free deals, `null` (= "No Tier" radio in admin).

Rule: if the source labels the tranche `AT1` / `T2` / `SubNC5` etc., `tier` must be set to the matching code.

### Banks

- **`dealBanks.active[]`** — array of bank IDs on this priced deal (bookrunners on the tranche). Count must match the source's per-tranche JLM count.
- **`dealBanks.passive[]`** — passive JLMs. Usually empty.
- **`leagueTable`** — league-table eligibility flag. **Almost always `true`** — most deals qualify. Set `false` only when the deal fails one of the LT rules below.

### League-table eligibility rules

**HG (High Grade) league-table rules — updated Jan 2024:**

1. All HG tables (except SSA, which has its own table) cover borrowers from Japan, Australia, New Zealand, Western Europe, North America — the "HG regions".
2. Publicity: coupon, size, currency, maturity, issue price, and lead managers must ALL be disclosed.
3. International bond market with relevant international documentation (RegS, SEC Global, etc.). Domestic-only issuance is ineligible.
4. **Minimum maturity 18 months.** Hard Calls or Puts before 18 months exclude the deal (Make-Whole Calls do NOT — MWC is fine).
5. **Minimum size USD100m equivalent** for the original deal. Taps/increases are included only if the original deal was ≥ USD100m equivalent.
6. Taps/increases are included when the original tranche was LT-eligible.
7. Bookrunners get equal accreditation regardless of actual economics. Passive bookrunners are accredited alongside active bookrunners equally.
8. Multi-tranche: each tranche is a separate LT transaction.
9. FX taken on day of issue; volumes expressed in USD equivalent (except currency-specific tables).
10. Full nominal amount is given LT credit regardless of retained portion.
11. Bond Radar may still cover non-LT-eligible transactions in the database (manageable via the admin data wizard).
12. Lead managers per final term sheet. Parent-bank accreditation OK if parent owns >50% of a named lead.

**EM (Emerging Markets) league-table rules — updated Jan 2024:**

1. Tables auto-update on pricing.
2. Accreditation only for new-cash aspects. Straight exchanges (bond-for-bond) not accredited; any surplus from an exchange IS.
3. International bond market with international documentation. Domestic-only ineligible.
4. Equal accreditation to all bookrunners (active + passive).
5. Volumes calculated from re-offer price. Same-price increases stack; different-price increases are separate deals (unless part of a greenshoe).
6. Multi-tranche: each tranche separate.
7. FX on day of issue; USD-equivalent unless currency-specific table.
8. Cross-default rules for subsidiaries whose parents are outside/inside the region — check case by case.
9. Deals backed/guaranteed by sovereign states, supranationals, or parent companies are included.
10. **ABS, CDO, and other securitisations NOT included — except covered bonds from EM regions.**
11. Regional supranationals only when the majority of member states/sponsors are in a specific region.
12. For "agency" status: must be 100% owned and guaranteed by its home State.
13. Deals must be sent to BR within 10 working days of pricing; coupon/size/currency/maturity/reoffer/leads must be disclosed.
14. Sub-IG league table: requires at least one senior unsub rating below IG at launch (or, for non-rated, the sovereign of origin has ≥1 sub-IG rating).
15. Non-Sovereign LT includes corporates, banks, municipal borrowers (regions/cities) from non-Japan Asia, CEEMEA, Latam.
16. **Minimum maturity 365 days.** Hard Calls or Puts before 365 days exclude the deal (MWCs OK).
17. Sovereign regions covered — Latam: Central + Southern Latin America + Caribbean (excl. Puerto Rico); CEEMEA: Central + Eastern Europe, Middle East, Africa, Central Asian republics (incl. semi-autonomous regions); Asia: All Asia, India, Pakistan, Oceania (except Australia, NZ, Japan).
18. BR may still cover non-eligible transactions; users manage via data wizard.
19. Lead-manager parent-bank rule same as HG.

### When to set `leagueTable: false`

- HG deal with `maturity < 18 months`, or a hard call/put before 18 months (MWCs don't count).
- HG deal with size (or original size for a tap) `< USD100m equivalent`.
- EM deal with `maturity < 365 days`, or a hard call/put before 365 days (MWCs don't count).
- ABS / CDO / other securitisation (except EM covered bonds).
- Domestic-only deal (no international docs).
- Deal from outside the region coverage (e.g. a Puerto Rico issue for Latam, or an Australian issue in the EM Asia table).
- Missing required disclosures (coupon/size/currency/maturity/reoffer/leads).
- Straight exchange with no new cash (EM only).

If none of the above apply → `leagueTable: true`.

### How to apply during QA

For every priced deal:
1. Check the region (HG or EM) based on `hgDetails` vs `emDetails`.
2. Check the maturity against the region's threshold.
3. Check the size and structure (`ABS`, `CDO`, `Securitisation`, `covered bond`).
4. Check for hard calls/puts before threshold (look at `firstCallDate`, `structure` like `5NC4` etc.).
5. If all rules pass → `leagueTable` should be `true`. Flag if `false`.
6. If any rule fails → `leagueTable` should be `false`. Flag if `true`.

### Books

- **`finalBooks`** — final orderbook in millions of currency (e.g. `4290.0` for A$4.29bn). Must match the source's per-tranche final orderbook figure.
- **`finalAccounts`** — number of investor accounts (optional; often null on smaller deals).
- **`statsCategories[]`** — book stats breakdown (by geography, investor type). Optional.

### Text + attachments + metadata

- **`message`** — full outgoing priced message text. Must match the outgoing body on the parent news deal for this tranche.
- **`headlineComment`** — optional headline addendum.
- **`stats`** — optional free-text book stats.
- **`additionalInfo`** — free-text field for distinguishing product features that don't fit any dedicated flag. It IS meaningful — populate it whenever any of the below apply, and flag if a deal has one of these attributes and `additionalInfo` is empty:
  - **Par call detail** — if the deal has an atypical par-call window, note it. e.g. `"3-month par call"`, `"6-month par call"`. (Standard 1-month par call is common enough it's often left off.)
  - **`EuGB`** — European Green Bond (per the EU Green Bond Regulation). Set alongside `green: true`.
  - **`MC`** — Mortgage Covered bond. Set alongside `covered: true` on any covered bond backed by mortgage collateral (residential or commercial).
  - **`PC`** — Public Covered bond. Set alongside `covered: true` on any covered bond backed by public-sector collateral (sovereign/agency/local-government loans, Öffentliche Pfandbriefe, etc.).
  - **`BC`** — Blockchain / digital bond (any deal issued on-chain or via distributed-ledger tech).
  - **HY UOP shorthand** — for HY deals, spell out the use of proceeds in shorthand: `"UOP: GCP"` (general corporate purposes) / `"UOP: Aqui"` (acquisition) / `"UOP: Recap"` (recapitalisation) / etc. Multiple can be combined with `;`.
  - **`Sukuk`** — EM deals that are Sukuk (Islamic-finance structured bonds).
  - **Sale of retained bond** — when the deal is a sale of previously-retained inventory (NOT a fresh tap increasing the outstanding). Note it here so it's clear this isn't a tap. e.g. `"sale of retained bond"`.
  - **`ESN`** — European Secured Note.
  - **`Books last heard over [amount]`** — when the desk had book updates during the deal but never received a final book at pricing. Populate `additionalInfo` with the last-heard book figure (and mirror it in the pricing message body). Distinguishes this from `Final books over` (which requires a final figure from the source at Priced).
  - **`Samurai`** — Samurai bond (JPY-denominated bond issued in Japan by a foreign issuer).
  - **`Kangaroo`** — Kangaroo bond (AUD-denominated bond issued in Australia by a foreign issuer).
  - Multiple tags can coexist (e.g. `"Kangaroo; 3-month par call"`).
  - Common existing values seen in the wild: `"Kangaroo"` (Alphabet AUD Kangaroo), `"FA backed"` (MassMutual funding-agreement-backed), `"EMTN drawdown"`.
- **`priceEvolution[]`** — array of `{price, date}` points showing the deal's move from IPTs → Guidance → Spread Set → Priced. Should include at least the final priced level.
- **`attachmentName`** / **`attachmentId`** / **`attachmentExists`** — optional file attachment.
- **`pricingMessage`** (boolean) — whether the outgoing feed should include a pricing message. Usually `false` unless the desk wants a specific pricing-message send.
- **`grade`** — `"INVESTMENT"` / `"HIGH_YIELD"` / `"EMERGING_MARKETS"`; must match the deal's actual grade.

### Priced-deal cross-checks (must all hold)

- **Count parity**: `len(news.pricedDeals) == len(news.tranches)` for a fully priced deal. If a tranche has `shouldBePriced: true` but no matching priced-deal record exists, flag the missing record.
- **Per-tranche mapping**: pair each priced-deal record with its parent tranche by (currency + nominal + maturityDate). Every tranche should have exactly one priced-deal; every priced-deal should map to exactly one tranche.
- **Coupon-shape consistency**: priced-deal `cpn` must be fixed-shape iff the parent tranche's `structure` is fixed (e.g. `3y Fixed`, `10y CB`), and FRN-shape iff the tranche is an FRN.
- **Message coherence**: the outgoing news `message` body's per-tranche Priced line must be consistent with the priced-deal record — same currency, nominal, coupon, spread, yield, ISIN, maturity.
- **Format + Additional-info + Tier coherence**: the booleans on the priced-deal must match the phrasing in the outgoing body (e.g. body says `Senior Non-Preferred` → `seniorNonPreferred: true` and `seniorPreferred: false`).
- **Bank count coherence**: `len(dealBanks.active) + len(dealBanks.passive)` must equal the JLM count in the outgoing body's bookrunner list for this tranche, AND match the parent tranche's `banks.active/.passive` counts.
- **Price-evolution coherence** — the priced-deal record's `priceEvolution[]` array is the tranche's full pricing history and must line up with (a) the parent tranche's `details[]` while it's still available, and (b) the outgoing news `dealHistory` string / `dealHistoryEntries[]` at every timestamp. Concretely:
  - **Ordering + monotone tightening**: entries are in ascending date order and levels should tighten stage-over-stage (IPTs area → Guidance area → Spread Set). If a later entry is a WIDER spread than an earlier one (e.g. `ASW+65` → `ASW+75`), flag — the desk almost certainly typed a stale earlier level as the final.
  - **Final entry matches `spread`**: the last `priceEvolution[i].price` must equal the priced-deal's own `spread` field. If `priceEvolution[-1]` is `ASW+65` and `spread` is `ASW+70`, one of them is wrong.
  - **Stage coverage**: the number of `priceEvolution` entries should reflect how many stages the deal went through. A deal that ran IPTs → Guidance → Set → Priced should have 3 entries (IPTs / Guidance-or-Set / final level). Fewer entries mean the desk skipped a step in the log.
  - **Cross-check against tranche.details (when accessible)**: for a partially-priced or still-EXPECTED deal, the parent tranche's `details[]` history includes a `priceEvolution` field per edit — every stage level in tranche.details should appear in the priced-deal's `priceEvolution[]` at the matching timestamp. Mismatched levels at the same date → flag. **Note:** once a deal moves to `type: PRICED`, the parent tranche's `details[]` is dropped from the list/news response — only the priced-deal's own `priceEvolution[]` remains. In that state, cross-check against `dealHistoryEntries[]` on the news record instead.
  - **Cross-check against the outgoing deal history**: every stage in the news record's `dealHistoryEntries[]` (IPTs / Guidance / Book Update / Spread Set / Launched / Priced) should have a corresponding level in the priced-deal's `priceEvolution[]`. If `dealHistoryEntries` shows a Guidance stage at `MS-2bp area` but `priceEvolution` skips straight from IPTs to the final spread, flag the missing Guidance entry.

## Reporting

For each Slack term sheet ✅:
1. Detect stage from the Bond Radar `message` (or fall back to the stage in the Slack term sheet if BR's is ambiguous).
2. Walk this checklist for that stage.
3. List ONLY the items genuinely missing. If the term sheet itself marks something TBD / N/A, don't flag it as missing from BR — that just tracks the source.
4. If nothing is missing and other checks pass, emit the clean one-liner.
