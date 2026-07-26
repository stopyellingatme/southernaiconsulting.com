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
| `logo.svg` | The mark on its own, for light backgrounds |
| `logo-lockup.svg` | Mark + wordmark, for email signatures and letterhead |
| `favicon.svg` | Mark on a navy rounded square, for browser tabs |
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

## The intake form — READ THIS FIRST

The audit buttons scroll to the form at the foot of the page. GitHub Pages
cannot process a form submission, so it posts to **FormSubmit.co**, which emails
the submission to `admin@southernaiconsulting.com`.

**One-time activation — until you do this, submissions are NOT delivered:**

1. Open the live site and submit the form once with real details.
2. FormSubmit emails `admin@southernaiconsulting.com` a confirmation link.
3. Click it. Done — every later submission arrives as an email.

Do this **after** HTTPS is working on the domain, because the form redirects to
`https://southernaiconsulting.com/thanks.html` on success.

**Then hide your address from scrapers.** After activating, FormSubmit gives you
a hashed endpoint like `https://formsubmit.co/abc123...`. Search `index.html` for
`FORM_ACTION` and swap it into the form's `action=`, so the raw email address is
no longer sitting in the page source. Commit and push.

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
