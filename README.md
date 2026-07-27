# southernaiconsulting.com

The public website for **Southern AI Consulting LLC** (Prattville, Alabama).

Static HTML and CSS. No framework, no build step, no dependencies, no
JavaScript, and no external network requests — the page is self-contained, so it
loads instantly and there is nothing to keep updated or patched.

Hosted on **GitHub Pages**. DNS stays at **Namecheap**, which is deliberate: the
nameservers never move, so the Google Workspace email on this domain is never
affected by anything done here.

## Files

| File | What it is |
|---|---|
| `index.html` | The entire site — one page, nine sections, anchor navigation |
| `styles.css` | All styling. Light and dark themes; contrast ratios noted in comments |
| `logo.svg` | The mark on its own — a circuit S, one path, one colour |
| `logo-lockup.svg` | Mark + wordmark, for email signatures and letterhead |
| `favicon.svg` | Mark reversed out of a navy rounded square, for browser tabs |
| `apple-touch-icon.png` | 180×180 home-screen icon. A PNG because iOS will not take an SVG here |
| `og.png` | 1200×630 link-preview card (Facebook, LinkedIn, texts) |
| `brand/` | **Print-ready logo assets for business cards, signage, etc. Start at [`brand/README.md`](brand/README.md).** Wordmark is outlined, so no font dependency |
| `tools/design_mark.py` | **Draws the letterform.** Only needed if the logo itself changes; writes `tools/mark_geometry.py`. Pure standard library |
| `tools/mark_geometry.py` | Generated. The S and its circuit as path data, plus flattened copies for the PNG builders. Everything else reads this |
| `tools/make_site_svgs.py` | Regenerates `logo.svg`, `logo-lockup.svg`, `favicon.svg`, and the inline mark in the HTML pages |
| `tools/make_og.py` | Regenerates `og.png` and `apple-touch-icon.png`. Needs Pillow + macOS Georgia font |
| `tools/wordmark.py` | The two-line Georgia wordmark, and the lockup geometry both lockup builders share |
| `tools/make_brand_assets.py` | Regenerates `brand/` SVGs and 300 dpi PNGs |
| `tools/make_brand_pdfs.py` | Regenerates `brand/` vector PDFs (needs Chrome) |
| `CNAME` | Tells GitHub Pages to serve this repo at the custom domain |
| `robots.txt`, `sitemap.xml` | Search-engine basics |
| `404.html` | Branded not-found page |

## Changing the logo

The letterform lives in one place: six numbers at the top of
`tools/design_mark.py`. The S is a stroked spine, the spine is 270° of one
ellipse followed by its own 180° rotation, and everything else is derived from
that — both counters, both terminals, the whole lower half of the letter, and
the circuit, which is the same spine drawn thin. There is no second set of
numbers that can drift out of step with the first. Edit those, then run the
chain in order:

```sh
python3 tools/design_mark.py        # redraws the S -> tools/mark_geometry.py
python3 tools/make_site_svgs.py     # logo/lockup/favicon + the inline header mark
python3 tools/make_brand_assets.py  # brand/ SVGs and PNGs
python3 tools/make_brand_pdfs.py    # brand/ PDFs
python3 tools/make_og.py            # og.png + apple-touch-icon.png
```

If you screenshot the site to check a change, note that **headless Chrome's
`--window-size` does not set the layout viewport** — media queries evaluate at
its default width no matter what you pass, so a "380px" screenshot silently
tests the desktop breakpoint. Load the page in an `<iframe>` of the width you
want instead; the iframe gets a real viewport. Also pass
`--virtual-time-budget=1500` or the header mark is captured mid-animation.

Nothing anywhere else hard-codes the shape, so the site, the print set and the
link-preview card cannot drift apart. The inline `<svg>` in each HTML page sits
between `<!-- mark:start -->` and `<!-- mark:end -->`; that block is rewritten
by the script, so edit the generator rather than the page.

One thing to know before touching it: **the circuit is a hole, not a second
ink.** The letter and the circuit go into a single `d` under
`fill-rule="evenodd"`, so whatever the mark sits on shows through the channel —
which is why there is no background colour to pass around, why the mark still
prints on one plate, and why it inverts correctly on the dark theme without any
rule for it. It also means the circuit cannot be switched off by hiding an SVG
element, so the header ships the letter twice, with and without, and
`styles.css` picks by device pixels. Below about 32 device pixels of ink the
channel closes up and the letter alone is the intended reduction —
`brand/logo-mark-solid-*.svg`.

## Making a change

```sh
# edit, then look at it locally — just open the file, no server needed
open index.html

git add -A
git commit -m "Describe the change"
git push
```

GitHub Pages redeploys automatically, usually within a minute.

## The intake form

The audit buttons scroll to the form at the foot of the page. GitHub Pages
cannot process a form submission, so it posts to **FormSubmit.co**, which emails
the submission to `admin@southernaiconsulting.com`.

**The form is activated and delivering.** A test submission returned a clean
`302` to `thanks.html` with no confirmation interstitial, which is what proves
activation took. Nothing further is required to receive leads.

**One optional cleanup is still open.** FormSubmit issues a hashed endpoint like
`https://formsubmit.co/abc123...`. Search `index.html` for `FORM_ACTION` and swap
it into the form's `action=`, so the raw email address is no longer sitting in
the page source for scrapers to harvest. Commit and push. The form works either
way; this only reduces spam to that address.

**`_next` must stay an absolute URL on the live domain** or FormSubmit rejects
the submission. It is `https://southernaiconsulting.com/thanks.html`. It was
`http://` while the certificate was pending, because an `https://` target fails
outright before the cert exists — worth remembering if the domain ever moves and
the certificate has to be reissued.

**If spam starts arriving**, change the `_captcha` hidden field from `false` to
`true` to add FormSubmit's challenge page. It costs you some conversions, so only
do it if you actually need to. There is already a hidden honeypot field
(`_honey`) catching the low-effort bots.

**The fields** map to the qualification gate: name, business, email, optional
phone, the two-sentence problem (required — this is the filter), current tools,
and how they heard about you. `thanks.html` is the post-submit page.

## Things you will probably want to change

**Retire the founding-client discount** once client #3 signs. Delete the
`<p class="founding">` block in `index.html`.

**Put a number on Custom Software & Websites.** It currently reads *"quoted per
project"* — the one package with no published floor. Four priced cards next to
one that won't say tends to read as "the expensive one", so this is worth
deciding. Search `index.html` for `PRICE_TBD`; change the card and add a
matching `priceSpecification` to that offer in `hasOfferCatalog`.

**Change a price.** Search for `from $1,200` / `from $1,500` / `from $800`.
Prices also appear in the structured-data block at the bottom of `index.html`
(`hasOfferCatalog`) — update both so search engines don't show a stale number.

**Add a testimonial or case study.** These are the highest-value additions once
the first founding clients are delivered.

## DNS (for reference — already done)

At Namecheap → Domain List → Manage → **Advanced DNS**:

| Type | Host | Value |
|---|---|---|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| CNAME | `www` | `stopyellingatme.github.io.` |

**Do not touch the `MX` record (`smtp.google.com`) or the
`google-site-verification` TXT record.** Those are the live business email. If
the site ever needs to be rolled back to a parking page, restore a single `A`
record for `@` pointing at `192.64.119.150`.
