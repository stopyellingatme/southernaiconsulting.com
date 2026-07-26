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
| `logo.svg` | The mark on its own — one copper stroke, no ornament |
| `logo-lockup.svg` | Mark + wordmark, for email signatures and letterhead |
| `favicon.svg` | Mark reversed out of a navy rounded square, for browser tabs |
| `og.png` | 1200×630 link-preview card (Facebook, LinkedIn, texts) |
| `brand/` | **Print-ready logo assets for business cards, signage, etc. Start at [`brand/README.md`](brand/README.md).** Wordmark is outlined, so no font dependency |
| `tools/make_og.py` | Regenerates `og.png`. Needs Pillow + macOS Georgia font |
| `tools/make_brand_assets.py` | Regenerates `brand/` SVGs and 300 dpi PNGs |
| `tools/make_brand_pdfs.py` | Regenerates `brand/` vector PDFs (needs Chrome) |
| `CNAME` | Tells GitHub Pages to serve this repo at the custom domain |
| `robots.txt`, `sitemap.xml` | Search-engine basics |
| `404.html` | Branded not-found page |

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
