# BR QA — Compact Rules Reference

## NEVER-FLAG LIST
- Timezone labels (CET/CEST/UKT/BST/EST/EDT/JST/HKT) — never check, never flag in any direction
- ESG short/long form in headline (Grn↔Green, Soc↔Social, Sus↔Sustainable) — interchangeable
- `(equiv. MS+X)` / `SOFR equivalent` in body — optional, never flag presence or absence
- WNG marker missing from headline — optional
- Level embed missing at Book Update or Allocations headline — optional
- `(Excl. JLMs)` qualifier missing from body — optional (but `(Incl. Xm JLM)` with figure IS required)
- Hedge reference bond / hedge ratio in body — source-only, never flag missing
- Tax-changes call / withholding-tax / tax-deductibility — never flag missing; flag as REMOVE if present
- `SNP` in headline on Canadian bail-inable — use `bail-inable` instead; only priced-form `seniorNonPreferred=true`
- `ggb` on priced-form — never propose `ggb=true`; only propose `ggb=false` if currently true
- `nonBullet=Y` — never propose; valid values are NC codes (`16NC6`) or `N`
- `FXD` suffix on structure — BR never uses it
- `144A/RegS` / `SEC` / `RegS` / `TEFRA D` / `NGN` in headline — docs-format markers live in body only
- Scope/DBRS/KBRA/JCR/R&I/ARC ratings missing — BR only carries M/S/F
- Sale-into-Canada / Clearing lines missing — never flag
- Stage-word casing (`Final terms`/`Final Terms`, `Book update`/`book update`) — flexible, never flag
- `SARON MS+` in body/headline on CHF deals — correct, do NOT drop the MS
- Tranche form `timing: "launched"` at Allocations Out — correct carry-forward
- `priceEvolution` at Launched may stay at guidance level — don't flag pe=guidance vs body=launched-spread
- SOFR equiv + timing="DROPPED" on dropped FRN tranche — valid format
- `**` prefix missing on previous-day deals — BR removes at end of pricing day
- Multi-tranche headline missing per-tranche tenors — `dual-tranche` marker sufficient
- SSN / Senior Secured is NOT a headline format flag
- 144A/RegS is NOT a headline format flag — never add to headline
- HoldCo is NOT a headline format flag
- `(the #)` / `(the number)` — body only, NEVER headline
- Issuer name shortening in headlines (dropped SCF/AG/N.V.) — intentional for char limit
- Quotation marks wrapping mandate body — correct (direct bank quote)
- `equivalent`/`equiv.` in body — optional
- No joined levels in multi-tranche headlines
- BR `type` field (EXPECTED/PRICED) — internal workflow state, not deal stage
- Structure field truncation (9-char cap, e.g. `11.5NC10` for `11.5NC10.5`) — by design
- `(no books)` bank drops entirely from body and banks.active/passive
- Tenders/LM/buyback/exchange/consent solicitation — verdict:"skipped", no post
- Co-managers — NOT in banks.active OR banks.passive; only GCs/Sr Co-Leads/passive JLMs in passive
- `JLNB` (Joint Lead Non-Books) — NOT in banks.active OR banks.passive; excluded same as co-managers
- "X to B&D" — role designation among existing JBRs, never changes bank counts
- MC/PC in additionalInfo — only flag if source explicitly states collateral type
- `Books last heard:` colon-form vs `Books last heard over` in additionalInfo — both acceptable
- additionalInfo book figure lagging by one stage — acceptable
- Book Update headline without embedded `at <level>` — acceptable (char limit)
- `Final Terms is …` as body opener — WRONG, never quote as a Fix
- Minor wording: "Original mandate as follows:" vs "Original mandate is as follows: -" — don't flag
- Don't flag punctuation nits on established shorthand (excl JLM, incl JLM, T+X)
- Fxd-to-Frn coupon structure / regulatory boilerplate — never flag missing
- SMR / List / Law when source didn't provide them — never flag
- Missing benchmark ref (UKT/UST/DBR/OAT) — pricing-stage only; added when a spread is set relative to it. Never flag at IPTs/Guidance/Launched (benchmark comes at pricing)
- FRN priceEvolution drops tenor prefix (`E+55a` not `3mE+55a`)
- CITIC Securities + China CITIC Bank Intl = one BR bank ID; don't flag 1-gap
- priceEvolution one-digit truncation when full value exceeds ~14 char field limit — by design
- 1-year par call NOT in additionalInfo — only sub-year atypical windows (2mo/3mo/6mo)
- 0.1% rounding in statsCategories to reach 100.0 — not a defect

## HEADLINE RULES
- Must start with `**` prefix (same-day deals only)
- Elements: `** <Issuer> <CCY><Size> [qualifier] <Tenor/Structure> [format flags] [at <level>]: <Stage>`
- Format flags in headline: Grn, Soc, Sus, EuGB, CB, MC, T2, AT1, Sub, Sukuk, Kangaroo, Samurai, tap, add-on
- NOT headline flags: 144A/RegS, SSN/Senior Secured, HoldCo, `(the #)`
- Stage word must match body opener
- Level matches body + source (single-tranche only; multi-tranche = no level in headline)
- Multi-tranche: `dual-tranche` for 2, `multi-tranche` for 3+; no per-tranche tenors
- Size qualifiers: `(exp.)` for expected, `+` or `(min.)` for minimum, `(max.)` for maximum — placed after size, before tenor
- Launched/Final Terms: two coherent forms — (A) `at <level>: Final Terms` or (B) `at <level>: Launched`; NEVER `… : Launched at <level>`
- `Revised guidance` when level moves between guidance updates (not `Guidance` or `Book update`)
- Stage progression: Mandate → IPTs → Price talk → Guidance → Revised Guidance → Book Update → Spread set → Launched/Final Terms → Allocations → Priced
- `Spread set` is a valid BR stage — spread fixed but deal not yet formally priced; do NOT flag as wrong stage or require priced-deal record
- `Price talk` is a valid BR stage word — used when source says "PRICE TALK" after a prior IPTs stage (narrowed range before final guidance); body opener: `Price talk is X% for <Issuer>'s...`
- `Revised IPTs` is almost never correct — source "PRICE TALK" after IPTs = `Price talk`, not `Revised IPTs`
- `Revised Guidance` only when level explicitly moves AFTER a Guidance stage was already published
- HY NC structure must appear in headline (`5NC2` not just `5y`)
- `dual-tranche` / `multi-tranche` after tenor: `EUR500m 5y dual-tranche`

## BODY RULES
- Opener format: `<Stage phrase> is <level> for <Borrower>'s <size> <structure> <ranking> <Notes/Bonds>, due <maturity>.`
- Priced opener: `Priced: <size>, coupon <X>%, due <date>.`
- Multi-tranche opens `Tranche A:` + `Tranche B:` + `Common terms:` — never `Launched:` opener
- Check `Common terms:` count == 1 on multi-tranche (duplicated = defect)
- Body strips accents/diacritics — flag if accents remain (except at Mandated stage)
- Benchmark date format: spell out month + year (`OBL 2.1% April 2029`, not `04/29`)
- House-style ordering: MWC before par call
- ISIN only in body — never CUSIP
- Spread range from source must be preserved in full (not just one endpoint)
- Per-tranche fields that differ go per-tranche, not in Common Terms
- CHF/SARON body/headline: `SARON MS+X` (with MS); bare `SARON+X` is a defect
- Mandate body Mode A: source gave prose paragraph → quote verbatim in `"..."`
- Mandate body Mode B: source gave term-sheet bullets → paraphrase into `<Issuer> is planning a …`
- Both modes require: mandate verb + banks + role, `may follow, subject to market conditions`, ratings (both issuer + expected issue when different), UOP, logistics coordinator
- Book-line at Allocations: own line with `Book update:` prefix, MUST say `Final books over` (not `Books over`)
- Book-line at Priced: NO new line, NO `Book update:` prefix; appended to end of closing paragraph
  - Case A (final books received, JLM disclosed): `… Final books over EUR1.2bn (incl. EUR250m JLM).`
  - Case A (no JLM disclosed): NO book line in body; `finalBooks` field only
  - Case B (no final book): `… Books last heard over EUR2.5bn.`
- Timing statements: always end of latest live line, never on own line or attached to carried-forward paragraph
- Book Update: previous timing removed from standing paragraph AND appended to Book update line
- `Final books over` vs `Final books above` — interchangeable; don't flag either wording

## TRANCHE FORM RULES
- `currency` — matches source
- `volume` — matches source (`bmk`, `300m`, `1bn`)
- `structure` — matches source (9-char cap); sub-2yr use fractional years (`1.5y` not `18m`)
- `priceEvolution` — matches current level; `a` suffix for area (pre-spread-set); no `a` once firm; ~14 char limit
- `bookOrRating` — HG: `JT-LEADS` if >3 BRs, bank name if ≤3; EM: ratings shorthand (M/S/F)
- `timing` — matches source; Mandate format: `i/c DD Mon>` (calls) or `i/m DD Mon>` (meetings); `>` for series; dash for ranges; launch phrase beats call dates; if source gives no specific date ("in the near future", "subject to market conditions"), vague timing is acceptable — don't flag format
- `banks.active[]` count == source active-JLM count (dedupe first; Co-managers excluded)
- `banks.passive[]` — GCs/Sr Co-Leads/passive JLMs only (NOT Co-managers)
- Parent deal fields: body = `deal.message` (not `deal.body`); banks = `tranche.banks.active` (not `tranche.dealBanks.active`)

## DEAL FLAGS RULES
- `activeWeb` = true, `activeBloomberg` = true, `notifyMobile` = true
- `hgDetails.regionAmericas` = true iff USD tranche + US targeting (HG only; skip for EM)
- `hgDetails.highYield` correct; if true, `hyExpectedPageId` populated (`HYRE##`)
- `hgDetails.coveredBonds` = true iff covered bond
- `emDetails.regionLatam`/`regionCeemea`/`regionAsia`/`feedEmrd` — correct for EM
- `expectedPageId` populated pre-priced; clears on Priced (don't flag null on Priced)
- `expectedPageCount` = min(len(tranches), 5) — pre-priced only
- `hyExpectedPageId` — pre-priced only; clears on Priced (don't flag null on Priced)
- `pricedDeals[]` empty at Allocations Out — NOT a flag (body-update stage only)
- EM deals: skip regionAmericas check and pricedDeals[] empty check (HG-only)

## PRICED-DEAL FORM RULES
- ALWAYS use deal's actual `_category` (em/hg) for priced API calls — never default to hg
- Field names: `moodysRating`/`snpRating`/`fitchRating` (NOT `moodys`/`snp`/`fitch`)
- Moody's stored ALL-CAPS: `BAA3` = `Baa3`; normalise before comparing
- S&P underscore: `BBB_PLUS` = `BBB+`, `A_MINUS` = `A-`
- Cross-over: ANY IG rating → treat as IG
- `isin`, `figi`, `bloombergCode` — all three MUST be populated; null = flag
- `cusip` — NOT on priced form; never flag
- Dual-ISIN: only one stored (usually RegS `XS…`); don't flag other missing
- Format flags: EXACTLY ONE true of `dealRegsOnly`/`deal144aOnly`/`deal144aRegs`/`secRegistered`/`hg3a2`/`hgSecExempt`
- `finalBooks` — MUST match body; null when source gave book size = flag
- `finalBooks` vs `additionalInfo Books last heard` — mutually exclusive
- `leagueTable` — true by default; false only for: maturity <18m (HG) / <365d (EM), size <USD100m equiv, ABS/CDO, domestic-only
- `additionalInfo` required tags: HY → `UOP:` shorthand (GCP/Aqui/Recap/Refi/Capex); EuGB; MC/PC (only if source explicitly states collateral); Sukuk; ESN; Kangaroo; Samurai; sub-year par call
- Boolean correlations: `covered`↔Covered Bond, `green`↔Green, `sustainable`↔Sustainable, `sustainabilityLinked`↔SLB, `social`↔Social, `seniorPreferred`↔SP, `seniorNonPreferred`↔SNP, `coc`↔CoC, `mwc`↔MWC, `cuc`↔CUC, `subordinated`↔Sub, `tier`↔AT1/T2
- opCo/holdCo whitelist ONLY: UK/Swiss/US/JP banks + ING + Nationwide + Softbank; false for all others incl Korean, EM, covered bonds, corporates, SSA
- Taps: add onto original priced record via `Increase nominal`; `nominalSecond` = original + increase; tap ISIN = original bond ISIN
- Bank counts: `dealBanks.active` = source active-JLM count; Co-managers excluded
- Re-fetch priced record immediately before posting flag (live edits by desk)
- statsCategories: GEOGRAPHY + INVESTOR must each sum to 100.0 (0.1 rounding OK)

## Spread Benchmark Table (priced-form `spread` field)
| Ccy | FXD prefix | FRN prefix |
|---|---|---|
| USD | `SMS+` | `SOFR+` |
| GBP | `SMS+` | `SONIA+` |
| CHF | `SARON+` | — |
| JPY | `TMS+` | — |
| EUR | `MS+`/`B+`/`OAT+` | `E+` |
| CAD | `CMS+` | — |
| SGD | `SORA+` | — |
| SEK | `MS+` | `S+` |

Strip source tenor prefixes (`3mS+`, `6mE+`, `3mL+`). Primary spread only (Gilts for GBP, Treasuries for USD); never post-reset margin.

## BOOK-LINE RULES (summary)
- Allocations: `Book update: Final books over <X>.` — own line, prefix required, `Final` required
- Priced Case A (JLM disclosed): appended to closing paragraph: `Final books over <X> (incl. <Y> JLM).`
- Priced Case A (no JLM): NO book line in body; `finalBooks` field only
- Priced Case B: appended: `Books last heard over <X>.`; mirror in `additionalInfo`; `finalBooks` null
- JLM handling: LATEST book update only; if latest didn't disclose JLM, no parenthetical
- `finalBooks` field: millions of tranche ccy (1200 = EUR1.2bn)
- Priced: flag new line or `Book update:` prefix (run regex at Priced stage ONLY, not Allocations)

## GENERAL RULES
- All bookrunners default Active unless source explicitly marks Passive
- Period-separated bank stays Active
- Slack images are readable — NEVER `skipped_image_unreadable`; download and read
- Empty-text messages: check for table blocks / HTML attachments before skipping
- `dealHistoryEntries[]` carries forward fields from prior updates — check before flagging missing
- Benchmark date: spell out month + year
- Clean verdict: no @-mention, short one-liner
- Flagged verdict: tag reactor as first line, `:warning:` header, Fix bullets, keep SHORT
- When correcting wrong clean: remove :double-tick:, add :exclamation:, chat.update the post
- Stale BR record (`changedAt` < Slack ts): wait one tick before flagging
- Canadian bail-inable = SNP (`seniorNonPreferred=true`)
- Source `max` → `(max.)` in headline after size; source `expected` → `(exp.)`; source minimum → `+` or `(min.)`
- Firm (WNG/no qualifier) → no tag
- At Priced/Allocations-after-Priced: size is firm, no qualifiers permitted
